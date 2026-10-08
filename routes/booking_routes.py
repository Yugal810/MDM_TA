from flask import Blueprint, request, jsonify
from services.booking_service import BookingService

booking_bp = Blueprint('bookings', __name__, url_prefix='/api/bookings')

@booking_bp.route('', methods=['GET'])
def get_bookings():
    """List all bookings."""
    bookings = BookingService.get_all_bookings()
    return jsonify({
        'success': True,
        'message': 'Bookings retrieved successfully',
        'data': [b.to_dict() for b in bookings]
    }), 200

@booking_bp.route('/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    """Get a specific booking."""
    booking = BookingService.get_booking_by_id(booking_id)
    if not booking:
        return jsonify({
            'success': False,
            'message': 'Booking not found',
            'error': 'BOOKING_NOT_FOUND'
        }), 404

    return jsonify({
        'success': True,
        'message': 'Booking retrieved successfully',
        'data': booking.to_dict()
    }), 200

@booking_bp.route('', methods=['POST'])
def create_booking():
    """Create a new booking with overlap prevention."""
    data = request.get_json() or {}
    booking, message, error_code, status_code = BookingService.create_booking(data)

    if not booking:
        return jsonify({
            'success': False,
            'message': message,
            'error': error_code
        }), status_code

    return jsonify({
        'success': True,
        'message': message,
        'data': booking.to_dict()
    }), status_code

@booking_bp.route('/<int:booking_id>', methods=['DELETE'])
def cancel_booking(booking_id):
    """Cancel a booking."""
    booking, message, error_code, status_code = BookingService.cancel_booking(booking_id)

    if not booking:
        return jsonify({
            'success': False,
            'message': message,
            'error': error_code
        }), status_code

    return jsonify({
        'success': True,
        'message': message,
        'data': booking.to_dict()
    }), 200
