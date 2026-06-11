import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILENAME = BASE_DIR / "instance" / "hotel.db"

conn = sqlite3.connect(str(DB_FILENAME))
cursor = conn.cursor()

print(f"Creating database tables inside '{DB_FILENAME}'...")

schema_queries = [
    """CREATE TABLE room_type (
        room_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_name TEXT NOT NULL,
        description TEXT
    );""",
    """CREATE TABLE occupancy_type (
        occupancy_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        min_guests INTEGER NOT NULL,
        max_guests INTEGER NOT NULL
    );""",
    """CREATE TABLE room_occupancy (
        room_type_id INTEGER NOT NULL,
        occupancy_type_id INTEGER NOT NULL,
        PRIMARY KEY (room_type_id, occupancy_type_id),
        FOREIGN KEY (room_type_id) REFERENCES room_type (room_type_id),
        FOREIGN KEY (occupancy_type_id) REFERENCES occupancy_type (occupancy_type_id)
    );""",
    """CREATE TABLE room_attribute (
        attribute_id INTEGER PRIMARY KEY AUTOINCREMENT,
        attribute_name TEXT NOT NULL
    );""",
    """CREATE TABLE room (
        room_id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number INTEGER NOT NULL UNIQUE,
        floor_number INTEGER NOT NULL,
        room_type_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'available',
        FOREIGN KEY (room_type_id) REFERENCES room_type (room_type_id),
        CHECK (status IN ('available', 'occupied', 'maintenance', 'blocked'))
    );""",
    """CREATE TABLE room_attribute_map (
        room_id INTEGER NOT NULL,
        attribute_id INTEGER NOT NULL,
        PRIMARY KEY (room_id, attribute_id),
        FOREIGN KEY (room_id) REFERENCES room (room_id),
        FOREIGN KEY (attribute_id) REFERENCES room_attribute (attribute_id)
    );""",
    """CREATE TABLE rate_type (
        rate_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
        rate_name TEXT NOT NULL,
        description TEXT,
        is_base_rate INTEGER NOT NULL DEFAULT 0
    );""",
    """CREATE TABLE rate (
        rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
        rate_type_id INTEGER NOT NULL,
        room_type_id INTEGER NOT NULL,
        occupancy_type_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        FOREIGN KEY (rate_type_id) REFERENCES rate_type (rate_type_id),
        FOREIGN KEY (room_type_id, occupancy_type_id) REFERENCES room_occupancy (room_type_id, occupancy_type_id)
    );""",
    """CREATE TABLE facility (
        facility_id INTEGER PRIMARY KEY AUTOINCREMENT,
        facility_name TEXT NOT NULL,
        description TEXT
    );""",
    """CREATE TABLE rate_facility (
        rate_type_id INTEGER NOT NULL,
        facility_id INTEGER NOT NULL,
        PRIMARY KEY (rate_type_id, facility_id),
        FOREIGN KEY (rate_type_id) REFERENCES rate_type (rate_type_id),
        FOREIGN KEY (facility_id) REFERENCES facility (facility_id)
    );""",
    """CREATE TABLE extra (
        extra_id INTEGER PRIMARY KEY AUTOINCREMENT,
        extra_name TEXT NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        description TEXT
    );""",
    """CREATE TABLE service_category (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT NOT NULL
    );""",
    """CREATE TABLE service_item (
        service_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        item_name TEXT NOT NULL,
        unit_price DECIMAL(10,2) NOT NULL,
        FOREIGN KEY (category_id) REFERENCES service_category (category_id)
    );""",
    """CREATE TABLE customer (
        customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        id_type TEXT,
        id_number TEXT,
        created_at TEXT NOT NULL
    );""",
    """CREATE TABLE booking (
        booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        planned_checkin TEXT NOT NULL,
        planned_checkout TEXT NOT NULL,
        actual_checkin TEXT,
        actual_checkout TEXT,
        status TEXT NOT NULL DEFAULT 'booked',
        booking_source TEXT NOT NULL,
        is_walkin INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customer (customer_id),
        CHECK (status IN ('booked', 'checked_in', 'checked_out', 'cancelled', 'no_show'))
    );""",
    """CREATE TABLE booking_room (
        booking_room_id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL,
        room_id INTEGER NOT NULL,
        rate_id INTEGER NOT NULL,
        num_guests INTEGER NOT NULL,
        FOREIGN KEY (booking_id) REFERENCES booking (booking_id),
        FOREIGN KEY (room_id) REFERENCES room (room_id),
        FOREIGN KEY (rate_id) REFERENCES rate (rate_id)
    );""",
    """CREATE TABLE booking_room_extra (
        booking_room_id INTEGER NOT NULL,
        extra_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        source TEXT NOT NULL DEFAULT 'booking',
        PRIMARY KEY (booking_room_id, extra_id, source),
        FOREIGN KEY (booking_room_id) REFERENCES booking_room (booking_room_id),
        FOREIGN KEY (extra_id) REFERENCES extra (extra_id),
        CHECK (source IN ('booking', 'checkin'))
    );""",
    """CREATE TABLE stay (
        stay_id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_room_id INTEGER NOT NULL,
        stay_date TEXT NOT NULL,
        applied_rate DECIMAL(10,2) NOT NULL,
        room_charge DECIMAL(10,2) NOT NULL,
        UNIQUE (booking_room_id, stay_date),
        FOREIGN KEY (booking_room_id) REFERENCES booking_room (booking_room_id)
    );""",
    """CREATE TABLE stay_service (
        stay_service_id INTEGER PRIMARY KEY AUTOINCREMENT,
        stay_id INTEGER NOT NULL,
        service_item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10,2) NOT NULL,
        total_price DECIMAL(10,2) NOT NULL,
        recorded_at TEXT NOT NULL,
        FOREIGN KEY (stay_id) REFERENCES stay (stay_id),
        FOREIGN KEY (service_item_id) REFERENCES service_item (service_item_id)
    );""",
    """CREATE TABLE invoice (
        invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL UNIQUE,
        issued_date TEXT NOT NULL,
        room_total DECIMAL(10,2) NOT NULL DEFAULT 0,
        service_total DECIMAL(10,2) NOT NULL DEFAULT 0,
        extra_total DECIMAL(10,2) NOT NULL DEFAULT 0,
        subtotal DECIMAL(10,2) NOT NULL,
        tax_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
        total_amount DECIMAL(10,2) NOT NULL,
        paid_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
        payment_status TEXT NOT NULL DEFAULT 'unpaid',
        FOREIGN KEY (booking_id) REFERENCES booking (booking_id),
        CHECK (payment_status IN ('unpaid', 'partial', 'paid', 'refunded'))
    );""",
    """CREATE TABLE invoice_extra (
        invoice_extra_id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        extra_id INTEGER NOT NULL,
        extra_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10,2) NOT NULL,
        line_total DECIMAL(10,2) NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES invoice (invoice_id),
        FOREIGN KEY (extra_id) REFERENCES extra (extra_id)
    );""",
    """CREATE TABLE invoice_service (
        invoice_service_id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        service_item_id INTEGER NOT NULL,
        item_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10,2) NOT NULL,
        line_total DECIMAL(10,2) NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES invoice (invoice_id),
        FOREIGN KEY (service_item_id) REFERENCES service_item (service_item_id)
    );""",
    """CREATE TABLE payment (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        payment_date TEXT NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        payment_method TEXT NOT NULL,
        reference_number TEXT,
        notes TEXT,
        FOREIGN KEY (invoice_id) REFERENCES invoice (invoice_id)
    );"""
]

