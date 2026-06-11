# StayDesk — Hotel Management System

A full-stack hotel management web application built with **Python Flask**, **SQLAlchemy**, and **SQLite**, based on a normalized relational database schema for real hotel operations.

---

## Team Members

| Name | Gmail |
|---|---|
| Danish Talpur | danishshuja11@gmail.com |
| Naushaba Asif | asifnaushaba8@gmail.com |
| Rohban Tariq | bscs2412488@szabist.pk |
---

## Project Structure

```
├── app.py                  Flask app factory and blueprint registration
├── main.py                 Entry point: init DB + run server
├── database.py             SQLAlchemy instance
├── models/                 SQLAlchemy ORM models (synced with DBML schema)
├── routers/                Flask blueprints (routes per screen)
├── services/               Business logic helpers
├── templates/              Jinja2 HTML templates (one per screen)
├── database/
│   └── hotel_schema_updated.dbml   Database design reference
└── instance/
    └── hotel.db            SQLite database (created on first run)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask 3 |
| ORM | Flask-SQLAlchemy / SQLAlchemy 2 |
| Database | SQLite (`instance/hotel.db`) |
| Frontend | HTML5, CSS3, Jinja2 |
| Icons | Tabler Icons (CDN) |

---

## Installation & Setup

### Requirements

- Python 3.8+
- pip

### Step 1 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 2 — Run the application

**First run** (creates database + sample data):

```bash
python main.py
```

**Reset database** (drop all tables and re-seed):

```bash
python main.py --reset
```

### Step 3 — Open in browser

```
http://127.0.0.1:5000
```

You should see:

```
Initializing database with sample data...
Database initialized successfully with sample data!
```

If you see `Database already initialized`, either use `--reset` or delete `instance/hotel.db` manually.

---

## Screens

| # | Screen | URL | Description |
|---|---|---|---|
| 1 | Dashboard | `/` | Room map, stats, activity feed |
| 2 | Reservations | `/reservations` | Bookings, check-in/out, new reservation |
| 3 | Room Management | `/rooms` | Room list, add/edit, status |
| 4 | Guests | `/guests` | Guest directory, validation, stay history |
| 5 | Invoices | `/invoices` | Invoice list, receipt, payments |
| 6 | Rates | `/rates` | Rate matrix and seasonal pricing |
| 7 | Services | `/services` | Service categories and items |
| 8 | Extras | `/extras` | Hotel add-on items |

---

## Key Features

### Guest validation
- Email must end with `@gmail.com`
- Phone must be exactly 11 digits
- CNIC (when selected) must be exactly 13 digits

### Reservation flow
- Select a specific **available room** (not just room type)
- Rate plans filter automatically by the chosen room's type
- Check-out date must be after check-in date
- Optional booking extras saved to `booking_room_extra`
- Date overlap check prevents double-booking the same room

### Custom checkout
1. Click **Check-out** on a checked-in reservation
2. Review stay summary, booking extras, and service catalog
3. Select services used (optional — leave unchecked if none)
4. Confirm → generates `Stay`, `StayService`, `Invoice`, and snapshot rows

### Invoicing
- Invoice breakdown uses **snapshot tables** (`invoice_extra`, `invoice_service`)
- Payments recorded in the `payment` table
- 16% GST applied to subtotal
- Print receipt or download PDF from invoice detail page

---

## Viewing the Database (DB Browser for SQLite)

Use **DB Browser for SQLite** to show your teacher that UI actions write real data to the database.

### Setup

1. Download from [sqlitebrowser.org](https://sqlitebrowser.org/)
2. Run the app: `python main.py`
3. In DB Browser: **File → Open Database**
4. Select: `instance/hotel.db`
5. Open the **Browse Data** tab and pick a table

### Demo workflow

Keep DB Browser open beside the browser. After each UI action, click **Refresh** in DB Browser (or re-select the table).

| UI action | Tables to watch |
|---|---|
| Add guest | `customer` |
| New booking + extras | `booking`, `booking_room`, `booking_room_extra` |
| Check-in | `booking` (status, actual_checkin), `room` (status → occupied) |
| Checkout + services | `stay`, `stay_service`, `invoice`, `invoice_extra`, `invoice_service` |
| Record payment | `payment`, `invoice` (paid_amount, payment_status) |

### Useful SQL queries (Execute SQL tab)

```sql
-- All bookings with guest names
SELECT b.booking_id, c.first_name, c.last_name, b.status,
       b.planned_checkin, b.planned_checkout
