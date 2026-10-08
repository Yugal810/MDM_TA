import pytest
from datetime import date
from app import create_app
from config import TestConfig
from database.database import db
from models.room import Room
from models.booking import Booking

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def room_101(app):
    with app.app_context():
        room = Room(room_number='101', room_type='Deluxe', price=150.0, availability_status='AVAILABLE')
        db.session.add(room)
        db.session.commit()
        return room.id

@pytest.fixture
def maintenance_room(app):
    with app.app_context():
        room = Room(room_number='102', room_type='Suite', price=300.0, availability_status='MAINTENANCE')
        db.session.add(room)
        db.session.commit()
        return room.id

# --------------------------------------------------------------------------
# BOOKING TESTS & CRITICAL OVERLAP LOGIC
# --------------------------------------------------------------------------
def test_successful_booking(client, room_101):
    res = client.post('/api/bookings', json={
        'room_id': room_101,
        'guest_name': 'John Doe',
        'guest_email': 'john@example.com',
        'check_in': '2026-10-10',
        'check_out': '2026-10-15'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['booking_status'] == 'CONFIRMED'
    assert data['data']['guest_name'] == 'John Doe'

def test_overlapping_booking_scenarios(client, room_101):
    """
    Existing Booking: 10 Oct -> 15 Oct
    Reject:
      - 9 Oct -> 11 Oct (overlaps start)
      - 12 Oct -> 16 Oct (overlaps end)
      - 10 Oct -> 15 Oct (exact match)
      - 11 Oct -> 14 Oct (inside)
      - 8 Oct -> 20 Oct (encompasses)
    """
    # 1. Base booking
    res_base = client.post('/api/bookings', json={
        'room_id': room_101,
        'guest_name': 'Base Guest',
        'guest_email': 'base@example.com',
        'check_in': '2026-10-10',
        'check_out': '2026-10-15'
    })
    assert res_base.status_code == 201

    # Conflict 1: 9 Oct -> 11 Oct
    r1 = client.post('/api/bookings', json={
        'room_id': room_101,
        'guest_name': 'Overlap 1',
        'guest_email': 'o1@example.com',
        'check_in': '2026-10-09',
        'check_out': '2026-10-11'
    })
    assert r1.status_code == 409
    assert r1.get_json()['error'] == 'ROOM_UNAVAILABLE'

    # Conflict 2: 12 Oct -> 16 Oct
    r2 = client.post('/api/bookings', json={
        'room_id': room_101,
        'guest_name': 'Overlap 2',
        'guest_email': 'o2@example.com',
        'check_in': '2026-10-12',
        'check_out': '2026-10-16'
    })
    assert r2.status_code == 409
    assert r2.get_json()['error'] == 'ROOM_UNAVAILABLE'

    # Conflict 3: Exact match 10 Oct -> 15 Oct
    r3 = client.post('/api/bookings', json={
        'room_id': room_101,
        'guest_name': 'Overlap 3',
        'guest_email': 'o3@example.com',
        'check_in': '2026-10-10',
        'check_out': '2026-10-15'
    })
    assert r3.status_code == 409

    # Conflict 4: Encompassing 8 Oct -> 20 Oct
    r4 = client.post('/api/bookings', json={
        'room_id': room_101,
        'guest_name': 'Overlap 4',
        'guest_email': 'o4@example.com',
        'check_in': '2026-10-08',
        'check_out': '2026-10-20'
    })
    assert r4.status_code == 409

def test_adjacent_bookings_allowed(client, room_101):
    """
    Existing Booking: 10 Oct -> 15 Oct
    Allow adjacent bookings:
      - 5 Oct -> 10 Oct (checks out when next guest checks in)
      - 15 Oct -> 18 Oct (checks in when previous guest checks out)
    """
    # 1. Base booking
    res_base = client.post('/api/bookings', json={
        'room_id': room_101,
        'guest_name': 'Base Guest',
        'guest_email': 'base@example.com',
        'check_in': '2026-10-10',
        'check_out': '2026-10-15'
    })
    assert res_base.status_code == 201

    # Before: 5 Oct -> 10 Oct
    res_before = client.post('/api/bookings', json={
        'room_id': room_101,
        'guest_name': 'Guest Before',
        'guest_email': 'before@example.com',
        'check_in': '2026-10-05',
        'check_out': '2026-10-10'
    })
    assert res_before.status_code == 201
    assert res_before.get_json()['success'] is True

    # After: 15 Oct -> 18 Oct
    res_after = client.post('/api/bookings', json={
        'room_id': room_101,
        'guest_name': 'Guest After',
        'guest_email': 'after@example.com',
        'check_in': '2026-10-15',
        'check_out': '2026-10-18'
    })
    assert res_after.status_code == 201
    assert res_after.get_json()['success'] is True

def test_invalid_dates(client, room_101):
    # Check-out before check-in
    r1 = client.post('/api/bookings', json={
        'room_id': room_101,
        'guest_name': 'Date Error',
        'guest_email': 'err@example.com',
        'check_in': '2026-10-15',
        'check_out': '2026-10-10'
    })
    assert r1.status_code == 400
    assert r1.get_json()['error'] == 'INVALID_DATE_RANGE'

    # Same day check-in and check-out
    r2 = client.post('/api/bookings', json={
        'room_id': room_101,
        'guest_name': 'Same Day',
        'guest_email': 'sameday@example.com',
        'check_in': '2026-10-10',
        'check_out': '2026-10-10'
    })
    assert r2.status_code == 400
    assert r2.get_json()['error'] == 'INVALID_DATE_RANGE'

    # Malformed date strings
    r3 = client.post('/api/bookings', json={
        'room_id': room_101,
        'guest_name': 'Malformed',
        'guest_email': 'mal@example.com',
        'check_in': 'not-a-date',
        'check_out': '2026-10-15'
    })
    assert r3.status_code == 400
    assert r3.get_json()['error'] == 'INVALID_DATE'

def test_nonexistent_room(client):
    res = client.post('/api/bookings', json={
        'room_id': 99999,
        'guest_name': 'Ghost',
        'guest_email': 'ghost@example.com',
        'check_in': '2026-10-10',
        'check_out': '2026-10-15'
    })
    assert res.status_code == 404
    assert res.get_json()['error'] == 'ROOM_NOT_FOUND'

def test_maintenance_room_cannot_be_booked(client, maintenance_room):
    res = client.post('/api/bookings', json={
        'room_id': maintenance_room,
        'guest_name': 'Alice',
        'guest_email': 'alice@example.com',
        'check_in': '2026-10-10',
        'check_out': '2026-10-15'
    })
    assert res.status_code == 400
    assert res.get_json()['error'] == 'ROOM_IN_MAINTENANCE'

def test_cancel_booking_and_frees_availability(client, room_101):
    # Book
    res = client.post('/api/bookings', json={
        'room_id': room_101,
        'guest_name': 'Canceller',
        'guest_email': 'canceller@example.com',
        'check_in': '2026-10-10',
        'check_out': '2026-10-15'
    })
    booking_id = res.get_json()['data']['id']

    # Room is not available during that window
    avail_res1 = client.get('/api/rooms/available?check_in=2026-10-10&check_out=2026-10-15')
    assert len(avail_res1.get_json()['data']) == 0

    # Cancel booking
    cancel_res = client.delete(f'/api/bookings/{booking_id}')
    assert cancel_res.status_code == 200
    assert cancel_res.get_json()['data']['booking_status'] == 'CANCELLED'

    # Cancelling again returns 400
    cancel_again = client.delete(f'/api/bookings/{booking_id}')
    assert cancel_again.status_code == 400
    assert cancel_again.get_json()['error'] == 'ALREADY_CANCELLED'

    # Now room must be available again for the exact same window!
    avail_res2 = client.get('/api/rooms/available?check_in=2026-10-10&check_out=2026-10-15')
    assert len(avail_res2.get_json()['data']) == 1
    assert avail_res2.get_json()['data'][0]['id'] == room_101

    # New guest can book the previously cancelled slot
    res_new = client.post('/api/bookings', json={
        'room_id': room_101,
        'guest_name': 'New Guest',
        'guest_email': 'new@example.com',
        'check_in': '2026-10-10',
        'check_out': '2026-10-15'
    })
    assert res_new.status_code == 201

def test_delete_room_with_active_booking_rejected(client, room_101):
    # Create active booking
    client.post('/api/bookings', json={
        'room_id': room_101,
        'guest_name': 'Active Guest',
        'guest_email': 'active@example.com',
        'check_in': '2026-10-10',
        'check_out': '2026-10-15'
    })

    # Try to delete room
    del_res = client.delete(f'/api/rooms/{room_101}')
    assert del_res.status_code == 409
    assert del_res.get_json()['error'] == 'ROOM_HAS_ACTIVE_BOOKINGS'
