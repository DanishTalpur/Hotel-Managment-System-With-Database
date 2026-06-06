from database import db

class BookingRoom(db.Model):
    __tablename__ = 'booking_room'
    
    booking_room_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.booking_id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.room_id'), nullable=False)
    rate_id = db.Column(db.Integer, db.ForeignKey('rate.rate_id'), nullable=False)
    num_guests = db.Column(db.Integer, nullable=False)
    
    # Relationships
    extras = db.relationship('Extra', secondary='booking_room_extra', back_populates='booking_rooms')
    stays = db.relationship('Stay', backref='booking_room', lazy=True)
    rate = db.relationship('Rate', backref='booking_rooms', lazy=True)


class BookingRoomExtra(db.Model):
    __tablename__ = 'booking_room_extra'
    
    booking_room_id = db.Column(db.Integer, db.ForeignKey('booking_room.booking_room_id'), primary_key=True)
    extra_id = db.Column(db.Integer, db.ForeignKey('extra.extra_id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    source = db.Column(db.String(20), primary_key=True, nullable=False, default='booking')
