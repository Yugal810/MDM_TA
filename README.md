# 🏨 Grand Stay Hotel Room Booking System

A production-style, clean architecture Hotel Room Booking System designed as a high-standard academic mini-project. Built strictly with **Python (Flask)**, **SQLAlchemy ORM (SQLite)**, and a responsive **HTML5/CSS3/Vanilla JavaScript** single-page dashboard using the **Fetch API**.

---

## 🌟 Key Features

- **Room Inventory Management**: Add rooms, view all rooms, edit room details/pricing, and delete rooms with protection against deleting rooms that have active bookings.
- **Dynamic Availability Search**: Query room availability for custom check-in and check-out dates and filter by room type without refreshing the page.
- **Robust Overlap Prevention Algorithm**: Rejects double-bookings using mathematical interval intersection logic:
  $$\text{Conflict} \iff (\text{new\_check\_in} < \text{existing\_check\_out}) \land (\text{new\_check\_out} > \text{existing\_check\_in})$$
- **Boundary Touching Allowed**: Guests can check in on the same calendar day another guest checks out (e.g. Booking 10–15 Oct allows 5–10 Oct and 15–18 Oct).
- **Booking Lifecycle & Cancellation**: Confirm bookings and cancel bookings instantly with automatic release of room availability back to the pool.
- **Strict Validation**: Input sanitization, email regex validation, positive price checks, date logical ordering (`check_in < check_out`), and maintenance status safeguards.
- **RESTful API**: Standardized JSON response envelope across all endpoints with proper HTTP status codes (`200`, `201`, `400`, `404`, `409`, `500`).
- **Reactive Dashboard UI**: Live KPI cards, modals, interactive status badges, loading states, empty states, and toast notifications.
- **Automated Pytest Suite**: 17 comprehensive unit and integration tests covering CRUD, edge cases, date arithmetic, adjacent check-ins, and cancellations.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+, Flask 3.1.0 |
| **ORM & Database** | SQLAlchemy 2.0+, SQLite3 |
| **Frontend** | HTML5, CSS3 (Modern Flexbox/Grid), Vanilla JavaScript (ES6+ async/await & Fetch API) |
| **Testing** | Pytest 8.3.4 |

> *No React, Node.js backend, MongoDB, or heavy external CSS frameworks used, adhering strictly to the assignment specifications.*

---

## 🏛️ Project Architecture

```
hotel-booking-system/
│
├── app.py                      # Application factory, route registration, sample data seeding
├── config.py                   # Development, production, and in-memory test configurations
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest runner configuration
├── README.md                   # Comprehensive documentation
│
├── models/
│   ├── room.py                 # Room SQLAlchemy model (Room 1 ─── * Bookings)
│   └── booking.py              # Booking SQLAlchemy model
│
├── routes/
│   ├── room_routes.py          # REST API endpoints for /api/rooms
│   └── booking_routes.py       # REST API endpoints for /api/bookings
│
├── services/
│   ├── room_service.py         # Business logic for rooms and dynamic availability query
│   └── booking_service.py      # Booking validations and date conflict resolution
│
├── database/
│   └── database.py             # Shared SQLAlchemy instance
│
├── templates/
│   └── index.html              # Single-page hotel administration & booking interface
│
├── static/
│   ├── css/
│   │   └── style.css           # Modern hotel admin UI styling, badges, modals, toasts
│   └── js/
│       └── app.js              # Fetch API integration, reactive state management, DOM manipulation
│
└── tests/
    ├── test_rooms.py           # Room creation, update, delete, duplicate checks
    └── test_bookings.py        # Booking lifecycle, overlapping date tests, boundary touch tests
```

---

## 🗄️ Database Schema

### 1. `rooms` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique room ID |
| `room_number` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Room identifier (e.g. "101", "302") |
| `room_type` | VARCHAR(50) | NOT NULL | Single, Double, Deluxe, Suite |
| `price` | FLOAT | NOT NULL | Price per night (must be > 0) |
| `availability_status`| VARCHAR(20) | NOT NULL, DEFAULT 'AVAILABLE' | AVAILABLE, BOOKED, MAINTENANCE |
| `created_at` | DATETIME | NOT NULL | Record creation timestamp (UTC) |
| `updated_at` | DATETIME | NOT NULL | Last update timestamp (UTC) |

### 2. `bookings` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique booking ID |
| `room_id` | INTEGER | FOREIGN KEY (`rooms.id`), NOT NULL | Reference to the booked room |
| `guest_name` | VARCHAR(120)| NOT NULL | Guest full name |
| `guest_email`| VARCHAR(120)| NOT NULL | Valid email address |
| `check_in` | DATE | NOT NULL, INDEX | Booking check-in date |
| `check_out` | DATE | NOT NULL, INDEX | Booking check-out date |
| `booking_status` | VARCHAR(20) | NOT NULL, DEFAULT 'CONFIRMED'| CONFIRMED, CANCELLED, COMPLETED |
| `created_at` | DATETIME | NOT NULL | Booking timestamp (UTC) |
| `updated_at` | DATETIME | NOT NULL | Last update timestamp (UTC) |

**Relationship**: `Room (1)` ──── `(N) Bookings` (Configured with `cascade="all, delete-orphan"`).

---

## 🧠 Booking Conflict Algorithm

A new booking with requested interval `[new_check_in, new_check_out]` conflicts with an existing `CONFIRMED` booking `[existing_check_in, existing_check_out]` if and only if:

```
new_check_in < existing_check_out AND new_check_out > existing_check_in
```

