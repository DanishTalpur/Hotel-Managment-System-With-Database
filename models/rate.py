from database import db

class Rate(db.Model):
    __tablename__ = 'rate'
    
    rate_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rate_type_id = db.Column(db.Integer, db.ForeignKey('rate_type.rate_type_id'), nullable=False)
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_type.room_type_id'), nullable=False)
    occupancy_type_id = db.Column(db.Integer, db.ForeignKey('occupancy_type.occupancy_type_id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)