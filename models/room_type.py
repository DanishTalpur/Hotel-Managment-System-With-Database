from database import db

class RoomType(db.Model):
    __tablename__ = 'room_type'
    
    room_type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type_name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255))
    
    # Relationships
    rooms = db.relationship('Room', backref='room_type', lazy=True)
    rates = db.relationship('Rate', backref='room_type', lazy=True)