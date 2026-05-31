from database import db

class Reservation(db.Model):
    __tablename__ = "reservations"

    reservation_id = db.Column(db.Integer, primary_key=True)

    guest_id = db.Column(
        db.Integer,
        db.ForeignKey("guests.guest_id")
    )

    room_id = db.Column(
        db.Integer,
        db.ForeignKey("rooms.room_id")
    )

    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)

    status = db.Column(
        db.String(20),
        default="Confirmed"
    )