FROM booking b
JOIN customer c ON b.customer_id = c.customer_id;

-- Invoice breakdown
SELECT invoice_id, room_total, service_total, extra_total,
       subtotal, tax_amount, total_amount, payment_status
FROM invoice;

-- Payment history
SELECT p.payment_id, p.invoice_id, p.amount, p.payment_method, p.payment_date
FROM payment p
ORDER BY p.payment_date DESC;
```

---

## Teacher Demo Script

### 1. Reset and start fresh

```bash
python main.py --reset
```

Open **http://127.0.0.1:5000** and DB Browser on `instance/hotel.db`.

### 2. Guest validation

Go to **Guests → Add New Guest Profile**:

| Test | Expected |
|---|---|
| Valid Gmail + 11-digit phone + 13-digit CNIC | Success |
| 10-digit phone | Error flash |
| `user@yahoo.com` | Error flash |
| CNIC with wrong length | Error flash |

Refresh `customer` table in DB Browser to show the new row.

### 3. Create a reservation

Go to **Reservations → New Booking Entry**:

- Pick customer, available room, matching rate plan
- Select check-in/check-out dates (check-out auto-adjusts)
- Check some extras → **Create Booking**

Verify rows in `booking`, `booking_room`, `booking_room_extra`.

### 4. Check-in and checkout

1. Click **Check-in** on the new booking
2. Click **Check-out** icon → checkout screen opens
3. Select services (e.g. Sandwich ×2, Coffee ×1) or leave all unchecked
4. **Confirm Checkout & Generate Invoice**
5. Review invoice receipt with room, extras, services, tax

Verify `stay`, `invoice`, `invoice_extra`, `invoice_service` in DB Browser.

### 5. Record payment

On the invoice detail page, click **Record Full Payment**.

Verify `payment` row and updated `invoice.payment_status = paid`.

---

## Database Schema Highlights

Core entities: `RoomType`, `Room`, `Customer`, `Booking`, `BookingRoom`, `Stay`, `StayService`, `Extra`, `BookingRoomExtra`, `Invoice`, `InvoiceExtra`, `InvoiceService`, `Payment`.

Full schema reference: `database/hotel_schema_updated.dbml`

---

## All Routes

| Method | Route | Description |
|---|---|---|
| GET | `/` | Dashboard |
| GET | `/reservations` | Reservation list |
| POST | `/reservations/add` | Create booking |
| POST | `/reservations/checkin/<id>` | Check in guest |
| GET | `/reservations/checkout/<id>` | Checkout screen |
| POST | `/reservations/checkout/<id>` | Process checkout + invoice |
| POST | `/reservations/delete/<id>` | Delete booking |
| GET | `/guests` | Guest directory |
| POST | `/guests/add` | Add guest |
| GET | `/invoices` | Invoice list |
| GET | `/invoices/<id>` | Invoice receipt |
| GET | `/invoices/mark_paid/<id>` | Record full payment |
| GET/POST | `/rooms`, `/rates`, `/services`, `/extras` | Management screens |

---

## Deploy on PythonAnywhere

### Step 1 — Upload the project

1. Log in at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Open the **Files** tab
3. Upload the project folder (or use **Git**):
   ```bash
   cd ~
   git clone YOUR_REPO_URL StayDesk
   ```
   Recommended folder: `/home/YOUR_USERNAME/StayDesk`

**Do not upload** the `venv/` folder — create a fresh virtualenv on PythonAnywhere.

### Step 2 — Create virtualenv and install packages

Open a **Bash** console:

```bash
cd ~/StayDesk
mkvirtualenv --python=/usr/bin/python3.10 staydesk-env
# If mkvirtualenv fails, use: python3.10 -m venv venv && source venv/bin/activate

