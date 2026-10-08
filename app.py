from flask import Flask, render_template, jsonify
from config import Config
from database.database import db
from models.room import Room
from models.booking import Booking
from routes.room_routes import room_bp
from routes.booking_routes import booking_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(room_bp)
    app.register_blueprint(booking_bp)

    # Main dashboard view
    @app.route('/')
    def index():
        return render_template('index.html')

    # Global error handlers for consistent JSON API responses
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'success': False,
            'message': 'Requested resource or route was not found',
            'error': 'NOT_FOUND'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'An internal server error occurred',
            'error': 'INTERNAL_SERVER_ERROR'
        }), 500

    # Auto create tables on startup
    with app.app_context():
        db.create_all()

    return app

def seed_sample_data(app):
    """Ensure the hotel demo data uses realistic INR rates and refresh stale sample records."""
    from datetime import date

    expected_rooms = [
        {'room_number': '101', 'room_type': 'Single', 'price': 3200.0, 'availability_status': 'AVAILABLE'},
        {'room_number': '102', 'room_type': 'Single', 'price': 3400.0, 'availability_status': 'AVAILABLE'},
        {'room_number': '201', 'room_type': 'Double', 'price': 4800.0, 'availability_status': 'AVAILABLE'},
        {'room_number': '202', 'room_type': 'Double', 'price': 5200.0, 'availability_status': 'AVAILABLE'},
        {'room_number': '301', 'room_type': 'Deluxe', 'price': 8200.0, 'availability_status': 'AVAILABLE'},
        {'room_number': '302', 'room_type': 'Deluxe', 'price': 9100.0, 'availability_status': 'AVAILABLE'},
        {'room_number': '401', 'room_type': 'Suite', 'price': 14500.0, 'availability_status': 'AVAILABLE'},
        {'room_number': '402', 'room_type': 'Suite', 'price': 15800.0, 'availability_status': 'MAINTENANCE'},
    ]

    with app.app_context():
        existing_rooms = {room.room_number: room for room in Room.query.all()}

        for room_data in expected_rooms:
            room = existing_rooms.get(room_data['room_number'])
            if room is None:
                db.session.add(Room(**room_data))
            else:
                room.room_type = room_data['room_type']
                room.price = room_data['price']
                room.availability_status = room_data['availability_status']

        db.session.commit()

        if Booking.query.count() == 0:
            room_101 = Room.query.filter_by(room_number='101').first()
            if room_101:
                sample_booking = Booking(
                    room_id=room_101.id,
                    guest_name="John Doe",
                    guest_email="john@example.com",
                    check_in=date(2026, 10, 10),
                    check_out=date(2026, 10, 15),
                    booking_status='CONFIRMED'
                )
                db.session.add(sample_booking)
                db.session.commit()

if __name__ == '__main__':
    app = create_app()
    seed_sample_data(app)
    print("Hotel Booking System running on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
