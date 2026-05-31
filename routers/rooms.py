from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Room, RoomType, RoomAttribute, RoomAttributeMap
from database import db

rooms_router = Blueprint('rooms', __name__)

@rooms_router.route('/rooms')
def rooms_screen():
    search = request.args.get('search', '')
    room_type_filter = request.args.get('room_type', '')
    status_filter = request.args.get('status', '')
    
    # Base query
    query = Room.query.join(RoomType)
    
    # Apply filters
    if search:
        query = query.filter(Room.room_number.ilike(f'%{search}%'))
    
    if room_type_filter:
        query = query.filter(Room.room_type_id == int(room_type_filter))
    
    if status_filter:
        query = query.filter(Room.status == status_filter)
    
    rooms = query.order_by(Room.room_number).all()
    
    # Get statistics
    total_rooms = Room.query.count()
    vacant_rooms = Room.query.filter_by(status='available').count()
    occupied_rooms = Room.query.filter_by(status='occupied').count()
    maintenance_rooms = Room.query.filter_by(status='maintenance').count()
    
    occupancy_rate = int((occupied_rooms / total_rooms * 100)) if total_rooms > 0 else 0
    
    stats = {
        'total_rooms': total_rooms,
        'vacant': vacant_rooms,
        'occupied': occupied_rooms,
        'maintenance': maintenance_rooms,
        'occupancy_rate': occupancy_rate
    }
    
    # Get room types for filter and form
    room_types = RoomType.query.all()
    
    # Get all attributes
    attributes = RoomAttribute.query.all()
    
    return render_template(
        'index.html',
        active='rooms',
        rooms=rooms,
        stats=stats,
        room_types=room_types,
        attributes=attributes,
        search=search,
        room_type_filter=room_type_filter,
        status_filter=status_filter
    )

@rooms_router.route('/rooms/add', methods=['POST'])
def add_room():
    room_number = request.form['room_number']
    floor_number = int(request.form['floor_number'])
    room_type_id = int(request.form['room_type_id'])
    status = request.form.get('status', 'available')
    
    # Check if room number already exists
    existing = Room.query.filter_by(room_number=room_number).first()
    if existing:
        flash('Room number already exists!', 'error')
        return redirect(url_for('rooms.rooms_screen'))
    
    room = Room(
        room_number=room_number,
        floor_number=floor_number,
        room_type_id=room_type_id,
        status=status
    )
    db.session.add(room)
    db.session.commit()
    
    # Add attributes if selected
    attribute_ids = request.form.getlist('attributes')
    for attr_id in attribute_ids:
        room_attr = RoomAttributeMap(
            room_id=room.room_id,
            attribute_id=int(attr_id)
        )
        db.session.add(room_attr)
    db.session.commit()
    
    flash('Room added successfully!', 'success')
    return redirect(url_for('rooms.rooms_screen'))

@rooms_router.route('/rooms/delete/<int:id>')
def delete_room(id):
    room = Room.query.get_or_404(id)
    
    # Check if room has any bookings
    if room.booking_rooms:
        flash('Cannot delete room with existing bookings!', 'error')
        return redirect(url_for('rooms.rooms_screen'))
    
    # Delete room attributes
    RoomAttributeMap.query.filter_by(room_id=id).delete()
    
    db.session.delete(room)
    db.session.commit()
    
    flash('Room deleted successfully!', 'success')
    return redirect(url_for('rooms.rooms_screen'))

@rooms_router.route('/rooms/update_status/<int:id>/<status>')
def update_room_status(id, status):
    room = Room.query.get_or_404(id)
    room.status = status
    db.session.commit()
    
    flash(f'Room status updated to {status}!', 'success')
    return redirect(url_for('rooms.rooms_screen'))

@rooms_router.route('/rooms/edit/<int:id>', methods=['POST'])
def edit_room(id):
    room = Room.query.get_or_404(id)
    
    room.room_number = request.form['room_number']
    room.floor_number = int(request.form['floor_number'])
    room.room_type_id = int(request.form['room_type_id'])
    room.status = request.form.get('status', 'available')
    
    # Update attributes
    RoomAttributeMap.query.filter_by(room_id=id).delete()
    attribute_ids = request.form.getlist('attributes')
    for attr_id in attribute_ids:
        room_attr = RoomAttributeMap(
            room_id=room.room_id,
            attribute_id=int(attr_id)
        )
        db.session.add(room_attr)
    
    db.session.commit()
    
    flash('Room updated successfully!', 'success')
    return redirect(url_for('rooms.rooms_screen'))