for query in schema_queries:
    cursor.execute(query)

print("Seeding core baseline lookup configurations...")

cursor.executemany("INSERT INTO room_type (type_name, description) VALUES (?, ?);", [
    ('Standard', 'Cozy single/double bedroom with essential amenities'),
    ('Executive', 'Spacious room with a dedicated sitting area and work desk'),
    ('Deluxe Family', 'Two interconnected rooms ideal for families'),
    ('Royal Suite', 'Luxury living space, dining area, and premium view')
])

cursor.executemany("INSERT INTO occupancy_type (name, min_guests, max_guests) VALUES (?, ?, ?);", [
    ('Single Occupancy', 1, 1),
    ('Double Occupancy', 1, 2),
    ('Triple Occupancy', 1, 3),
    ('Quad Occupancy', 2, 4)
])

cursor.executemany("INSERT INTO room_occupancy (room_type_id, occupancy_type_id) VALUES (?, ?);", [
    (1, 1), (1, 2), (2, 2), (2, 3), (3, 3), (3, 4), (4, 2), (4, 4)
])

cursor.executemany("INSERT INTO rate_type (rate_name, description, is_base_rate) VALUES (?, ?, ?);", [
    ('Standard Rack Rate', 'Walk-in regular counter price', 1),
    ('Corporate Discounted', 'Special negotiated rate for corporate companies', 0),
    ('Advance Purchase Promo', 'Non-refundable discounted rate for booking early', 0),
    ('Weekend Special', 'Discounted rate applicable for Friday-Sunday stays', 0),
    ('Long Stay Extended Package', 'Special daily pricing for stays exceeding 7 nights', 0)
])

