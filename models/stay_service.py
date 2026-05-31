from database import db
from datetime import datetime

class StayService(db.Model):
    __tablename__ = 'stay_service'
    
    stay_service_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stay_id = db.Column(db.Integer, db.ForeignKey('stay.stay_id'), nullable=False)
    service_item_id = db.Column(db.Integer, db.ForeignKey('service_item.service_item_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)