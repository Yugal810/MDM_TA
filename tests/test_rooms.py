import pytest
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
def sample_room(app):
    with app.app_context():
        room = Room(room_number='101', room_type='Deluxe', price=150.0, availability_status='AVAILABLE')
        db.session.add(room)
        db.session.commit()
        return room.id

# --------------------------------------------------------------------------
# ROOM TESTS
# --------------------------------------------------------------------------
def test_create_room_success(client):
    res = client.post('/api/rooms', json={
        'room_number': '102',
        'room_type': 'Single',
        'price': 80.0,
        'availability_status': 'AVAILABLE'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['room_number'] == '102'
    assert data['data']['price'] == 80.0

def test_get_rooms(client, sample_room):
    res = client.get('/api/rooms')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert len(data['data']) >= 1
    assert data['data'][0]['id'] == sample_room

def test_get_single_room(client, sample_room):
    res = client.get(f'/api/rooms/{sample_room}')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['room_number'] == '101'

def test_get_nonexistent_room(client):
    res = client.get('/api/rooms/99999')
    assert res.status_code == 404
    data = res.get_json()
    assert data['success'] is False
    assert data['error'] == 'ROOM_NOT_FOUND'

def test_update_room(client, sample_room):
    res = client.put(f'/api/rooms/{sample_room}', json={
        'price': 180.0,
        'room_type': 'Suite'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['price'] == 180.0
    assert data['data']['room_type'] == 'Suite'

def test_delete_room(client, sample_room):
    res = client.delete(f'/api/rooms/{sample_room}')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True

    # Verify room is gone
    check_res = client.get(f'/api/rooms/{sample_room}')
    assert check_res.status_code == 404

def test_duplicate_room_number(client, sample_room):
    res = client.post('/api/rooms', json={
        'room_number': '101',
        'room_type': 'Double',
        'price': 100.0,
        'availability_status': 'AVAILABLE'
    })
    assert res.status_code == 409
    data = res.get_json()
    assert data['success'] is False
    assert data['error'] == 'ROOM_EXISTS'

def test_invalid_price(client):
    # Negative price
    res1 = client.post('/api/rooms', json={
        'room_number': '103',
        'room_type': 'Single',
        'price': -50.0
    })
    assert res1.status_code == 400
    assert res1.get_json()['success'] is False

    # Zero price
    res2 = client.post('/api/rooms', json={
        'room_number': '104',
        'room_type': 'Single',
        'price': 0
    })
    assert res2.status_code == 400

    # Non-numeric price
    res3 = client.post('/api/rooms', json={
        'room_number': '105',
        'room_type': 'Single',
        'price': 'invalid'
    })
    assert res3.status_code == 400

def test_search_rooms_by_type(client, app):
    with app.app_context():
        r1 = Room(room_number='201', room_type='Deluxe', price=200.0)
        r2 = Room(room_number='202', room_type='Single', price=90.0)
        db.session.add_all([r1, r2])
        db.session.commit()

    res = client.get('/api/rooms/search?type=Deluxe')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    for room in data['data']:
        assert room['room_type'] == 'Deluxe'
