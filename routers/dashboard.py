from flask import Blueprint, render_template, redirect, url_for
from models import Room, RoomType, Booking, Customer, Invoice
from datetime import datetime, date

dashboard_router = Blueprint('dashboard', __name__)

@dashboard_router.route('/')
def dashboard():
    today = date.today()
    
    # Get room statistics
    total_rooms = Room.query.count()
    occupied_rooms = Room.query.filter_by(status='occupied').count()
    vacant_rooms = Room.query.filter_by(status='available').count()
    maintenance_rooms = Room.query.filter_by(status='maintenance').count()
    checkout_rooms = Room.query.filter_by(status='checkout').count()
    
    # Calculate occupancy rate
    occupancy_rate = int((occupied_rooms / total_rooms * 100)) if total_rooms > 0 else 0
    
    # Get today's check-ins and check-outs
    checkins_today = Booking.query.filter(
        Booking.planned_checkin == today,
        Booking.status.in_(['booked', 'pending'])
    ).count()
    
    checkouts_today = Booking.query.filter(
        Booking.planned_checkout == today,
        Booking.status.in_(['checked_in'])
    ).count()
    
    # Get room map data
    rooms = Room.query.order_by(Room.room_number).all()
    room_map = []
    for room in rooms:
        room_map.append({
            'room_id': room.room_id,
            'room_number': room.room_number,
            'status': room.status,
            'type_name': room.room_type.type_name if room.room_type else 'N/A'
        })
    
    # Get today's activities (check-ins and check-outs)
    today_activities = []
    
    # Check-ins
    checkin_bookings = Booking.query.filter(
        Booking.planned_checkin == today
    ).limit(5).all()
    
    for booking in checkin_bookings:
        customer = Customer.query.get(booking.customer_id)
        if customer and booking.booking_rooms:
            room = booking.booking_rooms[0].room if booking.booking_rooms else None
            today_activities.append({
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'room_number': room.room_number if room else 'N/A',
                'type_name': room.room_type.type_name if room and room.room_type else 'N/A',
                'booking_status': 'Check-in'
            })
    
    # Get upcoming reservations
    upcoming_bookings = Booking.query.filter(
        Booking.planned_checkin >= today,
        Booking.status.in_(['booked', 'pending'])
    ).order_by(Booking.planned_checkin).limit(5).all()
    
    upcoming_list = []
    for booking in upcoming_bookings:
        customer = Customer.query.get(booking.customer_id)
        if customer:
            room_number = 'N/A'
            if booking.booking_rooms and booking.booking_rooms[0].room:
                room_number = booking.booking_rooms[0].room.room_number
            upcoming_list.append({
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'room_number': room_number,
                'planned_checkin': booking.planned_checkin.strftime('%d %b %Y') if booking.planned_checkin else '',
                'planned_checkout': booking.planned_checkout.strftime('%d %b %Y') if booking.planned_checkout else '',
                'status': booking.status
            })
    
    stats = {
        'total_rooms': total_rooms,
        'occupied': occupied_rooms,
        'vacant': vacant_rooms,
        'maintenance': maintenance_rooms,
        'checkouts_today': checkouts_today,
        'checkins_today': checkins_today,
        'occupancy_rate': occupancy_rate
    }
    
    return render_template(
        'dashboard.html',
        active='dashboard',
        current_date=datetime.now().strftime('%A, %d %B %Y'),
        stats=stats,
        room_map=room_map,
        today_activities=today_activities,
        upcoming_bookings=upcoming_list
    )