from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Booking, BookingRoom, Customer, Room, Rate, RoomType, Invoice, Stay, StayService, BookingRoomExtra, Extra
from database import db
from datetime import datetime, date, timedelta

reservations_router = Blueprint('reservations', __name__)


def _room_has_date_conflict(room_id, checkin, checkout, exclude_booking_id=None):
    """Return True if the room already has an overlapping booked/checked-in reservation."""
    query = BookingRoom.query.join(Booking).filter(
        BookingRoom.room_id == room_id,
        Booking.status.in_(['booked', 'checked_in']),
        Booking.planned_checkin < checkout,
        Booking.planned_checkout > checkin,
    )
    if exclude_booking_id:
        query = query.filter(Booking.booking_id != exclude_booking_id)
    return query.first() is not None

@reservations_router.route('/reservations')
def reservations_screen():
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    source_filter = request.args.get('source', '')
    
    # Base query
    query = Booking.query.join(Customer).join(BookingRoom).join(Room)
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                Customer.first_name.ilike(f'%{search}%'),
                Customer.last_name.ilike(f'%{search}%'),
                Booking.booking_id == int(search) if search.isdigit() else False
            )
        )
    
    if status_filter:
        query = query.filter(Booking.status == status_filter)
    
    if source_filter:
        query = query.filter(Booking.booking_source == source_filter)
    
    bookings = query.order_by(Booking.planned_checkin.desc()).all()
    
    # Get statistics
    this_month = datetime.now().month
    this_year = datetime.now().year
    
    total_bookings = Booking.query.filter(
        db.extract('month', Booking.created_at) == this_month,
        db.extract('year', Booking.created_at) == this_year
    ).count()
    
    pending_bookings = Booking.query.filter_by(status='pending').count()
    
    walkins_today = Booking.query.filter(
        Booking.booking_source == 'Walk-in',
        db.func.date(Booking.created_at) == date.today()
    ).count()
    
    cancellations = Booking.query.filter(
        Booking.status == 'cancelled',
        db.extract('month', Booking.created_at) == this_month,
        db.extract('year', Booking.created_at) == this_year
    ).count()
    
    stats = {
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'walkins_today': walkins_today,
        'cancellations': cancellations
    }
    
    # Get customers for new booking form
    customers = Customer.query.all()
    
    # Get room types
    room_types = RoomType.query.all()
    
    # Get rates
    rates = Rate.query.filter(
        Rate.start_date <= date.today(),
        Rate.end_date >= date.today()
    ).all()
    
    # Get available rooms
    available_rooms = Room.query.filter_by(status='available').all()
    
    # Get all extras
    extras = Extra.query.all()
    
    # Format bookings for template
    bookings_data = []
    for booking in bookings:
        customer = Customer.query.get(booking.customer_id)
        room_number = 'N/A'
        rate_name = 'Standard'
        num_guests = 1
        
        if booking.booking_rooms:
            br = booking.booking_rooms[0]
            room_number = br.room.room_number if br.room else 'N/A'
            if br.rate:
                rate_name = br.rate.rate_type.rate_name if br.rate.rate_type else 'Standard'
            num_guests = br.num_guests
        
        # Check if repeat guest
        is_repeat = Booking.query.filter_by(customer_id=booking.customer_id).count() > 1
        
        invoice = Invoice.query.filter_by(booking_id=booking.booking_id).first()
        
        bookings_data.append({
            'booking': booking,
            'customer': customer,
            'room_number': room_number,
            'rate_name': rate_name,
            'num_guests': num_guests,
            'is_repeat': is_repeat,
            'invoice_id': invoice.invoice_id if invoice else None
        })
    
    return render_template(
        'reservations.html',
        active='reservations',
        current_date=datetime.now().strftime('%A, %d %B %Y'),
        bookings=bookings_data,
        stats=stats,
        customers=customers,
        room_types=room_types,
        rates=rates,
        available_rooms=available_rooms,
        extras=extras,
        search=search,
        status_filter=status_filter,
        source_filter=source_filter
    )

