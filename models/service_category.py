from database import db

class ServiceCategory(db.Model):
    __tablename__ = 'service_category'
    
    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_name = db.Column(db.String(100), nullable=False)
    
    # Relationships
    service_items = db.relationship('ServiceItem', backref='category', lazy=True)