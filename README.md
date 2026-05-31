# 🏨 StayDesk — Hotel Management System

A full-stack hotel management web application built with **Python Flask** and **HTML/CSS/Jinja2 templates**, based on a relational database schema designed for real hotel operations.

---

## 📋 Project Overview

StayDesk is a hotel management dashboard that covers the complete lifecycle of hotel operations — from room inventory and guest bookings to invoicing and service tracking. The UI is a single-page Flask application with 8 fully functional screens, all rendered from one HTML template (`index.html`) using Jinja2 conditional blocks.

This project was built as part of a **DBMS course project** at SZABIST, designed around a normalized SQL Server database schema.

---

## 👥 Team Members

| Name | Student ID |
|---|---|
| Rohban Tariq | BSCS2412488 |
| Naushaba Asif | BSCS2412485 |
| Sohaib Rafiq | BSCS2412481 |
| Danish Danish | BSCS2412467 |

---

## 🗂️ Project Structure

```
hotel_app/
│
├── app.py                  ← Flask application (routes + mock data)
│
└── templates/
    └── index.html          ← Single HTML template (all 8 screens)
```

---

## 🖥️ Screens

| # | Screen | URL Route | Description |
|---|---|---|---|
| 1 | Dashboard | `/` | Room map, stats, quick actions, activity feed |
| 2 | Reservations | `/reservations` | Booking list, new booking form, booking detail |
| 3 | Room Management | `/rooms` | Room list, add/edit room, attributes, rates |
| 4 | Guests | `/guests` | Guest directory, profile, stay history, repeat business chart |
| 5 | Invoices | `/invoices` | Invoice list, bill breakdown, revenue vs potential chart |
| 6 | Rates | `/rates` | Rate matrix, seasonal pricing, facilities per rate type |
| 7 | Services | `/services` | Service categories, items list, add/edit form |
| 8 | Extras | `/extras` | Add-on items, usage stats, add/edit form |

---

## 🗄️ Database Schema (DDL)

The application is based on the following SQL Server tables. The mock data in `app.py` mirrors these field names exactly.

### Core Tables

```sql
-- Room types (Standard, Deluxe, Executive, Suite)
CREATE TABLE RoomType (
    room_type_id   INT PRIMARY KEY IDENTITY(1,1),
    type_name      VARCHAR(50)  NOT NULL,
    description    VARCHAR(255)
)

-- Occupancy types (Single, Twin, Double)
CREATE TABLE OccupancyType (
    occupancy_type_id INT PRIMARY KEY IDENTITY(1,1),
    name              VARCHAR(50) NOT NULL,
    min_guests        INT NOT NULL,
    max_guests        INT NOT NULL
)

-- Junction: which room types support which occupancy types
CREATE TABLE RoomOccupancy (
    room_type_id      INT NOT NULL REFERENCES RoomType,
    occupancy_type_id INT NOT NULL REFERENCES OccupancyType
)

-- Individual rooms
CREATE TABLE Room (
    room_id      INT PRIMARY KEY IDENTITY(1,1),
    room_number  INT NOT NULL,
    floor_number INT NOT NULL,
    room_type_id INT NOT NULL REFERENCES RoomType,
    status       VARCHAR(20) NOT NULL DEFAULT 'available'
)

-- Room attributes (Road facing, Pool side, Wheelchair, etc.)
CREATE TABLE RoomAttribute (
    attribute_id   INT PRIMARY KEY IDENTITY(1,1),
    attribute_name VARCHAR(100) NOT NULL
)

-- Junction: which rooms have which attributes
CREATE TABLE RoomAttributeMap (
    room_id      INT NOT NULL REFERENCES Room,
    attribute_id INT NOT NULL REFERENCES RoomAttribute
)
```

### Rates & Pricing

```sql
-- Rate types (Rack, Corporate, Friends & Family, Group, Government)
CREATE TABLE RateType (
    rate_type_id INT PRIMARY KEY IDENTITY(1,1),
    rate_name    VARCHAR(100) NOT NULL,
    description  VARCHAR(255)
)

-- Seasonal rates per room type + occupancy type + rate type
CREATE TABLE Rate (
    rate_id           INT PRIMARY KEY IDENTITY(1,1),
    rate_type_id      INT          NOT NULL REFERENCES RateType,
    room_type_id      INT          NOT NULL REFERENCES RoomType,
    occupancy_type_id INT          NOT NULL REFERENCES OccupancyType,
    start_date        DATE         NOT NULL,
    end_date          DATE         NOT NULL,
    amount            DECIMAL(10,2) NOT NULL
)

-- Facilities included in a rate type (Breakfast, Newspaper, Toiletries, etc.)
CREATE TABLE Facility (
    facility_id   INT PRIMARY KEY IDENTITY(1,1),
    facility_name VARCHAR(100) NOT NULL,
    description   VARCHAR(255)
)

-- Junction: which facilities are included in which rate types
CREATE TABLE RateFacility (
    rate_type_id INT NOT NULL REFERENCES RateType,
    facility_id  INT NOT NULL REFERENCES Facility
)
```

