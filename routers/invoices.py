from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Invoice, Booking, BookingRoom, Stay, Customer, Room
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
    invoice.payment_status = 'paid'
    invoice.paid_amount = invoice.total_amount
    db.session.commit()
    
    flash('Invoice marked as paid!', 'success')
    return redirect(url_for('invoices.invoices_screen'))

@invoices_router.route('/invoices/<int:id>')
def invoice_detail(id):
    invoice = Invoice.query.get_or_404(id)
    booking = Booking.query.get(invoice.booking_id)
    customer = Customer.query.get(booking.customer_id) if booking else None
    
    # Get stay details
    stay_charges = []
    if booking:
        for br in booking.booking_rooms:
            for stay in br.stays:
                room = Room.query.get(br.room_id)
                stay_charges.append({
                    'date': stay.stay_date,
                    'room_number': room.room_number if room else 'N/A',
                    'charge': stay.room_charge
                })
    
    return render_template(
        'invoices.html',
        active='invoices',
        current_date=date.today().strftime('%A, %d %B %Y'),
        invoice=invoice,
        booking=booking,
        customer=customer,
        stay_charges=stay_charges,
        view_detail=True
    )

@invoices_router.route('/invoices/generate/<int:booking_id>', methods=['POST'])
def generate_invoice(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if invoice already exists
    existing_invoice = Invoice.query.filter_by(booking_id=booking_id).first()
    if existing_invoice:
        flash('Invoice already exists for this booking!', 'error')
        return redirect(url_for('invoices.invoices_screen'))
    
    # Calculate total from stays
    total = 0
    for br in booking.booking_rooms:
        for stay in br.stays:
            total += stay.room_charge
    
    if total == 0:
        flash('No charges found for this booking!', 'error')
        return redirect(url_for('invoices.invoices_screen'))
    
    # Create invoice
    invoice = Invoice(
        booking_id=booking_id,
        issued_date=date.today(),
        subtotal=total,
        tax_amount=total * 0.16,  # 16% tax
        total_amount=total * 1.16,
        paid_amount=0,
        payment_status='unpaid'
    )
    db.session.add(invoice)
    db.session.commit()
    
    flash('Invoice generated successfully!', 'success')
    return redirect(url_for('invoices.invoice_detail', id=invoice.invoice_id))

@invoices_router.route('/invoices/partial_payment/<int:id>', methods=['POST'])
def partial_payment(id):
    invoice = Invoice.query.get_or_404(id)
    amount = float(request.form['payment_amount'])
    
    invoice.paid_amount += amount
    if invoice.paid_amount >= invoice.total_amount:
        invoice.payment_status = 'paid'
        invoice.paid_amount = invoice.total_amount
    
    db.session.commit()
    flash('Payment recorded successfully!', 'success')
    return redirect(url_for('invoices.invoice_detail', id=id))