@reservations_router.route('/reservations/add', methods=['POST'])
def add_reservation():
    customer_id = int(request.form['customer_id'])
    room_id = int(request.form['room_id'])
    rate_id = int(request.form['rate_id'])
    num_guests = int(request.form['num_guests'])
    booking_source = request.form['booking_source']
    status = request.form.get('status', 'booked')
    
    planned_checkin = datetime.strptime(request.form['planned_checkin'], '%Y-%m-%d').date()
    planned_checkout = datetime.strptime(request.form['planned_checkout'], '%Y-%m-%d').date()
    
    # 1. Date validation
    if planned_checkout <= planned_checkin:
        flash('Check-out date must be after check-in date.', 'error')
        return redirect(url_for('reservations.reservations_screen'))
        
    # 2. Room availability check
    room = Room.query.get(room_id)
    if not room:
        flash('The selected room was not found.', 'error')
        return redirect(url_for('reservations.reservations_screen'))
    if room.status in ('maintenance', 'blocked'):
        flash('The selected room is not available for booking.', 'error')
        return redirect(url_for('reservations.reservations_screen'))
    if _room_has_date_conflict(room_id, planned_checkin, planned_checkout):
        flash('The selected room is already reserved for overlapping dates.', 'error')
        return redirect(url_for('reservations.reservations_screen'))
    if status == 'checked_in' and room.status != 'available':
        flash('The selected room is not available for immediate check-in.', 'error')
        return redirect(url_for('reservations.reservations_screen'))
        
    # Create booking
    booking = Booking(
        customer_id=customer_id,
        planned_checkin=planned_checkin,
        planned_checkout=planned_checkout,
        status=status,
        booking_source=booking_source,
        created_at=datetime.now()
    )
    db.session.add(booking)
    db.session.flush()
    
    # Create booking room
    booking_room = BookingRoom(
        booking_id=booking.booking_id,
        room_id=room.room_id,
        rate_id=rate_id,
        num_guests=num_guests
    )
    db.session.add(booking_room)
    db.session.flush()
    
    # Add selected extras
    selected_extras = request.form.getlist('extras')
    for extra_id in selected_extras:
        booking_room_extra = BookingRoomExtra(
            booking_room_id=booking_room.booking_room_id,
            extra_id=int(extra_id),
            quantity=1,
            source='booking'
        )
        db.session.add(booking_room_extra)
        
    # Update room status only on immediate check-in
    if status == 'checked_in':
        room.status = 'occupied'
        booking.actual_checkin = date.today()
    
    db.session.commit()
    
    flash('Reservation created successfully!', 'success')
    return redirect(url_for('reservations.reservations_screen'))

@reservations_router.route('/reservations/delete/<int:id>', methods=['POST'])
def delete_reservation(id):
    booking = Booking.query.get_or_404(id)

    # Delete associated invoice (cascades to snapshots and payments)
    invoice = Invoice.query.filter_by(booking_id=id).first()
    if invoice:
        db.session.delete(invoice)

    # Free up rooms and remove related records
    for br in booking.booking_rooms:
        for stay in list(br.stays):
            for ss in list(stay.stay_services):
                db.session.delete(ss)
            db.session.delete(stay)

        for bre in BookingRoomExtra.query.filter_by(booking_room_id=br.booking_room_id).all():
            db.session.delete(bre)

        room = Room.query.get(br.room_id)
        if room and room.status in ['occupied', 'checkout']:
            room.status = 'available'

        db.session.delete(br)

    db.session.delete(booking)
    db.session.commit()

    flash('Reservation deleted successfully!', 'success')
    return redirect(url_for('reservations.reservations_screen'))