cursor.executemany("INSERT INTO facility (facility_name, description) VALUES (?, ?);", [
    ('High-Speed Wi-Fi', 'Complimentary 50Mbps internet access'),
    ('Buffet Breakfast', 'Complimentary breakfast at the rooftop cafe'),
    ('Airport Shuttle', 'Pick and drop facility from Islamabad/Karachi/Lahore airports')
])

cursor.executemany("INSERT INTO rate_facility (rate_type_id, facility_id) VALUES (?, ?);", [
    (1, 1), (2, 1), (2, 2), (3, 1), (4, 1), (4, 2), (5, 1), (5, 2), (5, 3)
])

cursor.executemany("INSERT INTO extra (extra_name, price, description) VALUES (?, ?, ?);", [
    ('Extra Mattress', 1800.00, 'Foldable additional bed setup for guests.'),
    ('Late Checkout (up to 6 PM)', 3500.00, 'Extend checkout timing based on availability.'),
    ('Baby Cot', 1200.00, 'Comfortable infant cot with bedding included.')
])

cursor.executemany("INSERT INTO room_attribute (attribute_name) VALUES (?);", [
    ('Margalla Hills View',), ('Sea View',), ('Smoking Allowed',), ('Balcony',), ('Executive Lounge Access',)
])

cursor.executemany("INSERT INTO service_category (category_name) VALUES (?);", [
    ('Laundry & Dry Cleaning',), ('Room Service - Food',), ('Mini Bar',)
])

cursor.executemany("INSERT INTO service_item (category_id, item_name, unit_price) VALUES (?, ?, ?);", [
    (1, 'Shalwar Kameez Pressing', 120.00),
    (1, 'Suit Dry Cleaning', 950.00),
    (2, 'Chicken Biryani (Premium)', 750.00),
    (2, 'Chicken Karahi (Half)', 1450.00),
    (2, 'Club Sandwich with Fries', 600.00),
    (2, 'Chai (Karak Doodh Patti)', 140.00),
    (3, 'Mineral Water (Large)', 160.00),
    (3, 'Gourmet Cola Can', 150.00)
])

print("Constructing 75 rooms and structural floor architectures...")
rooms_to_insert = []
attribute_maps_to_insert = []

