from database import db

class RateType(db.Model):
    __tablename__ = 'rate_type'
    
    rate_type_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rate_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    
    # Relationships
    rates = db.relationship('Rate', backref='rate_type', lazy=True)
    facilities = db.relationship('Facility', secondary='rate_facility', back_populates='rate_types')