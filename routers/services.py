from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import ServiceCategory, ServiceItem
from database import db

services_router = Blueprint('services', __name__)

@services_router.route('/services')
def services_screen():
    categories = ServiceCategory.query.all()
    
    # Get all service items grouped by category
    service_items = []
    for category in categories:
        items = ServiceItem.query.filter_by(category_id=category.category_id).all()
        service_items.append({
            'category': category,
            'items': items
        })
    
    from datetime import datetime
    
    return render_template(
        'services.html',
        active='services',
        current_date=datetime.now().strftime('%A, %d %B %Y'),
        categories=categories,
        service_items=service_items
    )

@services_router.route('/services/category/add', methods=['POST'])
def add_category():
    category_name = request.form['category_name']
    
    # Check if category already exists
    existing = ServiceCategory.query.filter_by(category_name=category_name).first()
    if existing:
        flash('Category already exists!', 'error')
        return redirect(url_for('services.services_screen'))
    
    category = ServiceCategory(category_name=category_name)
    db.session.add(category)
    db.session.commit()
    
    flash('Category added successfully!', 'success')
    return redirect(url_for('services.services_screen'))

@services_router.route('/services/category/delete/<int:id>')
def delete_category(id):
    category = ServiceCategory.query.get_or_404(id)
    
    # Check if category has items
    if category.service_items:
        flash('Cannot delete category with service items!', 'error')
        return redirect(url_for('services.services_screen'))
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('services.services_screen'))

@services_router.route('/services/item/add', methods=['POST'])
def add_service_item():
    category_id = int(request.form['category_id'])
    item_name = request.form['item_name']
    unit_price = float(request.form['unit_price'])
    
    item = ServiceItem(
        category_id=category_id,
        item_name=item_name,
        unit_price=unit_price
    )
    db.session.add(item)
    db.session.commit()
    
    flash('Service item added successfully!', 'success')
    return redirect(url_for('services.services_screen'))

@services_router.route('/services/item/delete/<int:id>')
def delete_service_item(id):
    item = ServiceItem.query.get_or_404(id)
    category_id = item.category_id
    
    db.session.delete(item)
    db.session.commit()
    
    flash('Service item deleted successfully!', 'success')
    return redirect(url_for('services.services_screen'))

@services_router.route('/services/item/edit/<int:id>', methods=['POST'])
def edit_service_item(id):
    item = ServiceItem.query.get_or_404(id)
    
    item.item_name = request.form['item_name']
    item.unit_price = float(request.form['unit_price'])
    item.category_id = int(request.form['category_id'])
    
    db.session.commit()
    
    flash('Service item updated successfully!', 'success')
    return redirect(url_for('services.services_screen'))