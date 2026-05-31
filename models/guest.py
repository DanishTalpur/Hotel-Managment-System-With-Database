from database import db

class Guest(db.Model):

    __tablename__ = 'guests'

    guest_id = db.Column(
        db.Integer,
        primary_key=True
    )

    first_name = db.Column(
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120)
    )

    phone = db.Column(
        db.String(30)
    )

    nationality = db.Column(
        db.String(50)
    )