from database import db

class InvoiceExtra(db.Model):
    __tablename__ = 'invoice_extra'
    
    invoice_extra_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.invoice_id'), nullable=False)
    extra_id = db.Column(db.Integer, db.ForeignKey('extra.extra_id'), nullable=False)
    extra_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    line_total = db.Column(db.Float, nullable=False)
