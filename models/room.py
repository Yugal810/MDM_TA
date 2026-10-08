from datetime import datetime, timezone
from database.database import db

class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    room_type = db.Column(db.String(50), nullable=False)  # Single, Double, Deluxe, Suite
    price = db.Column(db.Float, nullable=False)
    availability_status = db.Column(db.String(20), nullable=False, default='AVAILABLE')  # AVAILABLE, BOOKED, MAINTENANCE
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # 1 Room -> Many Bookings relationship
    bookings = db.relationship('Booking', backref='room', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'room_number': self.room_number,
            'room_type': self.room_type,
            'price': float(self.price),
            'availability_status': self.availability_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
