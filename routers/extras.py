from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Extra
from database import db

extras_router = Blueprint('extras', __name__)

@extras_router.route('/extras')
def extras_screen():
    all_extras = Extra.query.order_by(Extra.extra_name).all()
    
    # Calculate statistics
    total_extras = Extra.query.count()
    total_value = db.session.query(db.func.sum(Extra.price)).scalar() or 0
    
    stats = {
        'total_extras': total_extras,
        'total_value': total_value
    }
    
    return render_template(
        'index.html',
        active='extras',
        extras=all_extras,
        stats=stats
    )

@extras_router.route('/extras/add', methods=['POST'])
def add_extra():
    extra_name = request.form['extra_name']
    price = float(request.form['price'])
    
    # Check if extra already exists
    existing = Extra.query.filter_by(extra_name=extra_name).first()
    if existing:
        flash('Extra item already exists!', 'error')
        return redirect(url_for('extras.extras_screen'))
    
    extra = Extra(
        extra_name=extra_name,
        price=price
    )
    db.session.add(extra)
    db.session.commit()
    
    flash('Extra item added successfully!', 'success')
    return redirect(url_for('extras.extras_screen'))

@extras_router.route('/extras/delete/<int:id>')
def delete_extra(id):
    extra = Extra.query.get_or_404(id)
    
    db.session.delete(extra)
    db.session.commit()
    
    flash('Extra item deleted successfully!', 'success')
    return redirect(url_for('extras.extras_screen'))

@extras_router.route('/extras/edit/<int:id>', methods=['POST'])
def edit_extra(id):
    extra = Extra.query.get_or_404(id)
    
    extra.extra_name = request.form['extra_name']
    extra.price = float(request.form['price'])
    
    db.session.commit()
    
    flash('Extra item updated successfully!', 'success')
    return redirect(url_for('extras.extras_screen'))