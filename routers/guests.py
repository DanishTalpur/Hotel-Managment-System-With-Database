from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Customer, Booking
from database import db
from datetime import date

guests_router = Blueprint('guests', __name__)

@guests_router.route('/guests')
def guests_screen():
    search = request.args.get('search', '')
    
    if search:
        all_guests = Customer.query.filter(
            (Customer.first_name.ilike(f'%{search}%')) |
            (Customer.last_name.ilike(f'%{search}%')) |
            (Customer.email.ilike(f'%{search}%')) |
            (Customer.phone.ilike(f'%{search}%'))
        ).all()
    else:
        all_guests = Customer.query.all()
    
    # Count repeat guests (guests with more than one booking)
    repeat_guest_ids = db.session.query(
        Booking.customer_id, db.func.count(Booking.booking_id).label('booking_count')
    ).group_by(Booking.customer_id).having(
        db.func.count(Booking.booking_id) > 1
    ).all()
    repeat_guest_ids = [r.customer_id for r in repeat_guest_ids]
    
    guests_data = []
    for guest in all_guests:
        booking_count = Booking.query.filter_by(customer_id=guest.customer_id).count()
        guests_data.append({
            'guest': guest,
            'is_repeat': guest.customer_id in repeat_guest_ids,
            'booking_count': booking_count
        })
    
    return render_template(
        'guests.html',
        active='guests',
        current_date=date.today().strftime('%A, %d %B %Y'),
        guests=guests_data,
        search=search
    )

@guests_router.route('/guests/add', methods=['POST'])
def add_guest():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    phone = request.form.get('phone', '').strip()
    id_type = request.form.get('id_type', '')
    id_number = request.form.get('id_number', '').strip()
    
    import re
    
    # 1. Gmail validation: must end with @gmail.com
    if not email.endswith('@gmail.com') or not re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', email):
        flash('Invalid email. Gmail must end with @gmail.com.', 'error')
        return redirect(url_for('guests.guests_screen'))
        
    # 2. Phone validation: exactly 11 digits, numbers only
    if not phone or len(phone) != 11 or not phone.isdigit():
        flash('Phone number must be exactly 11 digits long and contain only numbers.', 'error')
        return redirect(url_for('guests.guests_screen'))
            
    # 3. CNIC validation: exactly 13 digits, numbers only
    if id_type == 'CNIC':
        if not id_number or len(id_number) != 13 or not id_number.isdigit():
            flash('CNIC must be exactly 13 digits long and contain only numbers.', 'error')
            return redirect(url_for('guests.guests_screen'))
            
    guest = Customer(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        id_type=id_type,
        id_number=id_number,
        created_at=date.today()
    )
    
    db.session.add(guest)
    db.session.commit()
    
    flash('Guest added successfully!', 'success')
    return redirect(url_for('guests.guests_screen'))

@guests_router.route('/guests/delete/<int:id>')
def delete_guest(id):
    guest = Customer.query.get_or_404(id)
    
    # Check if guest has bookings
    booking_count = Booking.query.filter_by(customer_id=id).count()
    if booking_count > 0:
        flash('Cannot delete guest with existing bookings.', 'error')
        return redirect(url_for('guests.guests_screen'))
    
    db.session.delete(guest)
    db.session.commit()
    
    flash('Guest deleted successfully!', 'success')
    return redirect(url_for('guests.guests_screen'))

@guests_router.route('/guests/<int:id>')
def guest_detail(id):
    guest = Customer.query.get_or_404(id)
    bookings = Booking.query.filter_by(customer_id=id).all()
    
    return render_template(
        'guests.html',
        active='guests',
        current_date=date.today().strftime('%A, %d %B %Y'),
        guest=guest,
        bookings=bookings,
        view_detail=True
    )