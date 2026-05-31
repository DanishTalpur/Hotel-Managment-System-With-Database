from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Booking, BookingRoom, Customer, Room, Rate, RoomType, Invoice
from database import db
from datetime import datetime, date

reservations_router = Blueprint('reservations', __name__)

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
                rate_name = br.rate_type.rate_name if br.rate_type else 'Standard'
            num_guests = br.num_guests
        
        # Check if repeat guest
        is_repeat = Booking.query.filter_by(customer_id=booking.customer_id).count() > 1
        
        bookings_data.append({
            'booking': booking,
            'customer': customer,
            'room_number': room_number,
            'rate_name': rate_name,
            'num_guests': num_guests,
            'is_repeat': is_repeat
        })
    
    return render_template(
        'index.html',
        active='reservations',
        bookings=bookings_data,
        stats=stats,
        customers=customers,
        room_types=room_types,
        rates=rates,
        search=search,
        status_filter=status_filter,
        source_filter=source_filter
    )

@reservations_router.route('/reservations/add', methods=['POST'])
def add_reservation():
    customer_id = int(request.form['customer_id'])
    room_type_id = int(request.form['room_type_id'])
    rate_id = int(request.form['rate_id'])
    num_guests = int(request.form['num_guests'])
    booking_source = request.form['booking_source']
    status = request.form.get('status', 'booked')
    
    planned_checkin = datetime.strptime(request.form['planned_checkin'], '%Y-%m-%d').date()
    planned_checkout = datetime.strptime(request.form['planned_checkout'], '%Y-%m-%d').date()
    
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
    
    # Find an available room of the requested type
    available_room = Room.query.filter_by(
        room_type_id=room_type_id,
        status='available'
    ).first()
    
    if available_room:
        # Create booking room
        booking_room = BookingRoom(
            booking_id=booking.booking_id,
            room_id=available_room.room_id,
            rate_id=rate_id,
            num_guests=num_guests
        )
        db.session.add(booking_room)
        
        # Update room status
        if status == 'checked_in':
            available_room.status = 'occupied'
        elif status == 'booked':
            available_room.status = 'occupied'  # Reserve the room
    
    db.session.commit()
    
    flash('Reservation created successfully!', 'success')
    return redirect(url_for('reservations.reservations_screen'))

@reservations_router.route('/reservations/delete/<int:id>', methods=['POST'])
def delete_reservation(id):
    booking = Booking.query.get_or_404(id)
    
    # Free up any rooms associated with this booking
    for br in booking.booking_rooms:
        room = Room.query.get(br.room_id)
        if room and room.status in ['occupied', 'checkout']:
            room.status = 'available'
        
        # Delete booking room
        db.session.delete(br)
    
    # Delete associated invoice
    invoice = Invoice.query.filter_by(booking_id=id).first()
    if invoice:
        db.session.delete(invoice)
    
    db.session.delete(booking)
    db.session.commit()
    
    flash('Reservation deleted successfully!', 'success')
    return redirect(url_for('reservations.reservations_screen'))

@reservations_router.route('/reservations/checkin/<int:id>', methods=['POST'])
def checkin_reservation(id):
    booking = Booking.query.get_or_404(id)
    booking.status = 'checked_in'
    booking.actual_checkin = date.today()
    
    # Update room status
    for br in booking.booking_rooms:
        room = Room.query.get(br.room_id)
        if room:
            room.status = 'occupied'
    
    db.session.commit()
    flash('Guest checked in successfully!', 'success')
    return redirect(url_for('reservations.reservations_screen'))

@reservations_router.route('/reservations/checkout/<int:id>', methods=['POST'])
def checkout_reservation(id):
    booking = Booking.query.get_or_404(id)
    booking.status = 'checkout'
    booking.actual_checkout = date.today()
    
    # Update room status
    for br in booking.booking_rooms:
        room = Room.query.get(br.room_id)
        if room:
            room.status = 'checkout'
    
    db.session.commit()
    flash('Guest checked out successfully!', 'success')
    return redirect(url_for('reservations.reservations_screen'))