import re
from datetime import datetime, date
from database.database import db
from models.room import Room
from models.booking import Booking

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

class BookingService:
    @staticmethod
    def get_all_bookings():
        return Booking.query.order_by(Booking.created_at.desc()).all()

    @staticmethod
    def get_booking_by_id(booking_id):
        return db.session.get(Booking, booking_id)

    @staticmethod
    def parse_date(date_str):
        if not date_str:
            return None
        if isinstance(date_str, (date, datetime)):
            return date_str if isinstance(date_str, date) else date_str.date()
        try:
            return datetime.strptime(str(date_str).strip(), '%Y-%m-%d').date()
        except ValueError:
            return None

    @staticmethod
    def is_room_available(room_id, check_in_date, check_out_date, exclude_booking_id=None):
        """
        Check if room is available between check_in_date and check_out_date.
        Logic: A conflict occurs when:
        new_check_in < existing_check_out AND new_check_out > existing_check_in
        Only CONFIRMED bookings block dates. CANCELLED or COMPLETED do not block.
        """
        query = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.booking_status == 'CONFIRMED',
            Booking.check_in < check_out_date,
            Booking.check_out > check_in_date
        )

        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)

        conflicting_booking = query.first()
        return conflicting_booking is None

    @staticmethod
    def create_booking(data):
        room_id = data.get('room_id')
        guest_name = str(data.get('guest_name', '')).strip()
        guest_email = str(data.get('guest_email', '')).strip()
        check_in_str = data.get('check_in')
        check_out_str = data.get('check_out')

        # 1. Basic validation
        if not room_id:
            return None, "Room ID is required", "MISSING_FIELD", 400

        try:
            room_id = int(room_id)
        except (ValueError, TypeError):
            return None, "Invalid Room ID", "INVALID_FIELD", 400

        if not guest_name:
            return None, "Guest name is required", "MISSING_FIELD", 400

        if not guest_email:
            return None, "Guest email is required", "MISSING_FIELD", 400

        if not re.match(EMAIL_REGEX, guest_email):
            return None, "Invalid email address format", "INVALID_EMAIL", 400

        if not check_in_str:
            return None, "Check-in date is required", "MISSING_FIELD", 400

        if not check_out_str:
            return None, "Check-out date is required", "MISSING_FIELD", 400

        check_in = BookingService.parse_date(check_in_str)
        if not check_in:
            return None, "Invalid check-in date format. Use YYYY-MM-DD", "INVALID_DATE", 400

        check_out = BookingService.parse_date(check_out_str)
        if not check_out:
            return None, "Invalid check-out date format. Use YYYY-MM-DD", "INVALID_DATE", 400

        if check_in >= check_out:
            return None, "Check-in date must be strictly before check-out date", "INVALID_DATE_RANGE", 400

        # 2. Check room existence and maintenance
        room = db.session.get(Room, room_id)
        if not room:
            return None, "Room not found", "ROOM_NOT_FOUND", 404

        if room.availability_status == 'MAINTENANCE':
            return None, "Room is currently under maintenance and cannot be booked", "ROOM_IN_MAINTENANCE", 400

        # 3. Check for overlapping bookings
        if not BookingService.is_room_available(room_id, check_in, check_out):
            return None, "Room is already booked for the selected dates", "ROOM_UNAVAILABLE", 409

        booking = Booking(
            room_id=room_id,
            guest_name=guest_name,
            guest_email=guest_email,
            check_in=check_in,
            check_out=check_out,
            booking_status='CONFIRMED'
        )

        db.session.add(booking)
        db.session.commit()
        return booking, "Room booked successfully", None, 201

    @staticmethod
    def cancel_booking(booking_id):
        booking = BookingService.get_booking_by_id(booking_id)
        if not booking:
            return None, "Booking not found", "BOOKING_NOT_FOUND", 404

        if booking.booking_status == 'CANCELLED':
            return None, "Booking is already cancelled", "ALREADY_CANCELLED", 400

        booking.booking_status = 'CANCELLED'
        db.session.commit()
        return booking, "Booking cancelled successfully", None, 200
