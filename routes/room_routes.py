from flask import Blueprint, request, jsonify
from services.room_service import RoomService
from services.booking_service import BookingService

room_bp = Blueprint('rooms', __name__, url_prefix='/api/rooms')

@room_bp.route('', methods=['GET'])
def get_rooms():
    """Get all rooms."""
    rooms = RoomService.get_all_rooms()
    return jsonify({
        'success': True,
        'message': 'Rooms retrieved successfully',
        'data': [room.to_dict() for room in rooms]
    }), 200

@room_bp.route('/<int:room_id>', methods=['GET'])
def get_room(room_id):
    """Get a specific room."""
    room = RoomService.get_room_by_id(room_id)
    if not room:
        return jsonify({
            'success': False,
            'message': 'Room not found',
            'error': 'ROOM_NOT_FOUND'
        }), 404
    return jsonify({
        'success': True,
        'message': 'Room retrieved successfully',
        'data': room.to_dict()
    }), 200

@room_bp.route('', methods=['POST'])
def create_room():
    """Create a new room."""
    data = request.get_json() or {}
    room, message, status_code = RoomService.create_room(data)
    if not room:
        error_code = 'ROOM_EXISTS' if status_code == 409 else 'VALIDATION_ERROR'
        return jsonify({
            'success': False,
            'message': message,
            'error': error_code
        }), status_code

    return jsonify({
        'success': True,
        'message': message,
        'data': room.to_dict()
    }), status_code

@room_bp.route('/<int:room_id>', methods=['PUT'])
def update_room(room_id):
    """Update room information."""
    data = request.get_json() or {}
    room, message, status_code = RoomService.update_room(room_id, data)
    if not room:
        error_code = 'ROOM_NOT_FOUND' if status_code == 404 else ('ROOM_EXISTS' if status_code == 409 else 'VALIDATION_ERROR')
        return jsonify({
            'success': False,
            'message': message,
            'error': error_code
        }), status_code

    return jsonify({
        'success': True,
        'message': message,
        'data': room.to_dict()
    }), status_code

@room_bp.route('/<int:room_id>', methods=['DELETE'])
def delete_room(room_id):
    """Delete a room."""
    success, message, status_code = RoomService.delete_room(room_id)
    if not success:
        error_code = 'ROOM_NOT_FOUND' if status_code == 404 else 'ROOM_HAS_ACTIVE_BOOKINGS'
        return jsonify({
            'success': False,
            'message': message,
            'error': error_code
        }), status_code

    return jsonify({
        'success': True,
        'message': message,
        'data': {'room_id': room_id}
    }), 200

@room_bp.route('/search', methods=['GET'])
def search_rooms():
    """Search rooms by room type."""
    room_type = request.args.get('type', '')
    rooms = RoomService.search_rooms_by_type(room_type)
    return jsonify({
        'success': True,
        'message': f"Found {len(rooms)} room(s)",
        'data': [room.to_dict() for room in rooms]
    }), 200

@room_bp.route('/available', methods=['GET'])
def get_available_rooms():
    """Return rooms available for requested period, optional room type filter."""
    check_in_str = request.args.get('check_in')
    check_out_str = request.args.get('check_out')
    room_type = request.args.get('type')

    if not check_in_str or not check_out_str:
        return jsonify({
            'success': False,
            'message': 'Both check_in and check_out query parameters are required',
            'error': 'MISSING_DATE_PARAMS'
        }), 400

    check_in = BookingService.parse_date(check_in_str)
    check_out = BookingService.parse_date(check_out_str)

    if not check_in or not check_out:
        return jsonify({
            'success': False,
            'message': 'Dates must be in format YYYY-MM-DD',
            'error': 'INVALID_DATE_FORMAT'
        }), 400

    if check_in >= check_out:
        return jsonify({
            'success': False,
            'message': 'check_in date must be strictly before check_out date',
            'error': 'INVALID_DATE_RANGE'
        }), 400

    available_rooms = RoomService.get_available_rooms(check_in, check_out, room_type)
    return jsonify({
        'success': True,
        'message': f"Found {len(available_rooms)} available room(s)",
        'data': [room.to_dict() for room in available_rooms]
    }), 200
