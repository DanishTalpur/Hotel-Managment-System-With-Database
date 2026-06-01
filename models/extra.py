from database import db

class Extra(db.Model):
    __tablename__ = 'extra'
    
    extra_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    extra_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    
    # Relationships (secondary relationship through association table)
    booking_rooms = db.relationship('BookingRoom', secondary='booking_room_extra', back_populates='extras')