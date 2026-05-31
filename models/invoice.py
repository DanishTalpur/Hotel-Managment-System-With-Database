from database import db
from datetime import datetime

class Invoice(db.Model):
    __tablename__ = 'invoice'
    
    invoice_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.booking_id'), nullable=False)
    issued_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    subtotal = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, nullable=False, default=0)
    total_amount = db.Column(db.Float, nullable=False)
    paid_amount = db.Column(db.Float, nullable=False, default=0)
    payment_status = db.Column(db.String(20), nullable=False, default='unpaid')