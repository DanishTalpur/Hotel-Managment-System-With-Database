from database import db

class Facility(db.Model):
    __tablename__ = 'facility'
    
    facility_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    facility_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    
    # Relationships (secondary relationship through association table)
    rate_types = db.relationship('RateType', secondary='rate_facility', back_populates='facilities')


class RateFacility(db.Model):
    __tablename__ = 'rate_facility'
    
    rate_type_id = db.Column(db.Integer, db.ForeignKey('rate_type.rate_type_id'), primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.facility_id'), primary_key=True)