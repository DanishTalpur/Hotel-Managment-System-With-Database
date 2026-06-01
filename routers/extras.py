from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Extra, Booking, BookingRoom, BookingRoomExtra
from database import db
from sqlalchemy import func
from datetime import datetime

extras_router = Blueprint('extras', __name__)

@extras_router.route('/extras')
def extras_screen():
    all_extras = Extra.query.order_by(Extra.extra_name).all()
    
    # Calculate statistics
    total_extras = Extra.query.count()
    
    # Get this month's info
    this_month = datetime.now().month
    this_year = datetime.now().year
    
    # Get total booked count this month
    booked_count = db.session.query(func.sum(BookingRoomExtra.quantity)).join(BookingRoom).join(Booking).filter(
        db.extract('month', Booking.created_at) == this_month,
        db.extract('year', Booking.created_at) == this_year
    ).scalar() or 0
    
    # Most popular extra name & count this month
    popular_query = db.session.query(
        Extra.extra_name, func.sum(BookingRoomExtra.quantity).label('qty_sum')
    ).join(BookingRoomExtra, Extra.extra_id == BookingRoomExtra.extra_id).join(BookingRoom).join(Booking).filter(
        db.extract('month', Booking.created_at) == this_month,
        db.extract('year', Booking.created_at) == this_year
    ).group_by(Extra.extra_name).order_by(func.sum(BookingRoomExtra.quantity).desc()).first()
    
    popular_name = popular_query[0] if popular_query else 'None'
    popular_count = popular_query[1] if popular_query else 0
    
    # Total revenue this month from extras (sum of price * quantity)
    revenue = db.session.query(
        func.sum(Extra.price * BookingRoomExtra.quantity)
    ).join(BookingRoomExtra, Extra.extra_id == BookingRoomExtra.extra_id).join(BookingRoom).join(Booking).filter(
        db.extract('month', Booking.created_at) == this_month,
        db.extract('year', Booking.created_at) == this_year
    ).scalar() or 0
    
    stats = {
        'total_extras': total_extras,
        'booked_count': booked_count,
        'popular_name': popular_name,
        'popular_count': popular_count,
        'revenue': revenue
    }
    
    # Usage this month: for each extra, calculate its count and percentage
    usage_list = []
    # Query all extras and their usage counts (filtering the join on active month)
    extras_usage = db.session.query(
        Extra.extra_name, func.sum(BookingRoomExtra.quantity).label('qty_sum')
    ).outerjoin(BookingRoomExtra, Extra.extra_id == BookingRoomExtra.extra_id).outerjoin(BookingRoom).outerjoin(Booking).filter(
        db.or_(
            Booking.created_at == None,
            db.and_(
                db.extract('month', Booking.created_at) == this_month,
                db.extract('year', Booking.created_at) == this_year
            )
        )
    ).group_by(Extra.extra_id, Extra.extra_name).order_by(func.sum(BookingRoomExtra.quantity).desc()).all()
    
    # Find max usage count to calculate percentage
    max_count = max([row[1] or 0 for row in extras_usage] + [1])
    
    for row in extras_usage:
        count = row[1] or 0
        usage_list.append({
            'extra_name': row[0],
            'count': count,
            'pct': int((count / max_count) * 100)
        })
    
    return render_template(
        'extras.html',
        active='extras',
        current_date=datetime.now().strftime('%A, %d %B %Y'),
        extras=all_extras,
        stats=stats,
        usage_list=usage_list
    )

@extras_router.route('/extras/add', methods=['POST'])
def add_extra():
    extra_name = request.form['extra_name']
    price = float(request.form['price'])
    description = request.form.get('description', '')
    
    # Check if extra already exists
    existing = Extra.query.filter_by(extra_name=extra_name).first()
    if existing:
        flash('Extra item already exists!', 'error')
        return redirect(url_for('extras.extras_screen'))
    
    extra = Extra(
        extra_name=extra_name,
        price=price,
        description=description
    )
    db.session.add(extra)
    db.session.commit()
    
    flash('Extra item added successfully!', 'success')
    return redirect(url_for('extras.extras_screen'))

@extras_router.route('/extras/delete/<int:id>')
def delete_extra(id):
    extra = Extra.query.get_or_404(id)
    
    # Clean up associations first to prevent IntegrityError
    BookingRoomExtra.query.filter_by(extra_id=id).delete()
    
    db.session.delete(extra)
    db.session.commit()
    
    flash('Extra item deleted successfully!', 'success')
    return redirect(url_for('extras.extras_screen'))

@extras_router.route('/extras/edit/<int:id>', methods=['POST'])
def edit_extra(id):
    extra = Extra.query.get_or_404(id)
    
    extra.extra_name = request.form['extra_name']
    extra.price = float(request.form['price'])
    extra.description = request.form.get('description', '')
    
    db.session.commit()
    
    flash('Extra item updated successfully!', 'success')
    return redirect(url_for('extras.extras_screen'))