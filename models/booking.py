from database import db
from datetime import datetime

class Booking(db.Model):
    __tablename__ = 'booking'
    
    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.customer_id'), nullable=False)
    planned_checkin = db.Column(db.Date, nullable=False)
    planned_checkout = db.Column(db.Date, nullable=False)
    actual_checkin = db.Column(db.Date)
    actual_checkout = db.Column(db.Date)
    status = db.Column(db.String(20), nullable=False, default='booked')
    booking_source = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    booking_rooms = db.relationship('BookingRoom', backref='booking', lazy=True)
    invoice = db.relationship('Invoice', backref='booking', uselist=False)