### Bookings & Guests

```sql
-- Customer records
CREATE TABLE Customer (
    customer_id INT PRIMARY KEY IDENTITY(1,1),
    first_name  VARCHAR(100) NOT NULL,
    last_name   VARCHAR(100) NOT NULL,
    email       VARCHAR(150) NOT NULL,
    phone       VARCHAR(20),
    id_type     VARCHAR(50),
    id_number   VARCHAR(50),
    created_at  DATE NOT NULL
)

-- Bookings (one customer, one or more rooms)
CREATE TABLE Booking (
    booking_id       INT PRIMARY KEY IDENTITY(1,1),
    customer_id      INT         NOT NULL REFERENCES Customer,
    planned_checkin  DATE        NOT NULL,
    planned_checkout DATE        NOT NULL,
    actual_checkin   DATE,
    actual_checkout  DATE,
    status           VARCHAR(20) NOT NULL DEFAULT 'booked',
    booking_source   VARCHAR(50) NOT NULL,
    created_at       DATETIME    NOT NULL
)

-- Each room assigned to a booking
CREATE TABLE BookingRoom (
    booking_room_id INT PRIMARY KEY IDENTITY(1,1),
    booking_id      INT NOT NULL REFERENCES Booking,
    room_id         INT NOT NULL REFERENCES Room,
    rate_id         INT NOT NULL REFERENCES Rate,
    num_guests      INT NOT NULL
)
```

### Extras, Services & Billing

```sql
-- Paid add-ons (Internet, Extra bed, Fruit basket, etc.)
CREATE TABLE Extra (
    extra_id   INT PRIMARY KEY IDENTITY(1,1),
    extra_name VARCHAR(100)  NOT NULL,
    price      DECIMAL(10,2) NOT NULL
)

-- Junction: extras added to a booking room
CREATE TABLE BookingRoomExtra (
    booking_room_id INT NOT NULL REFERENCES BookingRoom,
    extra_id        INT NOT NULL REFERENCES Extra,
    quantity        INT NOT NULL DEFAULT 1
)

-- Service categories (Room service, Laundry, Mini-bar, etc.)
CREATE TABLE ServiceCategory (
    category_id   INT PRIMARY KEY IDENTITY(1,1),
    category_name VARCHAR(100) NOT NULL
)

-- Individual service items with unit prices
CREATE TABLE ServiceItem (
    service_item_id INT PRIMARY KEY IDENTITY(1,1),
    category_id     INT          NOT NULL REFERENCES ServiceCategory,
    item_name       VARCHAR(100) NOT NULL,
    unit_price      DECIMAL(10,2) NOT NULL
)

-- Daily stay records (one row per room per night)
CREATE TABLE Stay (
    stay_id         INT PRIMARY KEY IDENTITY(1,1),
    booking_room_id INT          NOT NULL REFERENCES BookingRoom,
    stay_date       DATE         NOT NULL,
    room_charge     DECIMAL(10,2) NOT NULL
)

-- Services consumed during a stay
CREATE TABLE StayService (
    stay_service_id INT PRIMARY KEY IDENTITY(1,1),
    stay_id         INT          NOT NULL REFERENCES Stay,
    service_item_id INT          NOT NULL REFERENCES ServiceItem,
    quantity        INT          NOT NULL,
    unit_price      DECIMAL(10,2) NOT NULL,
    total_price     DECIMAL(10,2) NOT NULL,
    recorded_at     DATETIME     NOT NULL
)

-- Final invoice per booking
CREATE TABLE Invoice (
    invoice_id     INT PRIMARY KEY IDENTITY(1,1),
    booking_id     INT          NOT NULL REFERENCES Booking,
    issued_date    DATE         NOT NULL,
    subtotal       DECIMAL(10,2) NOT NULL,
    tax_amount     DECIMAL(10,2) NOT NULL DEFAULT 0,
    total_amount   DECIMAL(10,2) NOT NULL,
    paid_amount    DECIMAL(10,2) NOT NULL DEFAULT 0,
    payment_status VARCHAR(20)  NOT NULL DEFAULT 'unpaid'
)
```

---

## 🔗 Entity Relationships