@reservations_router.route('/reservations/checkin/<int:id>', methods=['POST'])
def checkin_reservation(id):
    booking = Booking.query.get_or_404(id)

    if not booking.booking_rooms:
        flash('No room associated with this booking.', 'error')
        return redirect(url_for('reservations.reservations_screen'))

    br = booking.booking_rooms[0]
    room = Room.query.get(br.room_id)
    if not room:
        flash('Assigned room was not found.', 'error')
        return redirect(url_for('reservations.reservations_screen'))
    if room.status != 'available':
        flash('Assigned room is not available for check-in.', 'error')
        return redirect(url_for('reservations.reservations_screen'))
    if _room_has_date_conflict(br.room_id, booking.planned_checkin, booking.planned_checkout, exclude_booking_id=id):
        flash('Another reservation conflicts with this room for the selected dates.', 'error')
        return redirect(url_for('reservations.reservations_screen'))

    booking.status = 'checked_in'
    booking.actual_checkin = date.today()
    room.status = 'occupied'

    db.session.commit()
    flash('Guest checked in successfully!', 'success')
    return redirect(url_for('reservations.reservations_screen'))

@reservations_router.route('/reservations/checkout/<int:id>', methods=['GET'])
def checkout_screen(id):
    booking = Booking.query.get_or_404(id)
    if booking.status != 'checked_in':
        flash('Booking is not checked in.', 'error')
        return redirect(url_for('reservations.reservations_screen'))
        
    customer = Customer.query.get(booking.customer_id)
    booking_room = booking.booking_rooms[0] if booking.booking_rooms else None
    if not booking_room:
        flash('No room associated with this booking.', 'error')
        return redirect(url_for('reservations.reservations_screen'))
        
    room = Room.query.get(booking_room.room_id)
    rate = Rate.query.get(booking_room.rate_id)
    
    # Calculate stay duration
    checkin_date = booking.actual_checkin or booking.planned_checkin or date.today()
    checkout_date = date.today()
    
    if isinstance(checkin_date, datetime):
        checkin_date = checkin_date.date()
    if isinstance(checkout_date, datetime):
        checkout_date = checkout_date.date()
        
    nights = (checkout_date - checkin_date).days
    if nights <= 0:
        nights = 1  # Minimum 1 night charge
        
    # Calculate room total
    room_charge = rate.amount if rate else 5000
    room_total = room_charge * nights
    
    # Calculate extras pre-booked
    extra_charges = []
    extra_total = 0
    bre_items = BookingRoomExtra.query.filter_by(booking_room_id=booking_room.booking_room_id, source='booking').all()
    for bre in bre_items:
        extra = Extra.query.get(bre.extra_id)
        if extra:
            extra_charges.append({
                'name': extra.extra_name,
                'quantity': bre.quantity,
                'price': extra.price,
                'total_price': extra.price * bre.quantity
            })
            extra_total += extra.price * bre.quantity
            
    # Get all service items grouped by category for selection
    from models import ServiceCategory, ServiceItem
    categories = ServiceCategory.query.all()
    service_catalog = []
    for cat in categories:
        items = ServiceItem.query.filter_by(category_id=cat.category_id).all()
        if items:
            service_catalog.append({
                'name': cat.category_name,
                'service_items': items
            })
            
    return render_template(
        'checkout.html',
        active='reservations',
        current_date=date.today().strftime('%A, %d %B %Y'),
        booking=booking,
        customer=customer,
        booking_room=booking_room,
        room=room,
        rate=rate,
        checkin_date=checkin_date,
        checkout_date=checkout_date,
        nights=nights,
        room_total=room_total,
        extra_charges=extra_charges,
        extra_total=extra_total,
        service_catalog=service_catalog
    )