pip install -r requirements.txt
```

### Step 3 — Initialize the database

Still in Bash:

```bash
cd ~/StayDesk
workon staydesk-env   # skip if you used source venv/bin/activate
python init_db.py --reset
```

This creates `instance/hotel.db` with sample data on the server.

### Step 4 — Configure the Web app

1. Go to the **Web** tab → **Add a new web app**
2. Choose **Manual configuration** → **Python 3.10**
3. Under **Virtualenv**, enter: `/home/YOUR_USERNAME/.virtualenvs/staydesk-env`
4. Click the **WSGI configuration file** link and replace its contents with:

```python
import sys

path = '/home/YOUR_USERNAME/StayDesk'
if path not in sys.path:
    sys.path.insert(0, path)

from wsgi import application
```

Replace `YOUR_USERNAME` with your PythonAnywhere username.

5. Save the file, then click **Reload** on the Web tab.

Your site will be live at:

```
https://YOUR_USERNAME.pythonanywhere.com
```

### Step 5 — After code updates

```bash
cd ~/StayDesk
workon staydesk-env
git pull   # if using git
# Reload web app from the Web tab
```

---

## Showing the Database (Live Demo)

### Best option — Live DB Viewer (built into the app)

Open **Live DB Viewer** in the sidebar (or go to `/database`).

1. Open **two browser tabs**:
   - Tab 1: `Guests` or `Reservations` (use the app normally)
   - Tab 2: **Live DB Viewer** (`/database`)
2. Enable **Auto-refresh (3s)** — table row counts update automatically
3. When you add a guest, the `customer` count increases within 3 seconds
4. Click any table to browse the latest 50 rows
5. Run **SELECT** queries in the query box (read-only, safe for demo)

Works on **localhost** and **PythonAnywhere** — no file download needed.

**Demo script for your teacher:**
1. Show `customer` table with current row count
2. Add a new guest in the other tab
3. Switch back — count increases, new row appears
4. Run: `SELECT COUNT(*) FROM customer`

### Option B — DB Browser for SQLite (offline file)

1. On PythonAnywhere **Files** tab, open `StayDesk/instance/hotel.db`
2. Click **Download**
3. Open the downloaded file in [DB Browser for SQLite](https://sqlitebrowser.org/)
4. Perform an action on the live website (add guest, book room, checkout)
5. **Download the file again** from PythonAnywhere and reopen it in DB Browser (or use **File → Revert All** after re-download)

| Website action | Table to watch |
|---|---|
| Add guest | `customer` |
| New booking | `booking`, `booking_room`, `booking_room_extra` |
| Check-in | `booking`, `room` |
| Checkout | `stay`, `invoice`, `invoice_extra`, `invoice_service` |
| Record payment | `payment`, `invoice` |

### Option B — PythonAnywhere Bash (live terminal demo)

While screen-sharing, run queries in Bash after each UI action:

```bash
cd ~/StayDesk
sqlite3 instance/hotel.db

.tables
SELECT customer_id, first_name, last_name, email FROM customer;
SELECT booking_id, status FROM booking;
SELECT invoice_id, total_amount, payment_status FROM invoice;
.quit
```

Run a `SELECT` before and after adding a guest — the new row appears immediately.


### One-line proof query (after adding a guest)

```sql
SELECT COUNT(*) AS total_guests FROM customer;
```

The count increases by 1 after each successful guest registration.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| PythonAnywhere import error | Fix `path` in WSGI file to `/home/YOUR_USERNAME/StayDesk` |
| PythonAnywhere 502 / error log | Check **Web → Error log**; run `pip install -r requirements.txt` in virtualenv |
| Database empty on PA | Run `python init_db.py --reset` in Bash |
| Old schema / missing columns | `python main.py --reset` or `python init_db.py --reset` |
| `AssertionError` with SQLAlchemy on Python 3.14 | Run `pip install "SQLAlchemy>=2.0.40"` |
| Port already in use | Stop other Flask process or change port in `main.py` |
| Empty room dropdown | Only `available` rooms show; check `room` table status |
| Cannot add guest | Use `@gmail.com`, 11-digit phone, 13-digit CNIC |

---

*StayDesk — DBMS Project, SZABIST 2026*
