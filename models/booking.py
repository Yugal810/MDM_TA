from datetime import datetime, timezone
from database.database import db

class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False, index=True)
    guest_name = db.Column(db.String(120), nullable=False)
    guest_email = db.Column(db.String(120), nullable=False)
    check_in = db.Column(db.Date, nullable=False, index=True)
    check_out = db.Column(db.Date, nullable=False, index=True)
    booking_status = db.Column(db.String(20), nullable=False, default='CONFIRMED')  # CONFIRMED, CANCELLED, COMPLETED
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'room_number': self.room.room_number if self.room else None,
            'room_type': self.room.room_type if self.room else None,
            'guest_name': self.guest_name,
            'guest_email': self.guest_email,
            'check_in': self.check_in.strftime('%Y-%m-%d') if self.check_in else None,
            'check_out': self.check_out.strftime('%Y-%m-%d') if self.check_out else None,
            'booking_status': self.booking_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
