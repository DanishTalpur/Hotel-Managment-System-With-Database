from database import db

class Room(db.Model):
    __tablename__ = 'room'
    
    room_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_number = db.Column(db.String(10), nullable=False)
    floor_number = db.Column(db.Integer, nullable=False)
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_type.room_type_id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='available')
    
    # Relationships
    booking_rooms = db.relationship('BookingRoom', backref='room', lazy=True)
    attributes = db.relationship('RoomAttribute', secondary='room_attribute_map', back_populates='rooms')