@reservations_router.route('/reservations/checkout/<int:id>', methods=['POST'])
def checkout_reservation(id):
    booking = Booking.query.get_or_404(id)
    if booking.status != 'checked_in':
        flash('Booking is not checked in.', 'error')
        return redirect(url_for('reservations.reservations_screen'))
        
    booking.status = 'checkout'
    booking.actual_checkout = date.today()
    
    # Update room status
    for br in booking.booking_rooms:
        room = Room.query.get(br.room_id)
        if room:
            room.status = 'checkout'
            
    # Calculate stay duration
    checkin_date = booking.actual_checkin or booking.planned_checkin or date.today()
    checkout_date = booking.actual_checkout or date.today()
    
    if isinstance(checkin_date, datetime):
        checkin_date = checkin_date.date()
    if isinstance(checkout_date, datetime):
        checkout_date = checkout_date.date()
        
    nights = (checkout_date - checkin_date).days
    if nights <= 0:
        nights = 1  # Minimum 1 night charge
        
    # Generate Stay records for each booking room if they do not exist
    for br in booking.booking_rooms:
        existing_stays = Stay.query.filter_by(booking_room_id=br.booking_room_id).count()
        if existing_stays == 0:
            rate = Rate.query.get(br.rate_id)
            room_charge = rate.amount if rate else 5000
            
            current_date = checkin_date
            for _ in range(nights):
                stay = Stay(
                    booking_room_id=br.booking_room_id,
                    stay_date=current_date,
                    applied_rate=room_charge,
                    room_charge=room_charge
                )
                db.session.add(stay)
                current_date += timedelta(days=1)
                
    db.session.flush()
    
    # Get the stays created
    first_stay = None
    for br in booking.booking_rooms:
        first_stay = Stay.query.filter_by(booking_room_id=br.booking_room_id).first()
        if first_stay:
            break
            
    # Record service items used at checkout
    selected_service_ids = request.form.getlist('services')
    service_total = 0
    logged_services = []
    
    for svc_id_str in selected_service_ids:
        svc_id = int(svc_id_str)
        qty = int(request.form.get(f'qty_{svc_id}', 1))
        
        from models import ServiceItem, StayService
        svc_item = ServiceItem.query.get(svc_id)
        if svc_item and first_stay:
            line_total = svc_item.unit_price * qty
            service_total += line_total
            
            stay_svc = StayService(
                stay_id=first_stay.stay_id,
                service_item_id=svc_id,
                quantity=qty,
                unit_price=svc_item.unit_price,
                total_price=line_total,
                recorded_at=datetime.now()
            )
            db.session.add(stay_svc)
            logged_services.append((svc_item, qty, line_total))
            
    db.session.flush()
    
    # Check if invoice already exists
    invoice = Invoice.query.filter_by(booking_id=id).first()
    if not invoice:
        # Calculate subtotal (Room stays + Services + Extras)
        room_total = 0
        for br in booking.booking_rooms:
            for stay in br.stays:
                room_total += stay.room_charge
                
        # Calculate extras total
        extra_total = 0
        bre_items = []
        for br in booking.booking_rooms:
            extras_for_room = BookingRoomExtra.query.filter_by(booking_room_id=br.booking_room_id, source='booking').all()
            bre_items.extend(extras_for_room)
            for bre in extras_for_room:
                extra = Extra.query.get(bre.extra_id)
                if extra:
                    extra_total += extra.price * bre.quantity
                    
        subtotal = room_total + service_total + extra_total
        tax_amount = subtotal * 0.16  # 16% GST
        total_amount = subtotal + tax_amount
        
        invoice = Invoice(
            booking_id=id,
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
        
        # Save invoice extras (Snapshot)
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
                
        # Save invoice services (Snapshot)
        from models import InvoiceService
        for svc_item, qty, line_total in logged_services:
            invoice_svc = InvoiceService(
                invoice_id=invoice.invoice_id,
                service_item_id=svc_item.service_item_id,
                item_name=svc_item.item_name,
                quantity=qty,
                unit_price=svc_item.unit_price,
                line_total=line_total
            )
            db.session.add(invoice_svc)
        
    db.session.commit()
    flash('Guest checked out successfully! Invoice generated.', 'success')
    return redirect(url_for('invoices.invoice_detail', id=invoice.invoice_id))
