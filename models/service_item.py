from database import db

class ServiceItem(db.Model):
    __tablename__ = 'service_item'
    
    service_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey('service_category.category_id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    
    # Relationships
    stay_services = db.relationship('StayService', backref='service_item', lazy=True)