### Examples with Existing Booking `[2026-10-10 → 2026-10-15]`:
- **Reject (Overlaps Start)**: `2026-10-09 → 2026-10-11` ($10-09 < 10-15 \land 10-11 > 10-10 \implies \text{True}$)
- **Reject (Overlaps End)**: `2026-10-12 → 2026-10-16` ($10-12 < 10-15 \land 10-16 > 10-10 \implies \text{True}$)
- **Reject (Exact Match)**: `2026-10-10 → 2026-10-15`
- **Reject (Inside Window)**: `2026-10-11 → 2026-10-14`
- **Allow (Checkout Boundary)**: `2026-10-05 → 2026-10-10` ($10-10 > 10-10$ is $\text{False}$)
- **Allow (Checkin Boundary)**: `2026-10-15 → 2026-10-18` ($10-15 < 10-15$ is $\text{False}$)
- **Allow (Cancelled)**: Any date if the existing booking status is `CANCELLED`.

---

## 📡 REST API Documentation

### Standard Response Formats

#### Success (`200 OK` / `201 Created`):
```json
{
  "success": true,
  "message": "Room booked successfully",
  "data": { ... }
}
```

#### Error (`400 Bad Request` / `404 Not Found` / `409 Conflict`):
```json
{
  "success": false,
  "message": "Room is already booked for the selected dates",
  "error": "ROOM_UNAVAILABLE"
}
```

### Endpoints Summary

| Method | Endpoint | Description | Status Codes |
|---|---|---|---|
| `GET` | `/api/rooms` | Retrieve all rooms | `200` |
| `POST`| `/api/rooms` | Create a new hotel room | `201`, `400`, `409` |
| `GET` | `/api/rooms/<id>` | Retrieve specific room details | `200`, `404` |
| `PUT` | `/api/rooms/<id>` | Update room details | `200`, `400`, `404`, `409` |
| `DELETE` | `/api/rooms/<id>` | Delete room (blocked if active bookings exist) | `200`, `404`, `409` |
| `GET` | `/api/rooms/search?type=Deluxe` | Search rooms by room type | `200` |
| `GET` | `/api/rooms/available?check_in=YYYY-MM-DD&check_out=YYYY-MM-DD` | Dynamic availability lookup with optional `&type=Single` | `200`, `400` |
| `GET` | `/api/bookings` | List all bookings | `200` |
| `POST`| `/api/bookings` | Create booking with conflict check | `201`, `400`, `404`, `409` |
| `GET` | `/api/bookings/<id>` | Retrieve specific booking | `200`, `404` |
| `DELETE` | `/api/bookings/<id>` | Cancel active booking and release room | `200`, `400`, `404` |

---

## 💻 Installation & Setup (Windows)

### 1. Open PowerShell / Command Prompt and Navigate to the Directory
```powershell
cd d:\yugal\hotel-booking-system
```

### 2. (Optional) Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run the Application
```powershell
python app.py
```
Open your web browser and navigate to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

*Note: On first launch, the database table schema is automatically created and seeded with sample rooms and an initial booking for demonstration.*

---

## 🧪 Automated Testing

Execute the complete test suite with verbose output:

```powershell
pytest -v
```

### Test Suite Summary:
- **`tests/test_rooms.py`**:
  - `test_create_room_success`: Creates new room and checks field persistence.
  - `test_get_rooms`: Checks room listing.
  - `test_get_single_room` & `test_get_nonexistent_room`: Verifies ID retrieval and 404 responses.
  - `test_update_room`: Verifies updating room price and type.
  - `test_delete_room`: Verifies deletion and removal from DB.
  - `test_duplicate_room_number`: Rejects duplicate room numbers with 409 Conflict.
  - `test_invalid_price`: Rejects negative, zero, or non-numeric prices.
  - `test_search_rooms_by_type`: Filters rooms by type.
- **`tests/test_bookings.py`**:
  - `test_successful_booking`: Creates valid booking.
  - `test_overlapping_booking_scenarios`: Tests front overlap, back overlap, exact match, and encompassing dates (all return 409).
  - `test_adjacent_bookings_allowed`: Ensures back-to-back check-in/check-out dates are permitted.
  - `test_invalid_dates`: Checks same-day booking, inverted dates, and malformed date strings.
  - `test_nonexistent_room`: Verifies 404 response on unknown room ID.
  - `test_maintenance_room_cannot_be_booked`: Blocks booking for maintenance rooms.
  - `test_cancel_booking_and_frees_availability`: Cancels booking and immediately confirms dates are freed.
  - `test_delete_room_with_active_booking_rejected`: Protects rooms with active bookings from deletion.

---

## 🖼️ User Interface & Dashboard Overview

1. **Dashboard KPI Header**: Displays real-time counts for Total Rooms, Available Rooms, Booked Rooms, and Total Active Bookings.
2. **Availability Search Bar**: Form with date pickers (`Check-in`, `Check-out`) and room type filter. Queries live availability without reloading the page and displays interactive bookable cards.
3. **Room Inventory & Booking Tables**:
   - Status badges: `AVAILABLE` (green), `BOOKED` (amber), `MAINTENANCE` (gray), `CONFIRMED` (green), `CANCELLED` (red).
   - In-place action buttons: `✏️ Edit`, `🗑️ Delete`, `❌ Cancel Booking`, `⚡ Quick Book`.
   - Modals for creating and editing rooms without leaving the page.
   - Non-intrusive toast notifications for success and error messages.

---

## 🚀 Future Improvements

- User authentication and role-based access control (Admin vs. Front Desk Clerk vs. Guest).
- Payment gateway integration (Stripe / PayPal sandbox).
- Invoice PDF generation for confirmed bookings.
- Seasonal rate adjustments and dynamic weekend pricing.
#   M D M _ T A  
 