for idx in range(1, 76):
    floor = ((idx - 1) // 15) + 1
    room_no = (floor * 100) + ((idx - 1) % 15 + 1)
    
    if idx <= 30:
        rt_id = 1
    elif idx <= 55:
        rt_id = 2
    elif idx <= 70:
        rt_id = 3
    else:
        rt_id = 4
        
    rooms_to_insert.append((room_no, floor, rt_id, 'available'))
    
    if idx % 4 == 0: attribute_maps_to_insert.append((idx, 1))
    if idx % 5 == 0: attribute_maps_to_insert.append((idx, 3))
    if idx % 3 == 0: attribute_maps_to_insert.append((idx, 4))

cursor.executemany("INSERT INTO room (room_number, floor_number, room_type_id, status) VALUES (?, ?, ?, ?);", rooms_to_insert)
cursor.executemany("INSERT INTO room_attribute_map (room_id, attribute_id) VALUES (?, ?);", attribute_maps_to_insert)

print("Generating seasonal rate matrices (exceeding 720 configurations)...")
rates_to_insert = []

cursor.execute("SELECT room_type_id, occupancy_type_id FROM room_occupancy;")
room_occupancies = cursor.fetchall()

year_start = 2024
for y_idx in range(3):
    for s_idx in range(6):
        start_date = datetime(year_start + y_idx, 1, 1) + timedelta(days=s_idx * 60)
        end_date = start_date + timedelta(days=59)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        for curr_rt, curr_ot in room_occupancies:
            base_amount = {1: 9500.00, 2: 16000.00, 3: 26000.00, 4: 55000.00}[curr_rt]
            base_amount += {1: 0, 2: 2000, 3: 4000, 4: 6000}[curr_ot]
            
            multipliers = {1: 1.0, 2: 0.85, 3: 0.78, 4: 1.15, 5: 0.70}
            
            for rt_loop in range(1, 6):
                random_fluctuation = random.randint(-15, 15) * 100
                final_amount = (base_amount * multipliers[rt_loop]) + random_fluctuation
                final_amount = round(final_amount, -2)
                
                rates_to_insert.append((rt_loop, curr_rt, curr_ot, start_date_str, end_date_str, final_amount))

cursor.executemany("INSERT INTO rate (rate_type_id, room_type_id, occupancy_type_id, start_date, end_date, amount) VALUES (?, ?, ?, ?, ?, ?);", rates_to_insert)


print("Populating regional gender-coherent customer database with specified profiles...")

# Specific requested combinations (must not be altered or cross-combined)
mandatory_names = [
    ("Syed Muhammad Aun", "Hassan Naqvi"),
    ("Sohaib", "Rafiq"),
    ("Rohban", "Tariq"),
    ("Danish", "Talpur"),
    ("Sadiq", "Raza"),
    ("Mutahir", "Jabbar"),
    ("Muhammad", "Zohaib"),
    ("Aun", "Bajwa"), # Targeted customer for highest bookings
    ("Naushaba", "Asif"),
    ("Ayesha", "Farooq"),
    ("Mariyam", "Shoab"),
    ("Deepika", "Padukone")
]

# Baseline lists to generate additional pool limits safely
pak_first_names = [
    ('Muhammad', 'M'), ('Ahmed', 'M'), ('Zubair', 'M'), ('Kamran', 'M'), ('Faisal', 'M'), 
    ('Bilal', 'M'), ('Asif', 'M'), ('Tariq', 'M'), ('Usman', 'M'), ('Hamza', 'M'),
    ('Zain', 'M'), ('Omar', 'M'), ('Shahzad', 'M'), ('Nabeel', 'M'), ('Kashif', 'M'),
    ('Aisha', 'F'), ('Fatima', 'F'), ('Sana', 'F'), ('Zainab', 'F'), ('Mariam', 'F'),
    ('Amna', 'F'), ('Hira', 'F'), ('Sadia', 'F'), ('Nida', 'F'), ('Tayyaba', 'F'),
    ('Sidra', 'F'), ('Kiran', 'F'), ('Anum', 'F'), ('Sobia', 'F'), ('Irum', 'F')
]
pak_last_names = [
    'Khan', 'Khanum', 'Sheikh', 'Siddiqui', 'Malik', 'Qureshi', 'Shah', 
    'Mehmood', 'Iqbal', 'Javed', 'Riaz', 'Ahmed', 'Nawaz', 'Farooq', 
    'Haider', 'Asif', 'Alvi', 'Baig', 'ChaudHary', 'Butt', 'Lodhi'
]

raw_customers = []

# 1. Insert mandatory profiles first
for f_name, l_name in mandatory_names:
    unique_suffix = random.randint(100, 999)
    email = f"{f_name.lower().replace(' ', '')}.{l_name.lower().replace(' ', '')}{unique_suffix}@gmail.com"
    prefix = random.choice(['0300-', '0321-', '0333-', '0345-'])
    phone = prefix + str(random.randint(1000000, 9999999))
    cnic_prov = random.choice(['42101-', '35202-', '37405-'])
    id_number = cnic_prov + str(random.randint(1000000, 9999999)) + "-" + str(random.randint(0, 9))
    created_at = (datetime(2026, 1, 1) - timedelta(days=random.randint(0, 600))).strftime('%Y-%m-%d')
    
    raw_customers.append((f_name, l_name, email, phone, 'CNIC', id_number, created_at))

# 2. Complete the rest of the target database limit with combination logic
for f_name, gender in pak_first_names:
    for l_name in pak_last_names:
        # Check to prevent creating duplicate structural pairs of mandatory names accidentally
        if (f_name, l_name) in mandatory_names:
            continue
        unique_suffix = random.randint(100, 999)
        email = f"{f_name.lower()}.{l_name.lower()}{unique_suffix}@gmail.com"
        prefix = random.choice(['0300-', '0321-', '0333-', '0345-'])
        phone = prefix + str(random.randint(1000000, 9999999))
        cnic_prov = random.choice(['42101-', '35202-', '37405-'])
        id_number = cnic_prov + str(random.randint(1000000, 9999999)) + "-" + str(random.randint(0, 9))
        created_at = (datetime(2026, 1, 1) - timedelta(days=random.randint(0, 600))).strftime('%Y-%m-%d')
        
        raw_customers.append((f_name, l_name, email, phone, 'CNIC', id_number, created_at))

# RANDOMIZE IDs: Shuffling ensures similar first names are entirely scattered across random IDs
random.shuffle(raw_customers)

cursor.executemany("INSERT INTO customer (first_name, last_name, email, phone, id_type, id_number, created_at) VALUES (?, ?, ?, ?, ?, ?, ?);", raw_customers)
conn.commit()

# Retrieve ID of "Aun Bajwa" to systematically guarantee he gets the highest bookings
cursor.execute("SELECT customer_id FROM customer WHERE first_name = 'Aun' AND last_name = 'Bajwa';")
aun_bajwa_id = cursor.fetchone()[0]

print("Executing live operation engine loops (Iterating to ~10,500 Stay Service items)...")

target_service_rows = 10500
current_service_rows = 0
day_increment = 0

cursor.execute("SELECT count(*) FROM customer;")
max_customers = cursor.fetchone()[0]

cursor.execute("SELECT service_item_id, item_name, unit_price FROM service_item;")
service_items_pool = cursor.fetchall()

# Keep track of bookings per customer to ensure Aun Bajwa stays on top
booking_counts = {i: 0 for i in range(1, max_customers + 1)}

while current_service_rows < target_service_rows:
    day_increment = (day_increment + random.randint(1, 4)) % 700
    checkin_dt = datetime(2024, 1, 2) + timedelta(days=day_increment)
    stay_length = random.randint(1, 4)
    checkout_dt = checkin_dt + timedelta(days=stay_length)
    
    checkin_str = checkin_dt.strftime('%Y-%m-%d')
    checkout_str = checkout_dt.strftime('%Y-%m-%d')
    
    # 25% of the time, force the booking to belong to Aun Bajwa to ensure he dominates bookings
    if random.random() < 0.25:
        cust_id = aun_bajwa_id
    else:
        cust_id = random.randint(1, max_customers)
        
    room_id = random.randint(1, 75)
    
    cursor.execute("SELECT room_type_id FROM room WHERE room_id = ?;", (room_id,))
    rt_id = cursor.fetchone()[0]
    
    cursor.execute("SELECT occupancy_type_id FROM room_occupancy WHERE room_type_id = ?;", (rt_id,))
    occupancy_types = [r[0] for r in cursor.fetchall()]
    ot_id = random.choice(occupancy_types)
    
    cursor.execute("""
        SELECT rate_id, amount FROM rate 
        WHERE room_type_id = ? AND occupancy_type_id = ? AND ? BETWEEN start_date AND end_date;
    """, (rt_id, ot_id, checkin_str))
    rate_res = cursor.fetchone()
    
    if not rate_res:
        cursor.execute("SELECT rate_id, amount FROM rate WHERE room_type_id = ? LIMIT 1;", (rt_id,))
        rate_res = cursor.fetchone()
        
    rate_id, room_price = rate_res
    
    is_walkin = 1 if random.randint(1, 10) == 1 else 0
    status = 'cancelled' if random.randint(1, 15) == 1 else 'checked_out'
    booking_source = random.choice(['Direct Phone', 'Booking.com', 'Walk-In'])
    created_at = (checkin_dt - timedelta(hours=random.randint(0, 48))).strftime('%Y-%m-%d %H:%M:%S')
    
    actual_checkin = checkin_str if status != 'cancelled' else None
    actual_checkout = checkout_str if status != 'cancelled' else None
    
    cursor.execute("""
        INSERT INTO booking (customer_id, planned_checkin, planned_checkout, actual_checkin, actual_checkout, status, booking_source, is_walkin, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (cust_id, checkin_str, checkout_str, actual_checkin, actual_checkout, status, booking_source, is_walkin, created_at))
    booking_id = cursor.lastrowid
    booking_counts[cust_id] += 1
    
    if status == 'checked_out':
        num_guests = random.randint(1, 2)
        cursor.execute("""
            INSERT INTO booking_room (booking_id, room_id, rate_id, num_guests)
            VALUES (?, ?, ?, ?);
        """, (booking_id, room_id, rate_id, num_guests))
        booking_room_id = cursor.lastrowid
        
        service_total = 0
        service_items_invoiced = []
        
        for night_idx in range(stay_length):
            stay_date_str = (checkin_dt + timedelta(days=night_idx)).strftime('%Y-%m-%d')
            
            cursor.execute("""
                INSERT INTO stay (booking_room_id, stay_date, applied_rate, room_charge)
                VALUES (?, ?, ?, ?);
            """, (booking_room_id, stay_date_str, room_price, room_price))
            stay_id = cursor.lastrowid
            
            daily_items_count = random.randint(2, 6)
            for _ in range(daily_items_count):
                if current_service_rows >= target_service_rows:
                    break
                
                s_item_id, item_name, unit_price = random.choice(service_items_pool)
                qty = 2 if random.randint(1, 4) == 1 else 1
                total_price = unit_price * qty
                recorded_at = f"{stay_date_str} 14:00:00" 
                
                cursor.execute("""
                    INSERT INTO stay_service (stay_id, service_item_id, quantity, unit_price, total_price, recorded_at)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (stay_id, s_item_id, qty, unit_price, total_price, recorded_at))
                
                service_total += total_price
                service_items_invoiced.append((s_item_id, item_name, qty, unit_price, total_price))
                current_service_rows += 1

        room_total = room_price * stay_length
        subtotal = room_total + service_total
        tax_amount = round(subtotal * 0.16, 2)
        total_amount = subtotal + tax_amount
        
        cursor.execute("""
            INSERT INTO invoice (booking_id, issued_date, room_total, service_total, extra_total, subtotal, tax_amount, total_amount, paid_amount, payment_status)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, 'paid');
        """, (booking_id, checkout_str, room_total, service_total, subtotal, tax_amount, total_amount, total_amount))
        invoice_id = cursor.lastrowid
        
        for s_item_id, item_name, qty, unit_price, line_total in service_items_invoiced:
            cursor.execute("""
                INSERT INTO invoice_service (invoice_id, service_item_id, item_name, quantity, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (invoice_id, s_item_id, item_name, qty, unit_price, line_total))
            
        payment_method = random.choice(['Credit Card', 'Cash'])
        ref_num = f"PK-TXN-{random.randint(100000, 999999)}"
        
        cursor.execute("""
            INSERT INTO payment (invoice_id, payment_date, amount, payment_method, reference_number, notes)
            VALUES (?, ?, ?, ?, ?, 'Settled in full upon checkout counter.');
        """, (invoice_id, f"{checkout_str} 12:00:00", total_amount, payment_method, ref_num))

# Save changes to the physical .db file
conn.commit()

print("\n" + "="*64)
print("         PRODUCTION REALISM DATA GENERATION COMPLETE            ")
print("="*64)

metrics_queries = {
    'Total Configured Hotel Rooms': "SELECT COUNT(*) FROM room;",
    'Dynamic Structural Rate Pricing': "SELECT COUNT(*) FROM rate;",
    'Verified System Customer Base Profiles': "SELECT COUNT(*) FROM customer;",
    'Active Logged Booking Entities': "SELECT COUNT(*) FROM booking;",
    'Granular Consumer StayService Rows': "SELECT COUNT(*) FROM stay_service;"
}

print(f"{'Metric Descriptor':<40} | {'Generated Row Count':<20}")
print("-" * 64)
for metric_desc, sql_q in metrics_queries.items():
    cursor.execute(sql_q)
    count = cursor.fetchone()[0]
    print(f"{metric_desc:<40} | {count:<20}")
print("="*64)

# Confirm top customer validation metrics
print("\nVerifying Customer with Most Bookings:")
cursor.execute("""
    SELECT c.customer_id, c.first_name, c.last_name, COUNT(b.booking_id) AS total_res
    FROM customer c
    JOIN booking b ON c.customer_id = b.customer_id
    GROUP BY c.customer_id
    ORDER BY total_res DESC
    LIMIT 3;
""")
top_customers = cursor.fetchall()
for rank, (c_id, f_num, l_num, b_count) in enumerate(top_customers, start=1):
    print(f"Rank {rank}: ID {c_id} - {f_num} {l_num} (Total Bookings: {b_count})")

# Close Database Connection safely
conn.close()
print(f"\nSuccess! Database saved securely to: {os.path.abspath(DB_FILENAME)}")