```
RoomType ──< RoomOccupancy >── OccupancyType
RoomType ──< Room
Room     ──< RoomAttributeMap >── RoomAttribute

RateType ──< Rate >── RoomType
Rate     >── OccupancyType
RateType ──< RateFacility >── Facility

Customer ──< Booking
Booking  ──< BookingRoom >── Room
BookingRoom >── Rate
BookingRoom ──< BookingRoomExtra >── Extra
BookingRoom ──< Stay
Stay        ──< StayService >── ServiceItem
ServiceItem >── ServiceCategory

Booking ──< Invoice
```

---

## ⚙️ Installation & Setup

### Requirements

- Python 3.8+
- pip

### Step 1 — Clone or copy the project

```
hotel_app/
├── app.py
└── templates/
    └── index.html
```

### Step 2 — Install Flask

```bash
pip install flask
```

### Step 3 — Run the app

```bash
cd hotel_app
python app.py
```

### Step 4 — Open in browser

```
http://127.0.0.1:5000
```

---

## 🌐 All Routes

| Method | Route | Function | Description |
|---|---|---|---|
| GET | `/` | `dashboard` | Dashboard screen |
| GET | `/reservations` | `reservations` | Reservation list with filters |
| POST | `/reservations/add` | `add_booking` | Add new booking |
| GET | `/reservations/delete/<id>` | `delete_booking` | Delete a booking |
| GET | `/rooms` | `room_management` | Room list with filters |
| POST | `/rooms/add` | `add_room` | Add new room |
| GET | `/rooms/delete/<id>` | `delete_room` | Delete a room |
| GET | `/guests` | `guests` | Guest directory with search |
| POST | `/guests/add` | `add_guest` | Add new guest |
| GET | `/guests/delete/<id>` | `delete_guest` | Delete a guest |
| GET | `/invoices` | `invoices_view` | Invoice list with filters |
| GET | `/invoices/mark_paid/<id>` | `mark_paid` | Mark invoice as paid |
| GET | `/rates` | `rates_view` | Rate matrix screen |
| POST | `/rates/add` | `add_rate` | Add new rate |
| GET | `/rates/delete/<id>` | `delete_rate` | Delete a rate |
| GET | `/services` | `services` | Services screen |
| POST | `/services/add` | `add_service` | Add service item |
| GET | `/services/delete/<id>` | `delete_service` | Delete service item |
| GET | `/extras` | `extras_view` | Extras screen |
| POST | `/extras/add` | `add_extra` | Add new extra |
| GET | `/extras/delete/<id>` | `delete_extra` | Delete an extra |

---

## 📊 Key Reports Supported (From Project Brief)

| Report | Where in UI |
|---|---|
| Occupancy rate for different months/weeks/days | Dashboard → Donut chart + Room map |
| Actual revenue vs potential revenue for a date range | Invoices → Revenue bar chart |
| Bill of a customer for the whole stay | Invoices → Invoice detail panel |
| Percentage of repeat business month by month | Guests → Repeat business bar chart |
| List of room types and rates by date range and attributes | Rates → Rate matrix + Rooms screen |

---

## 📦 Data Volumes (From Project Brief)

| Table | Estimated Rows |
|---|---|
| Room | 50 |
| Stay | ~10,000 (50 rooms × 20 days × 2 years × 60% occupancy) |
| StayService | ~50,000 (5 items/day × 10,000 stay rows) |
| Rate | ~720 (4 room types × 2 occupancy × 5 rate types × 6 seasons × 3 years) |
| Customer | ~300–500 |
| Booking | ~500–1,000 |
| Invoice | ~500–1,000 |

---

## 🎨 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Frontend | HTML5, CSS3 (custom), Jinja2 |
| Icons | Tabler Icons (CDN) |
| Database (schema) | Microsoft SQL Server |
| Data (current) | Mock data in `app.py` (mirrors DDL) |

---

## 📝 Notes

- **Mock data** is used in place of a live database connection. All field names in `app.py` match the DDL column names exactly (`room_type_id`, `occupancy_type_id`, `booking_source`, `payment_status`, etc.)
- To connect to a real SQL Server database, replace the mock lists in `app.py` with `pyodbc` or `SQLAlchemy` queries
- All 8 screens are served from a single template `templates/index.html` using Jinja2 `{% if active == '...' %}` blocks
- Flash messages are used for add/delete confirmations

---

## 🔮 Future Enhancements

- Connect to live SQL Server database using `pyodbc`
- Add user authentication (login/logout for staff roles)
- Export invoices as PDF
- Add a calendar/timeline view for reservations
- Real-time room status updates
- Email notifications for bookings and checkouts

---

*StayDesk — DBMS Project, SZABIST 2026*
