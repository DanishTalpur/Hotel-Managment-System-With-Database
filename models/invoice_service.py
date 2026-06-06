from database import db

class InvoiceService(db.Model):
    __tablename__ = 'invoice_service'
    
    invoice_service_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.invoice_id'), nullable=False)
    service_item_id = db.Column(db.Integer, db.ForeignKey('service_item.service_item_id'), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    line_total = db.Column(db.Float, nullable=False)
