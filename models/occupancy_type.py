from database import db

class OccupancyType(db.Model):
    __tablename__ = 'occupancy_type'
    
    occupancy_type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    min_guests = db.Column(db.Integer, nullable=False)
    max_guests = db.Column(db.Integer, nullable=False)
    
    # Relationships
    rates = db.relationship('Rate', backref='occupancy_type', lazy=True)