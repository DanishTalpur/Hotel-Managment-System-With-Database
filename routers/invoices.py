from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Invoice, Booking, BookingRoom, Stay, Customer, Room, BookingRoomExtra, Extra, Payment
from database import db
from datetime import datetime, date

invoices_router = Blueprint('invoices', __name__)

@invoices_router.route('/invoices')
def invoices_screen():
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    # Base query
    query = Invoice.query.join(Booking).join(Customer)
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                Customer.first_name.ilike(f'%{search}%'),
                Customer.last_name.ilike(f'%{search}%'),
                Invoice.invoice_id == int(search) if search.isdigit() else False
            )
        )
    
    if status_filter:
        query = query.filter(Invoice.payment_status == status_filter)
    
    invoices = query.order_by(Invoice.issued_date.desc()).all()
    
    # Calculate statistics
    total_revenue = db.session.query(db.func.sum(Invoice.paid_amount)).filter_by(payment_status='paid').scalar() or 0
    pending_revenue = db.session.query(db.func.sum(Invoice.total_amount - Invoice.paid_amount)).filter_by(payment_status='unpaid').scalar() or 0
    total_invoices = Invoice.query.count()
    paid_invoices = Invoice.query.filter_by(payment_status='paid').count()
    unpaid_invoices = Invoice.query.filter_by(payment_status='unpaid').count()
    
    stats = {
        'total_revenue': total_revenue,
        'pending_revenue': pending_revenue,
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'unpaid_invoices': unpaid_invoices
    }
    
    # Format invoices for template
    invoices_data = []
    for invoice in invoices:
        booking = Booking.query.get(invoice.booking_id)
        customer = Customer.query.get(booking.customer_id) if booking else None
        
        invoices_data.append({
            'invoice': invoice,
            'customer': customer,
            'booking': booking
        })
    
    return render_template(
        'invoices.html',
        active='invoices',
        current_date=date.today().strftime('%A, %d %B %Y'),
        invoices=invoices_data,
        stats=stats,
        search=search,
        status_filter=status_filter
    )

@invoices_router.route('/invoices/mark_paid/<int:id>')
def mark_paid(id):
    invoice = Invoice.query.get_or_404(id)
    remaining = invoice.total_amount - invoice.paid_amount
    if remaining > 0:
        payment = Payment(
            invoice_id=invoice.invoice_id,
            payment_date=datetime.now(),
            amount=remaining,
            payment_method='Cash',
            reference_number=None,
            notes='Full payment recorded from invoice screen'
        )
        db.session.add(payment)
    invoice.payment_status = 'paid'
    invoice.paid_amount = invoice.total_amount
    db.session.commit()

    flash('Invoice marked as paid!', 'success')
    return redirect(url_for('invoices.invoice_detail', id=id))

@invoices_router.route('/invoices/<int:id>')
def invoice_detail(id):
    invoice = Invoice.query.get_or_404(id)
    booking = Booking.query.get(invoice.booking_id)
    customer = Customer.query.get(booking.customer_id) if booking else None
    
    # Get stay details
    stay_charges = []
    service_charges = []
    extra_charges = []
    
    if booking:
        for br in booking.booking_rooms:
            # 1. Stay charges
            for stay in br.stays:
                room = Room.query.get(br.room_id)
                stay_charges.append({
                    'date': stay.stay_date,
                    'room_number': room.room_number if room else 'N/A',
                    'charge': stay.room_charge
                })
                
    # 2. Add-on services from InvoiceService snapshot table
    from models import InvoiceService
    inv_services = InvoiceService.query.filter_by(invoice_id=id).all()
    if inv_services:
        for ss in inv_services:
            service_charges.append({
                'name': ss.item_name,
                'quantity': ss.quantity,
                'unit_price': ss.unit_price,
                'total_price': ss.line_total
            })
    else:
        # Fallback to live query for backward compatibility (pre-seeded invoices)
        if booking:
            for br in booking.booking_rooms:
                for stay in br.stays:
                    for ss in stay.stay_services:
                        service_charges.append({
                            'name': ss.service_item.item_name if ss.service_item else 'Unknown Service',
                            'quantity': ss.quantity,
                            'unit_price': ss.unit_price,
                            'total_price': ss.total_price
                        })

    # 3. Extras from InvoiceExtra snapshot table
    from models import InvoiceExtra
    inv_extras = InvoiceExtra.query.filter_by(invoice_id=id).all()
    if inv_extras:
        for ie in inv_extras:
            extra_charges.append({
                'name': ie.extra_name,
                'quantity': ie.quantity,
                'price': ie.unit_price,
                'total_price': ie.line_total
            })
    else:
        # Fallback to live query for backward compatibility (pre-seeded invoices)
        if booking:
            for br in booking.booking_rooms:
                bre_items = BookingRoomExtra.query.filter_by(booking_room_id=br.booking_room_id).all()
                for bre in bre_items:
                    extra = Extra.query.get(bre.extra_id)
                    if extra:
                        extra_charges.append({
                            'name': extra.extra_name,
                            'quantity': bre.quantity,
                            'price': extra.price,
                            'total_price': extra.price * bre.quantity
                        })
    
    payments = Payment.query.filter_by(invoice_id=id).order_by(Payment.payment_date.desc()).all()

    return render_template(
        'invoices.html',
        active='invoices',
        current_date=date.today().strftime('%A, %d %B %Y'),
        invoice=invoice,
        booking=booking,
        customer=customer,
        stay_charges=stay_charges,
        service_charges=service_charges,
        extra_charges=extra_charges,
        payments=payments,
        view_detail=True
    )

