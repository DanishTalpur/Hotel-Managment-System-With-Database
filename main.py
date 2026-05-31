from app import create_app
from database import db
from models import (
    RoomType, OccupancyType, Room, RoomAttribute, RoomAttributeMap,
    RateType, Rate, Facility, RateFacility,
    Customer, Booking, BookingRoom,
    Extra, BookingRoomExtra,
    ServiceCategory, ServiceItem,
    Stay, StayService,
    Invoice
)
from datetime import datetime, date, timedelta
import os

app = create_app()

def init_database():
    """Initialize database with tables and sample data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if data already exists
        if RoomType.query.first() is not None:
            print("Database already initialized.")
            return
        
        print("Initializing database with sample data...")
        
        # === Room Types ===
        room_types = [
            RoomType(type_name='Standard', description='Basic room with essential amenities'),
            RoomType(type_name='Deluxe', description='Spacious room with premium amenities'),
            RoomType(type_name='Executive', description='Business-friendly room with work area'),
            RoomType(type_name='Suite', description='Luxury room with separate living area'),
        ]
        db.session.add_all(room_types)
        db.session.commit()
        
        # === Occupancy Types ===
        occupancy_types = [
            OccupancyType(name='Single', min_guests=1, max_guests=1),
            OccupancyType(name='Double', min_guests=1, max_guests=2),
            OccupancyType(name='Twin', min_guests=1, max_guests=2),
            OccupancyType(name='Family', min_guests=2, max_guests=4),
        ]
        db.session.add_all(occupancy_types)
        db.session.commit()
        
        # === Room Attributes ===
        attributes = [
            RoomAttribute(attribute_name='Sea View'),
            RoomAttribute(attribute_name='City View'),
            RoomAttribute(attribute_name='Balcony'),
            RoomAttribute(attribute_name='Wheelchair Accessible'),
            RoomAttribute(attribute_name='Smoking'),
            RoomAttribute(attribute_name='Non-Smoking'),
            RoomAttribute(attribute_name='King Bed'),
            RoomAttribute(attribute_name='Twin Beds'),
        ]
        db.session.add_all(attributes)
        db.session.commit()
        
        # === Rate Types ===
        rate_types = [
            RateType(rate_name='Rack', description='Standard published rate'),
            RateType(rate_name='Corporate', description='Discounted rate for corporate clients'),
            RateType(rate_name='Friends & Family', description='Special rate for friends and family'),
            RateType(rate_name='Group', description='Discounted rate for group bookings'),
            RateType(rate_name='Government', description='Special rate for government employees'),
        ]
        db.session.add_all(rate_types)
        db.session.commit()
        
        # === Facilities ===
        facilities = [
            Facility(facility_name='Breakfast', description='Complimentary breakfast'),
            Facility(facility_name='WiFi', description='Free high-speed internet'),
            Facility(facility_name='Newspaper', description='Daily newspaper'),
            Facility(facility_name='Toiletries', description='Premium toiletries'),
            Facility(facility_name='Mini Bar', description='Stocked mini bar'),
            Facility(facility_name='Gym Access', description='Complimentary gym access'),
        ]
        db.session.add_all(facilities)
        db.session.commit()
        
        # === Rate Facilities (which facilities are included in which rate types) ===
        rate_facilities = [
            RateFacility(rate_type_id=1, facility_id=2),  # Rack: WiFi
            RateFacility(rate_type_id=2, facility_id=1),  # Corporate: Breakfast, WiFi
            RateFacility(rate_type_id=2, facility_id=2),
            RateFacility(rate_type_id=3, facility_id=1),  # Friends & Family: Breakfast, WiFi, Toiletries
            RateFacility(rate_type_id=3, facility_id=2),
            RateFacility(rate_type_id=3, facility_id=4),
            RateFacility(rate_type_id=4, facility_id=1),  # Group: Breakfast, WiFi
            RateFacility(rate_type_id=4, facility_id=2),
            RateFacility(rate_type_id=5, facility_id=1),  # Government: Breakfast, WiFi, Newspaper
            RateFacility(rate_type_id=5, facility_id=2),
            RateFacility(rate_type_id=5, facility_id=3),
        ]
        db.session.add_all(rate_facilities)
        db.session.commit()
        
        # === Create Rooms (50 rooms as per spec) ===
        rooms = []
        room_numbers = [
            (1, '101'), (1, '102'), (1, '103'), (1, '104'), (1, '105'), (1, '106'),
            (1, '107'), (1, '108'), (1, '109'), (1, '110'),
            (2, '201'), (2, '202'), (2, '203'), (2, '204'), (2, '205'), (2, '206'),
            (2, '207'), (2, '208'), (2, '209'), (2, '210'),
            (3, '301'), (3, '302'), (3, '303'), (3, '304'), (3, '305'), (3, '306'),
            (3, '307'), (3, '308'), (3, '309'), (3, '310'),
            (4, '401'), (4, '402'), (4, '403'), (4, '404'), (4, '405'), (4, '406'),
            (4, '407'), (4, '408'), (4, '409'), (4, '410'),
            (5, '501'), (5, '502'), (5, '503'), (5, '504'), (5, '505'), (5, '506'),
            (5, '507'), (5, '508'), (5, '509'), (5, '510'),
        ]
        
        # Assign room types (mix of all types)
        room_type_ids = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3] * 5 + [4, 4, 4, 4, 4, 4, 4, 4, 4, 4]
        
        for i, (floor, number) in enumerate(room_numbers):
            status = 'available'
            if i % 10 == 0:
                status = 'occupied'
            elif i % 15 == 0:
                status = 'maintenance'
            elif i % 20 == 0:
                status = 'checkout'
            
            room = Room(
                room_number=number,
                floor_number=floor,
                room_type_id=room_type_ids[i % len(room_type_ids)],
                status=status
            )
            rooms.append(room)
            db.session.add(room)
        db.session.commit()
        
        # === Rates ===
        today = date.today()
        rates = [
            # Standard rates
            Rate(rate_type_id=1, room_type_id=1, occupancy_type_id=1, start_date=today - timedelta(days=30), end_date=today + timedelta(days=365), amount=5000),
            Rate(rate_type_id=1, room_type_id=1, occupancy_type_id=2, start_date=today - timedelta(days=30), end_date=today + timedelta(days=365), amount=7000),
            # Deluxe rates
            Rate(rate_type_id=1, room_type_id=2, occupancy_type_id=1, start_date=today - timedelta(days=30), end_date=today + timedelta(days=365), amount=8000),
            Rate(rate_type_id=1, room_type_id=2, occupancy_type_id=2, start_date=today - timedelta(days=30), end_date=today + timedelta(days=365), amount=10000),
            # Executive rates
            Rate(rate_type_id=1, room_type_id=3, occupancy_type_id=1, start_date=today - timedelta(days=30), end_date=today + timedelta(days=365), amount=12000),
            Rate(rate_type_id=1, room_type_id=3, occupancy_type_id=2, start_date=today - timedelta(days=30), end_date=today + timedelta(days=365), amount=15000),
            # Suite rates
            Rate(rate_type_id=1, room_type_id=4, occupancy_type_id=1, start_date=today - timedelta(days=30), end_date=today + timedelta(days=365), amount=20000),
            Rate(rate_type_id=1, room_type_id=4, occupancy_type_id=2, start_date=today - timedelta(days=30), end_date=today + timedelta(days=365), amount=25000),
            # Corporate rates (discounted)
            Rate(rate_type_id=2, room_type_id=1, occupancy_type_id=1, start_date=today - timedelta(days=30), end_date=today + timedelta(days=365), amount=4500),
            Rate(rate_type_id=2, room_type_id=2, occupancy_type_id=1, start_date=today - timedelta(days=30), end_date=today + timedelta(days=365), amount=7200),
            Rate(rate_type_id=2, room_type_id=3, occupancy_type_id=1, start_date=today - timedelta(days=30), end_date=today + timedelta(days=365), amount=10800),
            Rate(rate_type_id=2, room_type_id=4, occupancy_type_id=1, start_date=today - timedelta(days=30), end_date=today + timedelta(days=365), amount=18000),
        ]
        db.session.add_all(rates)
        db.session.commit()
        
        # === Customers ===
        customers = [
            Customer(first_name='Ahmed', last_name='Khan', email='ahmed.khan@email.com', phone='0300-1234567', id_type='CNIC', id_number='42101-1234567-1', created_at=date.today() - timedelta(days=60)),
            Customer(first_name='Fatima', last_name='Ali', email='fatima.ali@email.com', phone='0300-2345678', id_type='CNIC', id_number='42101-2345678-2', created_at=date.today() - timedelta(days=45)),
            Customer(first_name='Hassan', last_name='Raza', email='hassan.raza@email.com', phone='0300-3456789', id_type='Passport', id_number='AB1234567', created_at=date.today() - timedelta(days=30)),
            Customer(first_name='Ayesha', last_name='Malik', email='ayesha.malik@email.com', phone='0300-4567890', id_type='CNIC', id_number='42101-4567890-4', created_at=date.today() - timedelta(days=15)),
            Customer(first_name='Usman', last_name='Shah', email='usman.shah@email.com', phone='0300-5678901', id_type='CNIC', id_number='42101-5678901-5', created_at=date.today() - timedelta(days=10)),
            Customer(first_name='Sara', last_name='Ahmed', email='sara.ahmed@email.com', phone='0300-6789012', id_type='CNIC', id_number='42101-6789012-6', created_at=date.today() - timedelta(days=5)),
            Customer(first_name='Bilal', last_name='Hussain', email='bilal.hussain@email.com', phone='0300-7890123', id_type='Passport', id_number='CD9876543', created_at=date.today() - timedelta(days=90)),
            Customer(first_name='Maria', last_name='Joseph', email='maria.joseph@email.com', phone='0300-8901234', id_type='CNIC', id_number='42101-8901234-8', created_at=date.today() - timedelta(days=75)),
            Customer(first_name='Tariq', last_name='Mahmood', email='tariq.mahmood@email.com', phone='0300-9012345', id_type='CNIC', id_number='42101-9012345-9', created_at=date.today() - timedelta(days=120)),
            Customer(first_name='Nadia', last_name='Siddiqui', email='nadia.siddiqui@email.com', phone='0300-0123456', id_type='CNIC', id_number='42101-0123456-0', created_at=date.today() - timedelta(days=20)),
        ]
        db.session.add_all(customers)
        db.session.commit()
        
        # === Bookings ===
        bookings = [
            Booking(customer_id=1, planned_checkin=today - timedelta(days=5), planned_checkout=today + timedelta(days=2), actual_checkin=today - timedelta(days=5), status='checked_in', booking_source='Online', created_at=datetime.now() - timedelta(days=30)),
            Booking(customer_id=2, planned_checkin=today - timedelta(days=2), planned_checkout=today + timedelta(days=3), actual_checkin=today - timedelta(days=2), status='checked_in', booking_source='Direct', created_at=datetime.now() - timedelta(days=15)),
            Booking(customer_id=3, planned_checkin=today + timedelta(days=1), planned_checkout=today + timedelta(days=5), status='booked', booking_source='Corporate', created_at=datetime.now() - timedelta(days=10)),
            Booking(customer_id=4, planned_checkin=today + timedelta(days=3), planned_checkout=today + timedelta(days=7), status='booked', booking_source='Online', created_at=datetime.now() - timedelta(days=5)),
            Booking(customer_id=5, planned_checkin=today - timedelta(days=10), planned_checkout=today - timedelta(days=3), actual_checkin=today - timedelta(days=10), actual_checkout=today - timedelta(days=3), status='checked_out', booking_source='Walk-in', created_at=datetime.now() - timedelta(days=20)),
            Booking(customer_id=6, planned_checkin=today - timedelta(days=7), planned_checkout=today, actual_checkin=today - timedelta(days=7), status='checkout', booking_source='Online', created_at=datetime.now() - timedelta(days=14)),
            Booking(customer_id=7, planned_checkin=today + timedelta(days=5), planned_checkout=today + timedelta(days=10), status='booked', booking_source='Corporate', created_at=datetime.now() - timedelta(days=3)),
            Booking(customer_id=8, planned_checkin=today - timedelta(days=15), planned_checkout=today - timedelta(days=10), actual_checkin=today - timedelta(days=15), actual_checkout=today - timedelta(days=10), status='checked_out', booking_source='Direct', created_at=datetime.now() - timedelta(days=30)),
        ]
        db.session.add_all(bookings)
        db.session.commit()
        
        # === Booking Rooms ===
        booking_rooms = [
            BookingRoom(booking_id=1, room_id=1, rate_id=1, num_guests=1),
            BookingRoom(booking_id=2, room_id=11, rate_id=3, num_guests=2),
            BookingRoom(booking_id=3, room_id=21, rate_id=5, num_guests=1),
            BookingRoom(booking_id=4, room_id=31, rate_id=7, num_guests=2),
            BookingRoom(booking_id=5, room_id=41, rate_id=2, num_guests=1),
            BookingRoom(booking_id=6, room_id=2, rate_id=4, num_guests=2),
            BookingRoom(booking_id=7, room_id=12, rate_id=6, num_guests=1),
            BookingRoom(booking_id=8, room_id=22, rate_id=8, num_guests=2),
        ]
        db.session.add_all(booking_rooms)
        db.session.commit()
        
        # === Extras ===
        extras = [
            Extra(extra_name='Extra Bed', price=1500),
            Extra(extra_name='Airport Transfer', price=3000),
            Extra(extra_name='Late Checkout', price=2000),
            Extra(extra_name='Room Service', price=1000),
            Extra(extra_name='Spa Access', price=2500),
        ]
        db.session.add_all(extras)
        db.session.commit()
        
        # === Service Categories ===
        service_categories = [
            ServiceCategory(category_name='Room Service'),
            ServiceCategory(category_name='Laundry'),
            ServiceCategory(category_name='Mini Bar'),
            ServiceCategory(category_name='Restaurant'),
        ]
        db.session.add_all(service_categories)
        db.session.commit()
        
        # === Service Items ===
        service_items = [
            ServiceItem(category_id=1, item_name='Sandwich', unit_price=500),
            ServiceItem(category_id=1, item_name='Coffee', unit_price=200),
            ServiceItem(category_id=1, item_name='Tea', unit_price=150),
            ServiceItem(category_id=2, item_name='Shirt Laundry', unit_price=300),
            ServiceItem(category_id=2, item_name='Pants Press', unit_price=250),
            ServiceItem(category_id=3, item_name='Soft Drink', unit_price=200),
            ServiceItem(category_id=3, item_name='Water Bottle', unit_price=100),
            ServiceItem(category_id=4, item_name='Breakfast Buffet', unit_price=1500),
            ServiceItem(category_id=4, item_name='Dinner', unit_price=2500),
        ]
        db.session.add_all(service_items)
        db.session.commit()
        
        # === Stays (one row per night for each booking room) ===
        stays = []
        for br in booking_rooms:
            booking = Booking.query.get(br.booking_id)
            if booking.actual_checkin and booking.actual_checkout:
                current_date = booking.actual_checkin
                while current_date < booking.actual_checkout:
                    rate = Rate.query.get(br.rate_id)
                    stays.append(Stay(
                        booking_room_id=br.booking_room_id,
                        stay_date=current_date,
                        room_charge=rate.amount
                    ))
                    current_date += timedelta(days=1)
        db.session.add_all(stays)
        db.session.commit()
        
        # === Invoices ===
        invoices = []
        for booking in bookings:
            if booking.status in ['checked_out', 'checkout']:
                # Calculate total from stays
                total = 0
                for br in booking.booking_rooms:
                    for stay in br.stays:
                        total += stay.room_charge
                
                invoice = Invoice(
                    booking_id=booking.booking_id,
                    issued_date=booking.actual_checkout or date.today(),
                    subtotal=total,
                    tax_amount=total * 0.16,  # 16% tax
                    total_amount=total * 1.16,
                    paid_amount=total * 1.16 if booking.status == 'checked_out' else 0,
                    payment_status='paid' if booking.status == 'checked_out' else 'unpaid'
                )
                invoices.append(invoice)
        db.session.add_all(invoices)
        db.session.commit()
        
        print("Database initialized successfully with sample data!")
        print(f"  - {len(room_types)} room types")
        print(f"  - {len(occupancy_types)} occupancy types")
        print(f"  - {len(rooms)} rooms")
        print(f"  - {len(rate_types)} rate types")
        print(f"  - {len(rates)} rates")
        print(f"  - {len(customers)} customers")
        print(f"  - {len(bookings)} bookings")

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    init_database()
    app.run(debug=True)