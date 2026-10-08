from datetime import date
from database.database import db
from models.room import Room
from models.booking import Booking

class RoomService:
    @staticmethod
    def get_all_rooms():
        return Room.query.order_by(Room.room_number.asc()).all()

    @staticmethod
    def get_room_by_id(room_id):
        return db.session.get(Room, room_id)

    @staticmethod
    def get_room_by_number(room_number):
        return Room.query.filter_by(room_number=room_number).first()

    @staticmethod
    def create_room(data):
        room_number = str(data.get('room_number', '')).strip()
        room_type = str(data.get('room_type', '')).strip()
        price = data.get('price')
        availability_status = str(data.get('availability_status', 'AVAILABLE')).strip().upper()

        # Validation
        if not room_number:
            return None, "Room number is required", 400
        
        valid_types = ['Single', 'Double', 'Deluxe', 'Suite']
        # Case-insensitive match normalization for room types
        matched_type = next((t for t in valid_types if t.lower() == room_type.lower()), None)
        if not matched_type:
            return None, f"Invalid room type. Must be one of: {', '.join(valid_types)}", 400
        room_type = matched_type

        try:
            price = float(price)
            if price <= 0:
                return None, "Price must be greater than 0", 400
        except (ValueError, TypeError):
            return None, "Price must be a valid positive number", 400

        valid_statuses = ['AVAILABLE', 'BOOKED', 'MAINTENANCE']
        if availability_status not in valid_statuses:
            return None, f"Invalid status. Must be one of: {', '.join(valid_statuses)}", 400

        # Unique check
        existing = RoomService.get_room_by_number(room_number)
        if existing:
            return None, f"Room number '{room_number}' already exists", 409

        room = Room(
            room_number=room_number,
            room_type=room_type,
            price=price,
            availability_status=availability_status
        )
        db.session.add(room)
        db.session.commit()
        return room, "Room created successfully", 201

    @staticmethod
    def update_room(room_id, data):
        room = RoomService.get_room_by_id(room_id)
        if not room:
            return None, "Room not found", 404

        if 'room_number' in data:
            new_number = str(data['room_number']).strip()
            if not new_number:
                return None, "Room number cannot be empty", 400
            existing = Room.query.filter(Room.room_number == new_number, Room.id != room_id).first()
            if existing:
                return None, f"Room number '{new_number}' is already taken", 409
            room.room_number = new_number

        if 'room_type' in data:
            room_type = str(data['room_type']).strip()
            valid_types = ['Single', 'Double', 'Deluxe', 'Suite']
            matched_type = next((t for t in valid_types if t.lower() == room_type.lower()), None)
            if not matched_type:
                return None, f"Invalid room type. Must be one of: {', '.join(valid_types)}", 400
            room.room_type = matched_type

        if 'price' in data:
            try:
                price = float(data['price'])
                if price <= 0:
                    return None, "Price must be greater than 0", 400
                room.price = price
            except (ValueError, TypeError):
                return None, "Price must be a valid positive number", 400

        if 'availability_status' in data:
            status = str(data['availability_status']).strip().upper()
            valid_statuses = ['AVAILABLE', 'BOOKED', 'MAINTENANCE']
            if status not in valid_statuses:
                return None, f"Invalid status. Must be one of: {', '.join(valid_statuses)}", 400
            room.availability_status = status

        db.session.commit()
        return room, "Room updated successfully", 200

    @staticmethod
    def delete_room(room_id):
        room = RoomService.get_room_by_id(room_id)
        if not room:
            return False, "Room not found", 404

        # Business rule: Check if room has active (CONFIRMED) bookings
        active_bookings = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.booking_status == 'CONFIRMED'
        ).count()

        if active_bookings > 0:
            return False, "Cannot delete room with active bookings. Cancel or complete bookings first.", 409

        db.session.delete(room)
        db.session.commit()
        return True, "Room deleted successfully", 200

    @staticmethod
    def search_rooms_by_type(room_type):
        if not room_type:
            return RoomService.get_all_rooms()
        return Room.query.filter(Room.room_type.ilike(room_type.strip())).order_by(Room.room_number.asc()).all()

    @staticmethod
    def get_available_rooms(check_in_date: date, check_out_date: date, room_type=None):
        """
        Finds rooms available between check_in_date and check_out_date.
        Excludes rooms that are in MAINTENANCE.
        Excludes rooms that have active (CONFIRMED) bookings overlapping:
        new_check_in < existing_check_out AND new_check_out > existing_check_in
        """
        # Find room_ids that have conflicting active bookings
        conflicting_room_ids = db.session.query(Booking.room_id).filter(
            Booking.booking_status == 'CONFIRMED',
            Booking.check_in < check_out_date,
            Booking.check_out > check_in_date
        ).distinct()

        query = Room.query.filter(
            Room.availability_status != 'MAINTENANCE',
            ~Room.id.in_(conflicting_room_ids)
        )

        if room_type:
            query = query.filter(Room.room_type.ilike(room_type.strip()))

        return query.order_by(Room.room_number.asc()).all()
