from database import db

class RoomAttribute(db.Model):
    __tablename__ = 'room_attribute'
    
    attribute_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    attribute_name = db.Column(db.String(100), nullable=False)
    
    # Relationships (secondary relationship through association table)
    rooms = db.relationship('Room', secondary='room_attribute_map', back_populates='attributes')


class RoomAttributeMap(db.Model):
    __tablename__ = 'room_attribute_map'
    
    room_id = db.Column(db.Integer, db.ForeignKey('room.room_id'), primary_key=True)
    attribute_id = db.Column(db.Integer, db.ForeignKey('room_attribute.attribute_id'), primary_key=True)