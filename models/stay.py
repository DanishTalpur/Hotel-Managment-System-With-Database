from database import db

class Stay(db.Model):
    __tablename__ = 'stay'
    
    stay_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_room_id = db.Column(db.Integer, db.ForeignKey('booking_room.booking_room_id'), nullable=False)
    stay_date = db.Column(db.Date, nullable=False)
    applied_rate = db.Column(db.Float, nullable=False)
    room_charge = db.Column(db.Float, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('booking_room_id', 'stay_date', name='uq_booking_room_stay_date'),
    )
    
    # Relationships
    stay_services = db.relationship('StayService', backref='stay', lazy=True)