@invoices_router.route('/invoices/generate/<int:booking_id>', methods=['POST'])
def generate_invoice(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if invoice already exists
    existing_invoice = Invoice.query.filter_by(booking_id=booking_id).first()
    if existing_invoice:
        flash('Invoice already exists for this booking!', 'error')
        return redirect(url_for('invoices.invoice_detail', id=existing_invoice.invoice_id))
    
    # Calculate room stays total
    room_total = 0
    for br in booking.booking_rooms:
        for stay in br.stays:
            room_total += stay.room_charge
            
    # Calculate service charges total
    service_total = 0
    logged_services = []
    for br in booking.booking_rooms:
        for stay in br.stays:
            for ss in stay.stay_services:
                service_total += ss.total_price
                logged_services.append(ss)
                
    # Calculate extras total
    extra_total = 0
    bre_items = []
    for br in booking.booking_rooms:
        extras_for_room = BookingRoomExtra.query.filter_by(booking_room_id=br.booking_room_id).all()
        bre_items.extend(extras_for_room)
        for bre in extras_for_room:
            extra = Extra.query.get(bre.extra_id)
            if extra:
                extra_total += extra.price * bre.quantity
                
    subtotal = room_total + service_total + extra_total
    
    if subtotal == 0:
        flash('No charges found for this booking!', 'error')
        return redirect(url_for('invoices.invoices_screen'))
    
    # Create invoice
    tax_amount = subtotal * 0.16
    total_amount = subtotal + tax_amount
    invoice = Invoice(
        booking_id=booking_id,
        issued_date=date.today(),
        room_total=room_total,
        service_total=service_total,
        extra_total=extra_total,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        paid_amount=0,
        payment_status='unpaid'
    )
    db.session.add(invoice)
    db.session.flush()
    
    # Create InvoiceExtra (Snapshot)
    from models import InvoiceExtra
    for bre in bre_items:
        extra = Extra.query.get(bre.extra_id)
        if extra:
            invoice_extra = InvoiceExtra(
                invoice_id=invoice.invoice_id,
                extra_id=bre.extra_id,
                extra_name=extra.extra_name,
                quantity=bre.quantity,
                unit_price=extra.price,
                line_total=extra.price * bre.quantity
            )
            db.session.add(invoice_extra)
            
    # Create InvoiceService (Snapshot)
    from models import InvoiceService
    for ss in logged_services:
        invoice_svc = InvoiceService(
            invoice_id=invoice.invoice_id,
            service_item_id=ss.service_item_id,
            item_name=ss.service_item.item_name if ss.service_item else 'Unknown Service',
            quantity=ss.quantity,
            unit_price=ss.unit_price,
            line_total=ss.total_price
        )
        db.session.add(invoice_svc)
        
    db.session.commit()
    
    flash('Invoice generated successfully!', 'success')
    return redirect(url_for('invoices.invoice_detail', id=invoice.invoice_id))

@invoices_router.route('/invoices/partial_payment/<int:id>', methods=['POST'])
def partial_payment(id):
    invoice = Invoice.query.get_or_404(id)
    amount = float(request.form['payment_amount'])
    payment_method = request.form.get('payment_method', 'Cash').strip() or 'Cash'
    reference_number = request.form.get('reference_number', '').strip() or None

    if amount <= 0:
        flash('Payment amount must be greater than zero.', 'error')
        return redirect(url_for('invoices.invoice_detail', id=id))

    balance_due = invoice.total_amount - invoice.paid_amount
    if amount > balance_due:
        amount = balance_due

    payment = Payment(
        invoice_id=invoice.invoice_id,
        payment_date=datetime.now(),
        amount=amount,
        payment_method=payment_method,
        reference_number=reference_number,
        notes='Partial payment recorded from invoice screen'
    )
    db.session.add(payment)

    invoice.paid_amount += amount
    if invoice.paid_amount >= invoice.total_amount:
        invoice.payment_status = 'paid'
        invoice.paid_amount = invoice.total_amount

    db.session.commit()
    flash('Payment recorded successfully!', 'success')
    return redirect(url_for('invoices.invoice_detail', id=id))