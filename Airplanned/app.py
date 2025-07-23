# app.py - AirPlanned Flight Booking System
# Complete fixed version with car booking and hotel/car payment status functionality

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, time
import mysql.connector
from mysql.connector import Error
import json
import re
import os
from decimal import Decimal

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'airplanned-secret-key-change-in-production')

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Root23500238',
    'database': 'airplanned_db',
    'port': 3307,
    'charset': 'utf8mb4',
    'autocommit': True,
    'use_unicode': True,
    'connect_timeout': 10
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def convert_timedelta_to_time(td):
    """Convert timedelta to time object"""
    if td is None:
        return None
    if isinstance(td, time):
        return td
    if isinstance(td, timedelta):
        total_seconds = int(td.total_seconds())
        hours = (total_seconds // 3600) % 24
        minutes = (total_seconds % 3600) // 60
        return time(hours, minutes)
    if isinstance(td, str):
        try:
            time_parts = td.split(':')
            return time(int(time_parts[0]), int(time_parts[1]))
        except:
            return None
    return td

def decimal_to_float(value):
    """Convert Decimal to float for template operations"""
    if isinstance(value, Decimal):
        return float(value)
    return value

def process_hotels_data(hotels_raw):
    """Process hotels data to add calculated prices"""
    hotels = []
    for hotel in hotels_raw:
        hotel_dict = {
            'id': hotel[0],
            'name': hotel[1],
            'location': hotel[2],
            'star_rating': hotel[3] or 3,
            'amenities': hotel[4],
            'contact_info': hotel[5],
            'base_price': decimal_to_float(hotel[6]),
            'availability': hotel[7]
        }
        
        # Calculate room prices
        base_price = hotel_dict['base_price']
        hotel_dict['room_prices'] = {
            'standard': base_price,
            'deluxe': base_price * 1.3,
            'suite': base_price * 1.8,
            'penthouse': base_price * 2.5
        }
        
        hotels.append(hotel_dict)
    
    return hotels

def process_cars_data(cars_raw):
    """Process car rental data to add calculated prices"""
    cars = []
    for car in cars_raw:
        car_dict = {
            'id': car[0],
            'company_name': car[1],
            'location': car[2],
            'car_types': car[3],
            'availability': car[4],
            'contact_info': car[5],
            'base_price': decimal_to_float(car[6])
        }
        
        # Calculate car type prices
        base_price = car_dict['base_price']
        car_dict['car_prices'] = {
            'Economy': base_price,
            'Compact': base_price * 1.2,
            'Mid-size': base_price * 1.4,
            'SUV': base_price * 1.8,
            'Luxury': base_price * 2.5,
            'Van': base_price * 2.0
        }
        
        cars.append(car_dict)
    
    return cars

# Template filters for safe time/date formatting
@app.template_filter('format_time')
def format_time_filter(time_obj):
    """Template filter to safely format time objects"""
    if time_obj is None:
        return 'N/A'
    
    time_obj = convert_timedelta_to_time(time_obj)
    
    if isinstance(time_obj, str):
        return time_obj
    
    if hasattr(time_obj, 'strftime'):
        return time_obj.strftime('%H:%M')
    
    return str(time_obj)

@app.template_filter('format_date')
def format_date_filter(date_obj):
    """Template filter to safely format date objects"""
    if date_obj is None:
        return 'N/A'
    
    if isinstance(date_obj, str):
        return date_obj
    
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime('%B %d, %Y')
    
    return str(date_obj)

@app.template_filter('decimal_to_float')
def decimal_to_float_filter(value):
    """Template filter to convert Decimal to float"""
    return decimal_to_float(value)

@app.route('/')
def index():
    """Home page with flight search"""
    connection = get_db_connection()
    origins, destinations, flights = [], [], []
    
    if connection:
        try:
            cursor = connection.cursor()
            
            cursor.execute("""
                SELECT DISTINCT origin_country, origin_airport 
                FROM flights 
                WHERE available_seats > 0 AND departure_date >= CURDATE()
                ORDER BY origin_country
            """)
            origins = cursor.fetchall() or []
            
            cursor.execute("""
                SELECT DISTINCT destination_country, destination_airport 
                FROM flights 
                WHERE available_seats > 0 AND departure_date >= CURDATE()
                ORDER BY destination_country
            """)
            destinations = cursor.fetchall() or []
            
            cursor.execute("""
                SELECT flight_id, flight_number, origin_country, destination_country, 
                       origin_airport, destination_airport, departure_date, 
                       departure_time, arrival_time, aircraft_type, total_seats, 
                       available_seats, price, airline
                FROM flights 
                WHERE available_seats > 0 AND departure_date >= CURDATE()
                ORDER BY departure_date, departure_time
                LIMIT 12
            """)
            flights = cursor.fetchall() or []
            
        except Error as e:
            print(f"Database error in index: {e}")
            flash('Error loading flight data. Please try again.', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        flash('Database connection unavailable. Please try again later.', 'error')
    
    return render_template('index.html', 
                         origins=origins, 
                         destinations=destinations, 
                         flights=flights)

@app.route('/search_flights', methods=['GET', 'POST'])
def search_flights():
    """Search flights based on criteria with round trip support"""
    connection = get_db_connection()
    outbound_flights = []
    return_flights = []
    
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('index'))
    
    try:
        cursor = connection.cursor()
        
        if request.method == 'POST':
            origin = request.form.get('origin', '').strip()
            destination = request.form.get('destination', '').strip()
            departure_date = request.form.get('departure_date', '').strip()
            return_date = request.form.get('return_date', '').strip()
            trip_type = request.form.get('trip_type', 'one-way')
            min_price = request.form.get('min_price', '').strip()
            max_price = request.form.get('max_price', '').strip()
            passengers = request.form.get('passengers', '1')
            flight_class = request.form.get('class', 'economy')
            
            # Base query for outbound flights
            outbound_query = """
                SELECT flight_id, flight_number, origin_country, destination_country, 
                       origin_airport, destination_airport, departure_date, 
                       departure_time, arrival_time, aircraft_type, total_seats, 
                       available_seats, price, airline
                FROM flights 
                WHERE available_seats >= %s AND departure_date >= CURDATE()
            """
            outbound_params = [int(passengers)]
            
            if origin:
                outbound_query += " AND origin_country = %s"
                outbound_params.append(origin)
            if destination:
                outbound_query += " AND destination_country = %s"
                outbound_params.append(destination)
            if departure_date:
                outbound_query += " AND departure_date = %s"
                outbound_params.append(departure_date)
            if min_price:
                try:
                    outbound_query += " AND price >= %s"
                    outbound_params.append(float(min_price))
                except ValueError:
                    flash('Invalid minimum price format', 'error')
            if max_price:
                try:
                    outbound_query += " AND price <= %s"
                    outbound_params.append(float(max_price))
                except ValueError:
                    flash('Invalid maximum price format', 'error')
            
            outbound_query += " ORDER BY departure_date, departure_time"
            
            # Execute outbound flights query
            cursor.execute(outbound_query, outbound_params)
            outbound_flights = cursor.fetchall() or []
            
            # If round trip, search for return flights
            if trip_type == 'round-trip' and return_date and origin and destination:
                return_query = """
                    SELECT flight_id, flight_number, origin_country, destination_country, 
                           origin_airport, destination_airport, departure_date, 
                           departure_time, arrival_time, aircraft_type, total_seats, 
                           available_seats, price, airline
                    FROM flights 
                    WHERE available_seats >= %s AND departure_date = %s
                    AND origin_country = %s AND destination_country = %s
                """
                return_params = [int(passengers), return_date, destination, origin]
                
                if min_price:
                    try:
                        return_query += " AND price >= %s"
                        return_params.append(float(min_price))
                    except ValueError:
                        pass
                if max_price:
                    try:
                        return_query += " AND price <= %s"
                        return_params.append(float(max_price))
                    except ValueError:
                        pass
                
                return_query += " ORDER BY departure_date, departure_time"
                
                # Execute return flights query
                cursor.execute(return_query, return_params)
                return_flights = cursor.fetchall() or []
            
            if not outbound_flights:
                flash('No outbound flights found matching your criteria.', 'info')
            elif trip_type == 'round-trip' and not return_flights:
                flash('No return flights found for your selected date.', 'warning')
        
    except Error as e:
        print(f"Database error in search: {e}")
        flash('Error searching flights. Please try again.', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('search_results.html', 
                         outbound_flights=outbound_flights,
                         return_flights=return_flights,
                         trip_type=request.form.get('trip_type', 'one-way') if request.method == 'POST' else 'one-way',
                         search_params=request.form if request.method == 'POST' else {})

@app.route('/book/<int:flight_id>')
def book_flight(flight_id):
    """Flight booking page with round trip support"""
    if 'user_id' not in session:
        flash('Please log in to book a flight', 'error')
        return redirect(url_for('login'))
    
    # Get parameters from URL
    passengers = request.args.get('passengers', 1, type=int)
    flight_class = request.args.get('class', 'economy')
    trip_type = request.args.get('trip_type', 'one-way')
    return_date = request.args.get('return_date', '')
    return_flight_id = request.args.get('return_flight_id', '', type=int)
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('index'))
    
    try:
        cursor = connection.cursor()
        
        # Get outbound flight details
        cursor.execute("""
            SELECT flight_id, flight_number, origin_country, destination_country, 
                   origin_airport, destination_airport, departure_date, departure_time, 
                   arrival_time, aircraft_type, total_seats, available_seats, price, airline
            FROM flights 
            WHERE flight_id = %s AND available_seats >= %s
        """, (flight_id, passengers))
        
        outbound_flight = cursor.fetchone()
        if not outbound_flight:
            flash('Flight not found or insufficient seats available', 'error')
            return redirect(url_for('index'))
        
        return_flight = None
        if trip_type == 'round-trip' and return_flight_id:
            cursor.execute("""
                SELECT flight_id, flight_number, origin_country, destination_country, 
                       origin_airport, destination_airport, departure_date, departure_time, 
                       arrival_time, aircraft_type, total_seats, available_seats, price, airline
                FROM flights 
                WHERE flight_id = %s AND available_seats >= %s
            """, (return_flight_id, passengers))
            
            return_flight = cursor.fetchone()
        
        # Get booked seats for both flights
        cursor.execute("""
            SELECT seat_number 
            FROM flight_bookings 
            WHERE flight_id = %s AND booking_status = 'Confirmed'
        """, (flight_id,))
        outbound_booked_seats = [row[0] for row in cursor.fetchall()]
        
        return_booked_seats = []
        if return_flight:
            cursor.execute("""
                SELECT seat_number 
                FROM flight_bookings 
                WHERE flight_id = %s AND booking_status = 'Confirmed'
            """, (return_flight_id,))
            return_booked_seats = [row[0] for row in cursor.fetchall()]
        
    except Error as e:
        print(f"Database error in booking: {e}")
        flash('Error loading flight details', 'error')
        return redirect(url_for('index'))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('booking.html', 
                         outbound_flight=outbound_flight,
                         return_flight=return_flight,
                         outbound_booked_seats=outbound_booked_seats,
                         return_booked_seats=return_booked_seats,
                         passengers=passengers,
                         flight_class=flight_class,
                         trip_type=trip_type)

@app.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    """Process flight booking confirmation with round trip support"""
    if 'user_id' not in session:
        flash('Please log in to book a flight', 'error')
        return redirect(url_for('login'))
    
    # Check if this is a round trip booking
    outbound_flight_id = request.form.get('outbound_flight_id')
    return_flight_id = request.form.get('return_flight_id', '')
    trip_type = request.form.get('trip_type', 'one-way')
    
    # Handle both single flight and round trip bookings
    if not outbound_flight_id:
        # Legacy single flight booking
        flight_id = request.form.get('flight_id')
        selected_seats = request.form.get('selectedSeat', '').split(',')
        passenger_names = request.form.getlist('passenger_name')
        passenger_emails = request.form.getlist('passenger_email')
        passenger_phones = request.form.getlist('passenger_phone')
        
        # Handle single passenger case
        if not passenger_names:
            passenger_names = [request.form.get('passenger_name', '').strip()]
            passenger_emails = [request.form.get('passenger_email', '').strip()]
            passenger_phones = [request.form.get('passenger_phone', '').strip()]
        
        # Clean up seat numbers
        selected_seats = [seat.strip() for seat in selected_seats if seat.strip()]
        
        if not all([flight_id, selected_seats, passenger_names[0], passenger_emails[0], passenger_phones[0]]):
            flash('All fields are required', 'error')
            return redirect(url_for('book_flight', flight_id=flight_id))
        
        return process_single_flight_booking(flight_id, selected_seats, passenger_names, passenger_emails, passenger_phones)
    
    else:
        # Round trip booking
        outbound_seats = request.form.get('outbound_selectedSeats', '').split(',')
        return_seats = request.form.get('return_selectedSeats', '').split(',') if trip_type == 'round-trip' else []
        
        passenger_names = request.form.getlist('passenger_name')
        passenger_emails = request.form.getlist('passenger_email')
        passenger_phones = request.form.getlist('passenger_phone')
        
        # Clean up seat numbers
        outbound_seats = [seat.strip() for seat in outbound_seats if seat.strip()]
        return_seats = [seat.strip() for seat in return_seats if seat.strip()]
        
        if not all([outbound_flight_id, outbound_seats, passenger_names[0], passenger_emails[0], passenger_phones[0]]):
            flash('All fields are required', 'error')
            return redirect(url_for('book_flight', flight_id=outbound_flight_id))
        
        return process_round_trip_booking(outbound_flight_id, return_flight_id, trip_type, 
                                        outbound_seats, return_seats, passenger_names, 
                                        passenger_emails, passenger_phones)

def process_single_flight_booking(flight_id, selected_seats, passenger_names, passenger_emails, passenger_phones):
    """Process single flight booking"""
    if len(selected_seats) != len(passenger_names):
        flash('Number of seats must match number of passengers', 'error')
        return redirect(url_for('book_flight', flight_id=flight_id))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('book_flight', flight_id=flight_id))
    
    try:
        cursor = connection.cursor()
        
        # Get flight price
        cursor.execute("SELECT price FROM flights WHERE flight_id = %s", (flight_id,))
        flight_price_result = cursor.fetchone()
        
        if not flight_price_result:
            flash('Flight not found', 'error')
            return redirect(url_for('index'))
            
        flight_price = flight_price_result[0]
        booking_ids = []
        
        # Create booking for each passenger
        for i, (name, email, phone, seat) in enumerate(zip(passenger_names, passenger_emails, passenger_phones, selected_seats)):
            if not all([name.strip(), email.strip(), phone.strip(), seat.strip()]):
                continue
                
            # Check if seat is still available
            cursor.execute("""
                SELECT COUNT(*) 
                FROM flight_bookings 
                WHERE flight_id = %s AND seat_number = %s AND booking_status = 'Confirmed'
            """, (flight_id, seat))
            
            if cursor.fetchone()[0] > 0:
                flash(f'Seat {seat} is no longer available. Please choose another seat.', 'error')
                return redirect(url_for('book_flight', flight_id=flight_id))
            
            # Insert booking
            cursor.execute("""
                INSERT INTO flight_bookings 
                (user_id, flight_id, passenger_name, passenger_email, passenger_phone, 
                 seat_number, total_amount, booking_status, payment_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (session['user_id'], flight_id, name.strip(), email.strip(), 
                  phone.strip(), seat, flight_price, 'Confirmed', 'Pending'))
            
            booking_ids.append(cursor.lastrowid)
        
        # Update available seats
        cursor.execute("""
            UPDATE flights 
            SET available_seats = available_seats - %s 
            WHERE flight_id = %s
        """, (len(booking_ids), flight_id))
        
        connection.commit()
        
        if len(booking_ids) == 1:
            flash('Booking confirmed successfully. Please proceed to payment.', 'success')
            return redirect(url_for('payment', booking_id=booking_ids[0]))
        else:
            flash(f'{len(booking_ids)} bookings confirmed successfully. Please proceed to payment.', 'success')
            return redirect(url_for('payment', booking_id=booking_ids[0]))
        
    except Error as e:
        connection.rollback()
        print(f"Database error in single flight booking: {e}")
        flash('Booking failed. Please try again.', 'error')
        return redirect(url_for('book_flight', flight_id=flight_id))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def process_round_trip_booking(outbound_flight_id, return_flight_id, trip_type, outbound_seats, 
                             return_seats, passenger_names, passenger_emails, passenger_phones):
    """Process round trip booking"""
    if len(outbound_seats) != len(passenger_names):
        flash('Number of seats must match number of passengers', 'error')
        return redirect(url_for('book_flight', flight_id=outbound_flight_id))
    
    if trip_type == 'round-trip' and len(return_seats) != len(passenger_names):
        flash('Number of return seats must match number of passengers', 'error')
        return redirect(url_for('book_flight', flight_id=outbound_flight_id))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('book_flight', flight_id=outbound_flight_id))
    
    try:
        cursor = connection.cursor()
        
        # Get flight prices
        cursor.execute("SELECT price FROM flights WHERE flight_id = %s", (outbound_flight_id,))
        outbound_price_result = cursor.fetchone()
        
        if not outbound_price_result:
            flash('Outbound flight not found', 'error')
            return redirect(url_for('index'))
            
        outbound_price = outbound_price_result[0]
        return_price = 0
        
        if trip_type == 'round-trip' and return_flight_id:
            cursor.execute("SELECT price FROM flights WHERE flight_id = %s", (return_flight_id,))
            return_price_result = cursor.fetchone()
            if return_price_result:
                return_price = return_price_result[0]
        
        booking_ids = []
        
        # Create bookings for each passenger
        for i, (name, email, phone) in enumerate(zip(passenger_names, passenger_emails, passenger_phones)):
            if not all([name.strip(), email.strip(), phone.strip()]):
                continue
            
            # Book outbound flight
            outbound_seat = outbound_seats[i] if i < len(outbound_seats) else None
            if outbound_seat:
                # Check if seat is still available
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM flight_bookings 
                    WHERE flight_id = %s AND seat_number = %s AND booking_status = 'Confirmed'
                """, (outbound_flight_id, outbound_seat))
                
                if cursor.fetchone()[0] > 0:
                    flash(f'Outbound seat {outbound_seat} is no longer available.', 'error')
                    return redirect(url_for('book_flight', flight_id=outbound_flight_id))
                
                # Insert outbound booking
                total_amount = outbound_price + return_price if trip_type == 'round-trip' else outbound_price
                cursor.execute("""
                    INSERT INTO flight_bookings 
                    (user_id, flight_id, passenger_name, passenger_email, passenger_phone, 
                     seat_number, total_amount, booking_status, payment_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (session['user_id'], outbound_flight_id, name.strip(), email.strip(), 
                      phone.strip(), outbound_seat, total_amount, 'Confirmed', 'Pending'))
                
                booking_ids.append(cursor.lastrowid)
            
            # Book return flight if round trip
            if trip_type == 'round-trip' and return_flight_id and i < len(return_seats):
                return_seat = return_seats[i]
                if return_seat:
                    # Check if return seat is still available
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM flight_bookings 
                        WHERE flight_id = %s AND seat_number = %s AND booking_status = 'Confirmed'
                    """, (return_flight_id, return_seat))
                    
                    if cursor.fetchone()[0] > 0:
                        flash(f'Return seat {return_seat} is no longer available.', 'error')
                        return redirect(url_for('book_flight', flight_id=outbound_flight_id))
                    
                    # Insert return booking
                    cursor.execute("""
                        INSERT INTO flight_bookings 
                        (user_id, flight_id, passenger_name, passenger_email, passenger_phone, 
                         seat_number, total_amount, booking_status, payment_status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (session['user_id'], return_flight_id, name.strip(), email.strip(), 
                          phone.strip(), return_seat, 0, 'Confirmed', 'Pending'))  # Total amount already included in outbound
                    
                    booking_ids.append(cursor.lastrowid)
        
        # Update available seats
        cursor.execute("""
            UPDATE flights 
            SET available_seats = available_seats - %s 
            WHERE flight_id = %s
        """, (len(passenger_names), outbound_flight_id))
        
        if trip_type == 'round-trip' and return_flight_id:
            cursor.execute("""
                UPDATE flights 
                SET available_seats = available_seats - %s 
                WHERE flight_id = %s
            """, (len(passenger_names), return_flight_id))
        
        connection.commit()
        
        flash(f'{"Round trip" if trip_type == "round-trip" else "Flight"} booking confirmed successfully. Please proceed to payment.', 'success')
        return redirect(url_for('payment', booking_id=booking_ids[0]))
        
    except Error as e:
        connection.rollback()
        print(f"Database error in round trip booking: {e}")
        flash('Booking failed. Please try again.', 'error')
        return redirect(url_for('book_flight', flight_id=outbound_flight_id))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/payment/<int:booking_id>')
def payment(booking_id):
    """Payment page"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT b.booking_id, b.passenger_name, b.seat_number, 
                   f.flight_number, f.origin_country, f.destination_country,
                   f.departure_date, f.departure_time, b.total_amount
            FROM flight_bookings b
            JOIN flights f ON b.flight_id = f.flight_id
            WHERE b.booking_id = %s AND b.user_id = %s AND b.payment_status = 'Pending'
        """, (booking_id, session['user_id']))
        
        booking_data = cursor.fetchone()
        if not booking_data:
            flash('Booking not found or payment already completed', 'error')
            return redirect(url_for('dashboard'))
        
        booking = list(booking_data)
        
        # Convert time if needed
        if len(booking) > 7 and booking[7] is not None:
            booking[7] = convert_timedelta_to_time(booking[7])
        
    except Error as e:
        print(f"Database error in payment: {e}")
        flash('Error loading booking details', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('payment.html', booking=booking)
@app.route('/process_payment', methods=['POST'])
def process_payment():
    """Process payment"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    
    booking_id = request.form.get('booking_id')
    card_number = request.form.get('card_number', '').replace(' ', '')
    expiry_date = request.form.get('expiry_date', '').strip()
    cvv = request.form.get('cvv', '').strip()
    cardholder_name = request.form.get('cardholder_name', '').strip()
    
    if not all([booking_id, card_number, expiry_date, cvv, cardholder_name]):
        flash('All payment fields are required', 'error')
        return redirect(url_for('payment', booking_id=booking_id))
    
    if len(card_number) != 16 or not card_number.isdigit():
        flash('Card number must be 16 digits', 'error')
        return redirect(url_for('payment', booking_id=booking_id))
    
    if not re.match(r'^\d{2}/\d{2}$', expiry_date):
        flash('Expiry date must be in MM/YY format', 'error')
        return redirect(url_for('payment', booking_id=booking_id))

    
    if len(cvv) != 3 or not cvv.isdigit():
        flash('CVV must be 3 digits', 'error')
        return redirect(url_for('payment', booking_id=booking_id))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('payment', booking_id=booking_id))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE flight_bookings 
            SET payment_status = 'Paid', payment_date = %s
            WHERE booking_id = %s AND user_id = %s AND payment_status = 'Pending'
        """, (datetime.now().date(), booking_id, session['user_id']))
        
        if cursor.rowcount == 0:
            flash('Booking not found or payment already processed', 'error')
            return redirect(url_for('dashboard'))
        
        connection.commit()
        flash('Payment successful', 'success')
        return redirect(url_for('payment_success', booking_id=booking_id))
        
    except Error as e:
        connection.rollback()
        print(f"Database error in process_payment: {e}")
        flash('Payment processing failed. Please try again.', 'error')
        return redirect(url_for('payment', booking_id=booking_id))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/payment_success/<int:booking_id>')
def payment_success(booking_id):
    """Payment confirmation"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT b.booking_id, b.passenger_name, b.seat_number, b.booking_date,
                   f.flight_number, f.origin_country, f.destination_country,
                   f.origin_airport, f.destination_airport, f.departure_date, 
                   f.departure_time, f.arrival_time, b.total_amount
            FROM flight_bookings b
            JOIN flights f ON b.flight_id = f.flight_id
            WHERE b.booking_id = %s AND b.user_id = %s AND b.payment_status = 'Paid'
        """, (booking_id, session['user_id']))
        
        booking_data = cursor.fetchone()
        if not booking_data:
            flash('Booking not found', 'error')
            return redirect(url_for('dashboard'))
        
        booking = list(booking_data)
        
        # Convert times if needed
        if len(booking) > 10 and booking[10] is not None:
            booking[10] = convert_timedelta_to_time(booking[10])
        if len(booking) > 11 and booking[11] is not None:
            booking[11] = convert_timedelta_to_time(booking[11])
        
    except Error as e:
        print(f"Database error in payment_success: {e}")
        flash('Error loading booking details', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('payment_success.html', booking=booking)

# HOTEL BOOKING ROUTES
@app.route('/hotels', methods=['GET', 'POST'])
def hotels():
    """Hotel booking page with database data and search functionality"""
    connection = get_db_connection()
    hotels = []
    
    if connection:
        try:
            cursor = connection.cursor()
            
            if request.method == 'POST':
                # Handle hotel search
                location = request.form.get('location', '').strip()
                check_in = request.form.get('check_in', '').strip()
                check_out = request.form.get('check_out', '').strip()
                guests = request.form.get('guests', '1')
                room_type = request.form.get('room_type', '').strip()
                star_rating = request.form.get('star_rating', '').strip()
                min_price = request.form.get('min_price_hotel', '').strip()
                max_price = request.form.get('max_price_hotel', '').strip()
                
                query = """
                    SELECT hotel_id, hotel_name, location, star_rating, amenities, 
                           contact_info, price_per_night, availability
                    FROM hotels 
                    WHERE availability > 0
                """
                params = []
                
                if location:
                    query += " AND location LIKE %s"
                    params.append(f"%{location}%")
                
                if star_rating:
                    query += " AND star_rating >= %s"
                    params.append(int(star_rating))
                
                if min_price:
                    try:
                        query += " AND price_per_night >= %s"
                        params.append(float(min_price))
                    except ValueError:
                        flash('Invalid minimum price format', 'error')
                
                if max_price:
                    try:
                        query += " AND price_per_night <= %s"
                        params.append(float(max_price))
                    except ValueError:
                        flash('Invalid maximum price format', 'error')
                
                query += " ORDER BY star_rating DESC, price_per_night ASC LIMIT 20"
                
                cursor.execute(query, params)
                hotels_raw = cursor.fetchall() or []
                hotels = process_hotels_data(hotels_raw)
                
                if not hotels:
                    flash('No hotels found matching your criteria.', 'info')
            else:
                # Default hotel listing
                cursor.execute("""
                    SELECT hotel_id, hotel_name, location, star_rating, amenities, 
                           contact_info, price_per_night, availability
                    FROM hotels 
                    WHERE availability > 0
                    ORDER BY star_rating DESC, price_per_night ASC
                    LIMIT 12
                """)
                hotels_raw = cursor.fetchall() or []
                hotels = process_hotels_data(hotels_raw)
            
        except Error as e:
            print(f"Database error in hotels: {e}")
            flash('Error loading hotels. Please try again.', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        flash('Database connection unavailable. Please try again later.', 'error')
    
    return render_template('hotels.html', hotels=hotels)

@app.route('/book_hotel/<int:hotel_id>')
def book_hotel(hotel_id):
    """Hotel booking page"""
    if 'user_id' not in session:
        flash('Please log in to book a hotel', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('hotels'))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT hotel_id, hotel_name, location, star_rating, amenities, 
                   contact_info, price_per_night, availability
            FROM hotels 
            WHERE hotel_id = %s AND availability > 0
        """, (hotel_id,))
        
        hotel_data = cursor.fetchone()
        if not hotel_data:
            flash('Hotel not found or no longer available', 'error')
            return redirect(url_for('hotels'))
        
        # Convert hotel tuple to list and ensure price is float for template
        hotel = list(hotel_data)
        hotel[6] = decimal_to_float(hotel[6])  # Convert price_per_night to float
        
        # Add room pricing calculations
        base_price = hotel[6]
        room_prices = {
            'standard': base_price,
            'deluxe': base_price * 1.3,
            'suite': base_price * 1.8,
            'penthouse': base_price * 2.5
        }
        
    except Error as e:
        print(f"Database error in hotel booking: {e}")
        flash('Error loading hotel details', 'error')
        return redirect(url_for('hotels'))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('hotel_booking.html', hotel=hotel, room_prices=room_prices)

@app.route('/confirm_hotel_booking', methods=['POST'])
def confirm_hotel_booking():
    """Process hotel booking confirmation"""
    if 'user_id' not in session:
        flash('Please log in to book a hotel', 'error')
        return redirect(url_for('login'))
    
    hotel_id = request.form.get('hotel_id')
    check_in_date = request.form.get('check_in_date')
    check_out_date = request.form.get('check_out_date')
    room_type = request.form.get('room_type')
    guest_name = request.form.get('guest_name', '').strip()
    guest_email = request.form.get('guest_email', '').strip()
    guest_phone = request.form.get('guest_phone', '').strip()
    
    if not all([hotel_id, check_in_date, check_out_date, room_type, guest_name, guest_email, guest_phone]):
        flash('All fields are required', 'error')
        return redirect(url_for('book_hotel', hotel_id=hotel_id))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('book_hotel', hotel_id=hotel_id))
    
    try:
        cursor = connection.cursor()
        
        # Get hotel price
        cursor.execute("SELECT price_per_night FROM hotels WHERE hotel_id = %s", (hotel_id,))
        hotel_price_result = cursor.fetchone()
        
        if not hotel_price_result:
            flash('Hotel not found', 'error')
            return redirect(url_for('hotels'))
            
        base_price = decimal_to_float(hotel_price_result[0])
        
        # Calculate total price based on room type
        room_multipliers = {
            'standard': 1.0,
            'deluxe': 1.3,
            'suite': 1.8,
            'penthouse': 2.5
        }
        
        nights = (datetime.strptime(check_out_date, '%Y-%m-%d') - datetime.strptime(check_in_date, '%Y-%m-%d')).days
        total_amount = base_price * room_multipliers.get(room_type, 1.0) * nights
        
        # Insert hotel booking with payment status
        cursor.execute("""
            INSERT INTO hotel_bookings 
            (user_id, hotel_id, check_in_date, check_out_date, room_type,
             guest_name, guest_email, guest_phone, booking_date, total_amount,
             payment_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (session['user_id'], hotel_id, check_in_date, check_out_date, room_type,
              guest_name, guest_email, guest_phone, datetime.now().date(), total_amount, 'Pending'))
        
        booking_id = cursor.lastrowid
        
        # Update hotel availability
        cursor.execute("""
            UPDATE hotels 
            SET availability = availability - 1 
            WHERE hotel_id = %s
        """, (hotel_id,))
        
        connection.commit()
        flash('Hotel booking confirmed successfully! Please proceed to payment.', 'success')
        return redirect(url_for('hotel_payment', booking_id=booking_id))
        
    except Error as e:
        connection.rollback()
        print(f"Database error in confirm_hotel_booking: {e}")
        flash('Hotel booking failed. Please try again.', 'error')
        return redirect(url_for('book_hotel', hotel_id=hotel_id))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/hotel_payment/<int:booking_id>')
def hotel_payment(booking_id):
    """Hotel payment page"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT hb.booking_id, hb.guest_name, hb.room_type, 
                   h.hotel_name, h.location, hb.check_in_date, 
                   hb.check_out_date, hb.total_amount, hb.payment_status
            FROM hotel_bookings hb
            JOIN hotels h ON hb.hotel_id = h.hotel_id
            WHERE hb.booking_id = %s AND hb.user_id = %s AND hb.payment_status = 'Pending'
        """, (booking_id, session['user_id']))
        
        booking_data = cursor.fetchone()
        if not booking_data:
            flash('Booking not found or payment already completed', 'error')
            return redirect(url_for('dashboard'))
        
        booking = list(booking_data)
        
    except Error as e:
        print(f"Database error in hotel_payment: {e}")
        flash('Error loading booking details', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('hotel_payment.html', booking=booking)

@app.route('/process_hotel_payment', methods=['POST'])
def process_hotel_payment():
    """Process hotel payment"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    
    booking_id = request.form.get('booking_id')
    card_number = request.form.get('card_number', '').replace(' ', '')
    expiry_date = request.form.get('expiry_date', '').strip()
    cvv = request.form.get('cvv', '').strip()
    cardholder_name = request.form.get('cardholder_name', '').strip()
    
    if not all([booking_id, card_number, expiry_date, cvv, cardholder_name]):
        flash('All payment fields are required', 'error')
        return redirect(url_for('hotel_payment', booking_id=booking_id))
    
    if len(card_number) != 16 or not card_number.isdigit():
        flash('Card number must be 16 digits', 'error')
        return redirect(url_for('hotel_payment', booking_id=booking_id))
    
    if not re.match(r'^\d{2}/\d{2}$', expiry_date):
        flash('Expiry date must be in MM/YY format', 'error')
        return redirect(url_for('hotel_payment', booking_id=booking_id))

    
    if len(cvv) != 3 or not cvv.isdigit():
        flash('CVV must be 3 digits', 'error')
        return redirect(url_for('hotel_payment', booking_id=booking_id))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('hotel_payment', booking_id=booking_id))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE hotel_bookings 
            SET payment_status = 'Paid'
            WHERE booking_id = %s AND user_id = %s AND payment_status = 'Pending'
        """, (booking_id, session['user_id']))
        
        if cursor.rowcount == 0:
            flash('Booking not found or payment already processed', 'error')
            return redirect(url_for('dashboard'))
        
        connection.commit()
        flash('Hotel payment successful', 'success')
        return redirect(url_for('dashboard'))
        
    except Error as e:
        connection.rollback()
        print(f"Database error in process_hotel_payment: {e}")
        flash('Payment processing failed. Please try again.', 'error')
        return redirect(url_for('hotel_payment', booking_id=booking_id))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# CAR RENTAL ROUTES
@app.route('/cars', methods=['GET', 'POST'])
def cars():
    """Car rental page with database data and search functionality"""
    connection = get_db_connection()
    car_rentals = []
    
    if connection:
        try:
            cursor = connection.cursor()
            
            if request.method == 'POST':
                # Handle car search
                pickup_location = request.form.get('pickup_location', '').strip()
                pickup_date = request.form.get('pickup_date', '').strip()
                pickup_time = request.form.get('pickup_time', '').strip()
                return_date = request.form.get('return_date', '').strip()
                return_time = request.form.get('return_time', '').strip()
                car_type = request.form.get('car_type', '').strip()
                transmission = request.form.get('transmission', '').strip()
                fuel_type = request.form.get('fuel_type', '').strip()
                
                query = """
                    SELECT rental_id, company_name, location, car_types, availability, 
                           contact_info, price_per_day
                    FROM car_rentals 
                    WHERE availability > 0
                """
                params = []
                
                if pickup_location:
                    query += " AND location LIKE %s"
                    params.append(f"%{pickup_location}%")
                
                if car_type:
                    query += " AND car_types LIKE %s"
                    params.append(f"%{car_type}%")
                
                query += " ORDER BY price_per_day ASC LIMIT 20"
                
                cursor.execute(query, params)
                cars_raw = cursor.fetchall() or []
                car_rentals = process_cars_data(cars_raw)
                
                if not car_rentals:
                    flash('No car rentals found matching your criteria.', 'info')
            else:
                # Default car rental listing
                cursor.execute("""
                    SELECT rental_id, company_name, location, car_types, availability, 
                           contact_info, price_per_day
                    FROM car_rentals 
                    WHERE availability > 0
                    ORDER BY price_per_day ASC
                    LIMIT 12
                """)
                cars_raw = cursor.fetchall() or []
                car_rentals = process_cars_data(cars_raw)
            
        except Error as e:
            print(f"Database error in cars: {e}")
            flash('Error loading car rentals. Please try again.', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        flash('Database connection unavailable. Please try again later.', 'error')
    
    return render_template('cars.html', car_rentals=car_rentals)

@app.route('/book_car/<int:rental_id>')
def book_car(rental_id):
    """Car rental booking page"""
    if 'user_id' not in session:
        flash('Please log in to book a car', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('cars'))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT rental_id, company_name, location, car_types, availability, 
                   contact_info, price_per_day
            FROM car_rentals 
            WHERE rental_id = %s AND availability > 0
        """, (rental_id,))
        
        rental_data = cursor.fetchone()
        if not rental_data:
            flash('Car rental not found or no longer available', 'error')
            return redirect(url_for('cars'))
        
        # Process rental data
        rentals_processed = process_cars_data([rental_data])
        rental = rentals_processed[0] if rentals_processed else None
        
        if not rental:
            flash('Error processing rental data', 'error')
            return redirect(url_for('cars'))
        
    except Error as e:
        print(f"Database error in car booking: {e}")
        flash('Error loading car rental details', 'error')
        return redirect(url_for('cars'))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('car_booking.html', rental=rental)

@app.route('/confirm_car_booking', methods=['POST'])
def confirm_car_booking():
    """Process car rental booking confirmation"""
    if 'user_id' not in session:
        flash('Please log in to book a car', 'error')
        return redirect(url_for('login'))
    
    rental_id = request.form.get('rental_id')
    pickup_date = request.form.get('pickup_date')
    return_date = request.form.get('return_date')
    car_type = request.form.get('car_type')
    renter_name = request.form.get('renter_name', '').strip()
    renter_email = request.form.get('renter_email', '').strip()
    renter_phone = request.form.get('renter_phone', '').strip()
    
    if not all([rental_id, pickup_date, return_date, car_type, renter_name, renter_email, renter_phone]):
        flash('All fields are required', 'error')
        return redirect(url_for('book_car', rental_id=rental_id))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('book_car', rental_id=rental_id))
    
    try:
        cursor = connection.cursor()
        
        # Get rental price
        cursor.execute("SELECT price_per_day FROM car_rentals WHERE rental_id = %s", (rental_id,))
        rental_price_result = cursor.fetchone()
        
        if not rental_price_result:
            flash('Car rental not found', 'error')
            return redirect(url_for('cars'))
            
        base_price = decimal_to_float(rental_price_result[0])
        
        # Calculate total price based on car type
        car_multipliers = {
            'Economy': 1.0,
            'Compact': 1.2,
            'Mid-size': 1.4,
            'SUV': 1.8,
            'Luxury': 2.5,
            'Van': 2.0
        }
        
        days = (datetime.strptime(return_date, '%Y-%m-%d') - datetime.strptime(pickup_date, '%Y-%m-%d')).days
        total_amount = base_price * car_multipliers.get(car_type, 1.0) * days
        
        # Insert car booking with payment status
        cursor.execute("""
            INSERT INTO car_bookings 
            (user_id, rental_id, pickup_date, return_date, car_type,
             renter_name, renter_email, renter_phone, booking_date, total_amount,
             payment_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (session['user_id'], rental_id, pickup_date, return_date, car_type,
              renter_name, renter_email, renter_phone, datetime.now().date(), total_amount, 'Pending'))
        
        booking_id = cursor.lastrowid
        
        # Update car availability
        cursor.execute("""
            UPDATE car_rentals 
            SET availability = availability - 1 
            WHERE rental_id = %s
        """, (rental_id,))
        
        connection.commit()
        flash('Car rental booking confirmed successfully! Please proceed to payment.', 'success')
        return redirect(url_for('car_payment', booking_id=booking_id))
        
    except Error as e:
        connection.rollback()
        print(f"Database error in confirm_car_booking: {e}")
        flash('Car rental booking failed. Please try again.', 'error')
        return redirect(url_for('book_car', rental_id=rental_id))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/car_payment/<int:booking_id>')
def car_payment(booking_id):
    """Car payment page"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT cb.booking_id, cb.renter_name, cb.car_type, 
                   cr.company_name, cr.location, cb.pickup_date, 
                   cb.return_date, cb.total_amount, cb.payment_status
            FROM car_bookings cb
            JOIN car_rentals cr ON cb.rental_id = cr.rental_id
            WHERE cb.booking_id = %s AND cb.user_id = %s AND cb.payment_status = 'Pending'
        """, (booking_id, session['user_id']))
        
        booking_data = cursor.fetchone()
        if not booking_data:
            flash('Booking not found or payment already completed', 'error')
            return redirect(url_for('dashboard'))
        
        booking = list(booking_data)
        
    except Error as e:
        print(f"Database error in car_payment: {e}")
        flash('Error loading booking details', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('car_payment.html', booking=booking)

@app.route('/process_car_payment', methods=['POST'])
def process_car_payment():
    """Process car payment"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    
    booking_id = request.form.get('booking_id')
    card_number = request.form.get('card_number', '').replace(' ', '')
    expiry_date = request.form.get('expiry_date', '').strip()
    cvv = request.form.get('cvv', '').strip()
    cardholder_name = request.form.get('cardholder_name', '').strip()
    
    if not all([booking_id, card_number, expiry_date, cvv, cardholder_name]):
        flash('All payment fields are required', 'error')
        return redirect(url_for('car_payment', booking_id=booking_id))
    
    if len(card_number) != 16 or not card_number.isdigit():
        flash('Card number must be 16 digits', 'error')
        return redirect(url_for('car_payment', booking_id=booking_id))
    
    if not re.match(r'^\d{2}/\d{2}', expiry_date):
        flash('Expiry date must be in MM/YY format', 'error')
        return redirect(url_for('car_payment', booking_id=booking_id))
    
    if len(cvv) != 3 or not cvv.isdigit():
        flash('CVV must be 3 digits', 'error')
        return redirect(url_for('car_payment', booking_id=booking_id))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('car_payment', booking_id=booking_id))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE car_bookings 
            SET payment_status = 'Paid'
            WHERE booking_id = %s AND user_id = %s AND payment_status = 'Pending'
        """, (booking_id, session['user_id']))
        
        if cursor.rowcount == 0:
            flash('Booking not found or payment already processed', 'error')
            return redirect(url_for('dashboard'))
        
        connection.commit()
        flash('Car rental payment successful', 'success')
        return redirect(url_for('dashboard'))
        
    except Error as e:
        connection.rollback()
        print(f"Database error in process_car_payment: {e}")
        flash('Payment processing failed. Please try again.', 'error')
        return redirect(url_for('car_payment', booking_id=booking_id))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# USER AUTHENTICATION ROUTES
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('login.html')
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'error')
            return render_template('login.html')
        
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT user_id, password, first_name, last_name 
                FROM users 
                WHERE email = %s
            """, (email,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user[1], password):
                session['user_id'] = user[0]
                session['user_name'] = f"{user[2]} {user[3]}"
                flash(f'Welcome back, {user[2]}', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password', 'error')
                
        except Error as e:
            print(f"Database error in login: {e}")
            flash('Login failed. Please try again.', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not all([full_name, email, password, confirm_password]):
            flash('All fields are required', 'error')
            return render_template('signup.html')

        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            flash('Please enter a valid email address', 'error')
            return render_template('signup.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('signup.html')
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'error')
            return render_template('signup.html')
        
        try:
            cursor = connection.cursor()
            
            cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Email already registered. Please use a different email.', 'error')
                return render_template('signup.html')
            
            # Split full name into first and last name
            name_parts = full_name.strip().split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            password_hash = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO users (first_name, last_name, email, password)
                VALUES (%s, %s, %s, %s)
            """, (first_name, last_name, email, password_hash))
            
            connection.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Error as e:
            connection.rollback()
            print(f"Database error in signup: {e}")
            flash('Registration failed. Please try again.', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """User logout"""
    user_name = session.get('user_name', 'User')
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """User dashboard with flight, hotel, and car bookings"""
    if 'user_id' not in session:
        flash('Please log in to view your dashboard', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    flight_bookings = []
    hotel_bookings = []
    car_bookings = []
    
    if connection:
        try:
            cursor = connection.cursor()
            
            # Get flight bookings
            cursor.execute("""
                SELECT b.booking_id, b.passenger_name, b.seat_number, b.booking_date,
                       b.booking_status, b.payment_status, f.flight_number, 
                       f.origin_country, f.destination_country, f.departure_date,
                       f.departure_time, b.total_amount
                FROM flight_bookings b
                JOIN flights f ON b.flight_id = f.flight_id
                WHERE b.user_id = %s
                ORDER BY b.booking_date DESC
            """, (session['user_id'],))
            
            raw_flight_bookings = cursor.fetchall() or []
            
            for booking_data in raw_flight_bookings:
                booking = list(booking_data)
                if len(booking) > 10 and booking[10] is not None:
                    booking[10] = convert_timedelta_to_time(booking[10])
                flight_bookings.append(booking)
            
            # Get hotel bookings with payment status
            cursor.execute("""
                SELECT hb.booking_id, hb.guest_name, hb.check_in_date, hb.check_out_date,
                       hb.room_type, hb.booking_date, hb.total_amount, hb.booking_status,
                       h.hotel_name, h.location, hb.payment_status
                FROM hotel_bookings hb
                JOIN hotels h ON hb.hotel_id = h.hotel_id
                WHERE hb.user_id = %s
                ORDER BY hb.booking_date DESC
            """, (session['user_id'],))
            
            hotel_bookings = cursor.fetchall() or []
            
            # Get car bookings with payment status
            cursor.execute("""
                SELECT cb.booking_id, cb.renter_name, cb.pickup_date, cb.return_date,
                       cb.car_type, cb.booking_date, cb.total_amount, cb.booking_status,
                       cr.company_name, cr.location, cb.payment_status
                FROM car_bookings cb
                JOIN car_rentals cr ON cb.rental_id = cr.rental_id
                WHERE cb.user_id = %s
                ORDER BY cb.booking_date DESC
            """, (session['user_id'],))
            
            car_bookings = cursor.fetchall() or []
            
        except Error as e:
            print(f"Database error in dashboard: {e}")
            flash('Error loading bookings', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        flash('Database connection unavailable. Please try again later.', 'error')
    
    return render_template('dashboard.html', 
                         flight_bookings=flight_bookings,
                         hotel_bookings=hotel_bookings,
                         car_bookings=car_bookings)

@app.route('/cancel_booking/<int:booking_id>')
def cancel_booking(booking_id):
    """Cancel a booking"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = connection.cursor()
        
        # Fetch booking info and make sure it's valid
        cursor.execute("""
            SELECT flight_id, booking_status, payment_status 
            FROM flight_bookings 
            WHERE booking_id = %s AND user_id = %s
        """, (booking_id, session['user_id']))

        result = cursor.fetchone()
        if not result:
            flash('Booking not found', 'error')
            return redirect(url_for('dashboard'))

        flight_id, current_status, payment_status = result

        if current_status == 'Cancelled':
            flash('Booking is already cancelled', 'info')
            return redirect(url_for('dashboard'))

        # Update the booking to "Cancelled"
        cursor.execute("""
            UPDATE flight_bookings 
            SET booking_status = 'Cancelled'
            WHERE booking_id = %s AND user_id = %s
        """, (booking_id, session['user_id']))

        # Only increase available seats if booking was Paid
        if payment_status == 'Paid':
            cursor.execute("""
                UPDATE flights 
                SET available_seats = available_seats + 1
                WHERE flight_id = %s
            """, (flight_id,))

        connection.commit()
        flash('Booking cancelled successfully', 'success')
        
    except Error as e:
        connection.rollback()
        print(f"Database error in cancel_booking: {e}")
        flash('Cancellation failed. Please try again.', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return redirect(url_for('dashboard'))

# ADMIN ROUTES
@app.route('/admin')
def admin_login():
    """Admin login page"""
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_authenticate():
    """Authenticate admin user"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    # Simple admin authentication (in production, use proper authentication)
    # Default admin credentials: admin / admin123
    if username == 'admin' and password == 'admin123':
        session['admin_logged_in'] = True
        session['admin_username'] = username
        flash('Welcome to Admin Dashboard', 'success')
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Invalid admin credentials', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Logged out from admin panel', 'info')
    return redirect(url_for('admin_login'))

# Admin authentication decorator
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please login as admin to access this page', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard with statistics"""
    connection = get_db_connection()
    stats = {}
    
    if connection:
        try:
            cursor = connection.cursor()
            
            # Get statistics
            cursor.execute("SELECT COUNT(*) FROM flights WHERE departure_date >= CURDATE()")
            stats['active_flights'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM hotels WHERE availability > 0")
            stats['active_hotels'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM car_rentals WHERE availability > 0")
            stats['active_cars'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM flight_bookings WHERE booking_status = 'Confirmed'")
            stats['flight_bookings'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM hotel_bookings WHERE booking_status = 'Confirmed'")
            stats['hotel_bookings'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM car_bookings WHERE booking_status = 'Confirmed'")
            stats['car_bookings'] = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT SUM(total_amount) FROM flight_bookings 
                WHERE payment_status = 'Paid' AND booking_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            """)
            stats['revenue_flights'] = cursor.fetchone()[0] or 0
            
        except Error as e:
            print(f"Database error in admin dashboard: {e}")
            flash('Error loading statistics', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('admin/dashboard.html', stats=stats)

# FLIGHT ADMIN ROUTES WITH SEARCH
@app.route('/admin/flights')
@admin_required
def admin_flights():
    """List all flights for admin with search"""
    connection = get_db_connection()
    flights = []
    search_query = request.args.get('search', '').strip()
    
    if connection:
        try:
            cursor = connection.cursor()
            
            if search_query:
                # Search in multiple fields
                search_pattern = f"%{search_query}%"
                cursor.execute("""
                    SELECT flight_id, flight_number, origin_country, destination_country, 
                           origin_airport, destination_airport, departure_date, 
                           departure_time, arrival_time, aircraft_type, total_seats, 
                           available_seats, price, airline
                    FROM flights 
                    WHERE flight_number LIKE %s 
                       OR origin_country LIKE %s 
                       OR destination_country LIKE %s 
                       OR origin_airport LIKE %s 
                       OR destination_airport LIKE %s 
                       OR airline LIKE %s
                       OR aircraft_type LIKE %s
                    ORDER BY departure_date DESC, departure_time DESC
                """, (search_pattern, search_pattern, search_pattern, search_pattern, 
                      search_pattern, search_pattern, search_pattern))
            else:
                cursor.execute("""
                    SELECT flight_id, flight_number, origin_country, destination_country, 
                           origin_airport, destination_airport, departure_date, 
                           departure_time, arrival_time, aircraft_type, total_seats, 
                           available_seats, price, airline
                    FROM flights 
                    ORDER BY departure_date DESC, departure_time DESC
                """)
            
            flights = cursor.fetchall() or []
            
        except Error as e:
            print(f"Database error in admin flights: {e}")
            flash('Error loading flights', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('admin/flights.html', flights=flights, search_query=search_query)

@app.route('/admin/flights/add', methods=['GET', 'POST'])
@admin_required
def admin_add_flight():
    """Add new flight"""
    if request.method == 'POST':
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'error')
            return redirect(url_for('admin_flights'))
        
        try:
            cursor = connection.cursor()
            
            # Get form data
            flight_data = {
                'flight_number': request.form.get('flight_number'),
                'origin_country': request.form.get('origin_country'),
                'destination_country': request.form.get('destination_country'),
                'origin_airport': request.form.get('origin_airport'),
                'destination_airport': request.form.get('destination_airport'),
                'departure_date': request.form.get('departure_date'),
                'departure_time': request.form.get('departure_time'),
                'arrival_time': request.form.get('arrival_time'),
                'aircraft_type': request.form.get('aircraft_type'),
                'total_seats': int(request.form.get('total_seats', 0)),
                'available_seats': int(request.form.get('available_seats', 0)),
                'price': float(request.form.get('price', 0)),
                'airline': request.form.get('airline')
            }
            
            cursor.execute("""
                INSERT INTO flights 
                (flight_number, origin_country, destination_country, origin_airport, 
                 destination_airport, departure_date, departure_time, arrival_time, 
                 aircraft_type, total_seats, available_seats, price, airline)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, tuple(flight_data.values()))
            
            connection.commit()
            flash('Flight added successfully', 'success')
            return redirect(url_for('admin_flights'))
            
        except Error as e:
            connection.rollback()
            print(f"Database error in add flight: {e}")
            flash('Error adding flight', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('admin/flight_form.html', flight=None)

@app.route('/admin/flights/edit/<int:flight_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_flight(flight_id):
    """Edit existing flight"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('admin_flights'))
    
    try:
        cursor = connection.cursor()
        
        if request.method == 'POST':
            # Update flight
            flight_data = {
                'flight_number': request.form.get('flight_number'),
                'origin_country': request.form.get('origin_country'),
                'destination_country': request.form.get('destination_country'),
                'origin_airport': request.form.get('origin_airport'),
                'destination_airport': request.form.get('destination_airport'),
                'departure_date': request.form.get('departure_date'),
                'departure_time': request.form.get('departure_time'),
                'arrival_time': request.form.get('arrival_time'),
                'aircraft_type': request.form.get('aircraft_type'),
                'total_seats': int(request.form.get('total_seats', 0)),
                'available_seats': int(request.form.get('available_seats', 0)),
                'price': float(request.form.get('price', 0)),
                'airline': request.form.get('airline')
            }
            
            cursor.execute("""
                UPDATE flights SET 
                flight_number = %s, origin_country = %s, destination_country = %s,
                origin_airport = %s, destination_airport = %s, departure_date = %s,
                departure_time = %s, arrival_time = %s, aircraft_type = %s,
                total_seats = %s, available_seats = %s, price = %s, airline = %s
                WHERE flight_id = %s
            """, (*flight_data.values(), flight_id))
            
            connection.commit()
            flash('Flight updated successfully', 'success')
            return redirect(url_for('admin_flights'))
        
        else:
            # Get flight data
            cursor.execute("""
                SELECT flight_id, flight_number, origin_country, destination_country, 
                       origin_airport, destination_airport, departure_date, 
                       departure_time, arrival_time, aircraft_type, total_seats, 
                       available_seats, price, airline
                FROM flights WHERE flight_id = %s
            """, (flight_id,))
            
            flight = cursor.fetchone()
            if not flight:
                flash('Flight not found', 'error')
                return redirect(url_for('admin_flights'))
                
    except Error as e:
        if request.method == 'POST':
            connection.rollback()
        print(f"Database error in edit flight: {e}")
        flash('Error processing flight', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('admin/flight_form.html', flight=flight)

@app.route('/admin/flights/delete/<int:flight_id>')
@admin_required
def admin_delete_flight(flight_id):
    """Delete flight"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('admin_flights'))
    
    try:
        cursor = connection.cursor()
        
        # Check if flight has bookings
        cursor.execute("""
            SELECT COUNT(*) FROM flight_bookings 
            WHERE flight_id = %s AND booking_status = 'Confirmed'
        """, (flight_id,))
        
        booking_count = cursor.fetchone()[0]
        if booking_count > 0:
            flash(f'Cannot delete flight with {booking_count} active bookings', 'error')
        else:
            cursor.execute("DELETE FROM flights WHERE flight_id = %s", (flight_id,))
            connection.commit()
            flash('Flight deleted successfully', 'success')
            
    except Error as e:
        connection.rollback()
        print(f"Database error in delete flight: {e}")
        flash('Error deleting flight', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return redirect(url_for('admin_flights'))

# HOTEL ADMIN ROUTES WITH SEARCH
@app.route('/admin/hotels')
@admin_required
def admin_hotels():
    """List all hotels for admin with search"""
    connection = get_db_connection()
    hotels = []
    search_query = request.args.get('search', '').strip()
    
    if connection:
        try:
            cursor = connection.cursor()
            
            if search_query:
                # Search in multiple fields
                search_pattern = f"%{search_query}%"
                cursor.execute("""
                    SELECT hotel_id, hotel_name, location, star_rating, amenities, 
                           contact_info, price_per_night, availability
                    FROM hotels 
                    WHERE hotel_name LIKE %s 
                       OR location LIKE %s 
                       OR amenities LIKE %s
                       OR contact_info LIKE %s
                    ORDER BY hotel_name
                """, (search_pattern, search_pattern, search_pattern, search_pattern))
            else:
                cursor.execute("""
                    SELECT hotel_id, hotel_name, location, star_rating, amenities, 
                           contact_info, price_per_night, availability
                    FROM hotels 
                    ORDER BY hotel_name
                """)
            
            hotels = cursor.fetchall() or []
            
        except Error as e:
            print(f"Database error in admin hotels: {e}")
            flash('Error loading hotels', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('admin/hotels.html', hotels=hotels, search_query=search_query)

@app.route('/admin/hotels/add', methods=['GET', 'POST'])
@admin_required
def admin_add_hotel():
    """Add new hotel"""
    if request.method == 'POST':
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'error')
            return redirect(url_for('admin_hotels'))
        
        try:
            cursor = connection.cursor()
            
            hotel_data = {
                'hotel_name': request.form.get('hotel_name'),
                'location': request.form.get('location'),
                'star_rating': int(request.form.get('star_rating', 3)),
                'amenities': request.form.get('amenities'),
                'contact_info': request.form.get('contact_info'),
                'price_per_night': float(request.form.get('price_per_night', 0)),
                'availability': int(request.form.get('availability', 0))
            }
            
            cursor.execute("""
                INSERT INTO hotels 
                (hotel_name, location, star_rating, amenities, contact_info, 
                 price_per_night, availability)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, tuple(hotel_data.values()))
            
            connection.commit()
            flash('Hotel added successfully', 'success')
            return redirect(url_for('admin_hotels'))
            
        except Error as e:
            connection.rollback()
            print(f"Database error in add hotel: {e}")
            flash('Error adding hotel', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('admin/hotel_form.html', hotel=None)

@app.route('/admin/hotels/edit/<int:hotel_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_hotel(hotel_id):
    """Edit existing hotel"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('admin_hotels'))
    
    try:
        cursor = connection.cursor()
        
        if request.method == 'POST':
            hotel_data = {
                'hotel_name': request.form.get('hotel_name'),
                'location': request.form.get('location'),
                'star_rating': int(request.form.get('star_rating', 3)),
                'amenities': request.form.get('amenities'),
                'contact_info': request.form.get('contact_info'),
                'price_per_night': float(request.form.get('price_per_night', 0)),
                'availability': int(request.form.get('availability', 0))
            }
            
            cursor.execute("""
                UPDATE hotels SET 
                hotel_name = %s, location = %s, star_rating = %s,
                amenities = %s, contact_info = %s, price_per_night = %s, 
                availability = %s
                WHERE hotel_id = %s
            """, (*hotel_data.values(), hotel_id))
            
            connection.commit()
            flash('Hotel updated successfully', 'success')
            return redirect(url_for('admin_hotels'))
        
        else:
            cursor.execute("""
                SELECT hotel_id, hotel_name, location, star_rating, amenities, 
                       contact_info, price_per_night, availability
                FROM hotels WHERE hotel_id = %s
            """, (hotel_id,))
            
            hotel = cursor.fetchone()
            if not hotel:
                flash('Hotel not found', 'error')
                return redirect(url_for('admin_hotels'))
                
    except Error as e:
        if request.method == 'POST':
            connection.rollback()
        print(f"Database error in edit hotel: {e}")
        flash('Error processing hotel', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('admin/hotel_form.html', hotel=hotel)

@app.route('/admin/hotels/delete/<int:hotel_id>')
@admin_required
def admin_delete_hotel(hotel_id):
    """Delete hotel"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('admin_hotels'))
    
    try:
        cursor = connection.cursor()
        
        # Check if hotel has bookings
        cursor.execute("""
            SELECT COUNT(*) FROM hotel_bookings 
            WHERE hotel_id = %s AND booking_status = 'Confirmed'
        """, (hotel_id,))
        
        booking_count = cursor.fetchone()[0]
        if booking_count > 0:
            flash(f'Cannot delete hotel with {booking_count} active bookings', 'error')
        else:
            cursor.execute("DELETE FROM hotels WHERE hotel_id = %s", (hotel_id,))
            connection.commit()
            flash('Hotel deleted successfully', 'success')
            
    except Error as e:
        connection.rollback()
        print(f"Database error in delete hotel: {e}")
        flash('Error deleting hotel', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return redirect(url_for('admin_hotels'))

# CAR ADMIN ROUTES WITH SEARCH
@app.route('/admin/cars')
@admin_required
def admin_cars():
    """List all car rentals for admin with search"""
    connection = get_db_connection()
    cars = []
    search_query = request.args.get('search', '').strip()
    
    if connection:
        try:
            cursor = connection.cursor()
            
            if search_query:
                # Search in multiple fields
                search_pattern = f"%{search_query}%"
                cursor.execute("""
                    SELECT rental_id, company_name, location, car_types, availability, 
                           contact_info, price_per_day
                    FROM car_rentals 
                    WHERE company_name LIKE %s 
                       OR location LIKE %s 
                       OR car_types LIKE %s
                       OR contact_info LIKE %s
                    ORDER BY company_name
                """, (search_pattern, search_pattern, search_pattern, search_pattern))
            else:
                cursor.execute("""
                    SELECT rental_id, company_name, location, car_types, availability, 
                           contact_info, price_per_day
                    FROM car_rentals 
                    ORDER BY company_name
                """)
            
            cars = cursor.fetchall() or []
            
        except Error as e:
            print(f"Database error in admin cars: {e}")
            flash('Error loading car rentals', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('admin/cars.html', cars=cars, search_query=search_query)

@app.route('/admin/cars/add', methods=['GET', 'POST'])
@admin_required
def admin_add_car():
    """Add new car rental"""
    if request.method == 'POST':
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'error')
            return redirect(url_for('admin_cars'))
        
        try:
            cursor = connection.cursor()
            
            car_data = {
                'company_name': request.form.get('company_name'),
                'location': request.form.get('location'),
                'car_types': request.form.get('car_types'),
                'availability': int(request.form.get('availability', 0)),
                'contact_info': request.form.get('contact_info'),
                'price_per_day': float(request.form.get('price_per_day', 0))
            }
            
            cursor.execute("""
                INSERT INTO car_rentals 
                (company_name, location, car_types, availability, contact_info, price_per_day)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, tuple(car_data.values()))
            
            connection.commit()
            flash('Car rental added successfully', 'success')
            return redirect(url_for('admin_cars'))
            
        except Error as e:
            connection.rollback()
            print(f"Database error in add car: {e}")
            flash('Error adding car rental', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('admin/car_form.html', car=None)

@app.route('/admin/cars/edit/<int:rental_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_car(rental_id):
    """Edit existing car rental"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('admin_cars'))
    
    try:
        cursor = connection.cursor()
        
        if request.method == 'POST':
            car_data = {
                'company_name': request.form.get('company_name'),
                'location': request.form.get('location'),
                'car_types': request.form.get('car_types'),
                'availability': int(request.form.get('availability', 0)),
                'contact_info': request.form.get('contact_info'),
                'price_per_day': float(request.form.get('price_per_day', 0))
            }
            
            cursor.execute("""
                UPDATE car_rentals SET 
                company_name = %s, location = %s, car_types = %s,
                availability = %s, contact_info = %s, price_per_day = %s
                WHERE rental_id = %s
            """, (*car_data.values(), rental_id))
            
            connection.commit()
            flash('Car rental updated successfully', 'success')
            return redirect(url_for('admin_cars'))
        
        else:
            cursor.execute("""
                SELECT rental_id, company_name, location, car_types, availability, 
                       contact_info, price_per_day
                FROM car_rentals WHERE rental_id = %s
            """, (rental_id,))
            
            car = cursor.fetchone()
            if not car:
                flash('Car rental not found', 'error')
                return redirect(url_for('admin_cars'))
                
    except Error as e:
        if request.method == 'POST':
            connection.rollback()
        print(f"Database error in edit car: {e}")
        flash('Error processing car rental', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('admin/car_form.html', car=car)

@app.route('/admin/cars/delete/<int:rental_id>')
@admin_required
def admin_delete_car(rental_id):
    """Delete car rental"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('admin_cars'))
    
    try:
        cursor = connection.cursor()
        
        # Check if car has bookings
        cursor.execute("""
            SELECT COUNT(*) FROM car_bookings 
            WHERE rental_id = %s AND booking_status = 'Confirmed'
        """, (rental_id,))
        
        booking_count = cursor.fetchone()[0]
        if booking_count > 0:
            flash(f'Cannot delete car rental with {booking_count} active bookings', 'error')
        else:
            cursor.execute("DELETE FROM car_rentals WHERE rental_id = %s", (rental_id,))
            connection.commit()
            flash('Car rental deleted successfully', 'success')
            
    except Error as e:
        connection.rollback()
        print(f"Database error in delete car: {e}")
        flash('Error deleting car rental', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return redirect(url_for('admin_cars'))


@app.route('/admin/search')
@admin_required
def admin_global_search():
    """Global search across all entities"""
    search_query = request.args.get('q', '').strip()
    results = []
    
    if not search_query:
        return render_template('admin/search_results.html', results=results, search_query=search_query)
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            search_pattern = f"%{search_query}%"
            
            # Search flights
            cursor.execute("""
                SELECT flight_id as id, flight_number as name, 
                       CONCAT(origin_country, ' → ', destination_country) as details,
                       'flight' as type, departure_date, price
                FROM flights 
                WHERE flight_number LIKE %s 
                   OR origin_country LIKE %s 
                   OR destination_country LIKE %s 
                   OR airline LIKE %s
                LIMIT 5
            """, (search_pattern, search_pattern, search_pattern, search_pattern))
            
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'name': row[1],
                    'details': row[2],
                    'type': row[3],
                    'departure_date': row[4],
                    'price': row[5]
                })
            
            # Search hotels
            cursor.execute("""
                SELECT hotel_id as id, hotel_name as name, 
                       location as details, 'hotel' as type,
                       NULL as departure_date, price_per_night as price_per_night
                FROM hotels 
                WHERE hotel_name LIKE %s 
                   OR location LIKE %s
                LIMIT 5
            """, (search_pattern, search_pattern))
            
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'name': row[1],
                    'details': row[2],
                    'type': row[3],
                    'location': row[2],
                    'star_rating': 4,  # Default
                    'price_per_night': row[5],
                    'availability': 10  # Default
                })
            
            # Search cars
            cursor.execute("""
                SELECT rental_id as id, company_name as name, 
                       location as details, 'car' as type,
                       NULL as departure_date, price_per_day
                FROM car_rentals 
                WHERE company_name LIKE %s 
                   OR location LIKE %s
                LIMIT 5
            """, (search_pattern, search_pattern))
            
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'name': row[1],
                    'details': row[2],
                    'type': row[3],
                    'company_name': row[1],
                    'location': row[2],
                    'price_per_day': row[5],
                    'availability': 5  # Default
                })
            
        except Error as e:
            print(f"Database error in global search: {e}")
            flash('Error performing search', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('admin/search_results.html', results=results, search_query=search_query)



# app.py - AirPlanned Flight Booking System
# Complete fixed version with car booking and hotel/car payment status functionality

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, time
import mysql.connector
from mysql.connector import Error
import json
import re
import os
from decimal import Decimal

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'airplanned-secret-key-change-in-production')

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Root23500238',
    'database': 'airplanned_db',
    'port': 3307,
    'charset': 'utf8mb4',
    'autocommit': True,
    'use_unicode': True,
    'connect_timeout': 10
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def convert_timedelta_to_time(td):
    """Convert timedelta to time object"""
    if td is None:
        return None
    if isinstance(td, time):
        return td
    if isinstance(td, timedelta):
        total_seconds = int(td.total_seconds())
        hours = (total_seconds // 3600) % 24
        minutes = (total_seconds % 3600) // 60
        return time(hours, minutes)
    if isinstance(td, str):
        try:
            time_parts = td.split(':')
            return time(int(time_parts[0]), int(time_parts[1]))
        except:
            return None
    return td

def decimal_to_float(value):
    """Convert Decimal to float for template operations"""
    if isinstance(value, Decimal):
        return float(value)
    return value

def process_hotels_data(hotels_raw):
    """Process hotels data to add calculated prices"""
    hotels = []
    for hotel in hotels_raw:
        hotel_dict = {
            'id': hotel[0],
            'name': hotel[1],
            'location': hotel[2],
            'star_rating': hotel[3] or 3,
            'amenities': hotel[4],
            'contact_info': hotel[5],
            'base_price': decimal_to_float(hotel[6]),
            'availability': hotel[7]
        }
        
        # Calculate room prices
        base_price = hotel_dict['base_price']
        hotel_dict['room_prices'] = {
            'standard': base_price,
            'deluxe': base_price * 1.3,
            'suite': base_price * 1.8,
            'penthouse': base_price * 2.5
        }
        
        hotels.append(hotel_dict)
    
    return hotels

def process_cars_data(cars_raw):
    """Process car rental data to add calculated prices"""
    cars = []
    for car in cars_raw:
        car_dict = {
            'id': car[0],
            'company_name': car[1],
            'location': car[2],
            'car_types': car[3],
            'availability': car[4],
            'contact_info': car[5],
            'base_price': decimal_to_float(car[6])
        }
        
        # Calculate car type prices
        base_price = car_dict['base_price']
        car_dict['car_prices'] = {
            'Economy': base_price,
            'Compact': base_price * 1.2,
            'Mid-size': base_price * 1.4,
            'SUV': base_price * 1.8,
            'Luxury': base_price * 2.5,
            'Van': base_price * 2.0
        }
        
        cars.append(car_dict)
    
    return cars

# Template filters for safe time/date formatting
@app.template_filter('format_time')
def format_time_filter(time_obj):
    """Template filter to safely format time objects"""
    if time_obj is None:
        return 'N/A'
    
    time_obj = convert_timedelta_to_time(time_obj)
    
    if isinstance(time_obj, str):
        return time_obj
    
    if hasattr(time_obj, 'strftime'):
        return time_obj.strftime('%H:%M')
    
    return str(time_obj)

@app.template_filter('format_date')
def format_date_filter(date_obj):
    """Template filter to safely format date objects"""
    if date_obj is None:
        return 'N/A'
    
    if isinstance(date_obj, str):
        return date_obj
    
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime('%B %d, %Y')
    
    return str(date_obj)

@app.template_filter('decimal_to_float')
def decimal_to_float_filter(value):
    """Template filter to convert Decimal to float"""
    return decimal_to_float(value)

@app.route('/')
def index():
    """Home page with flight search"""
    connection = get_db_connection()
    origins, destinations, flights = [], [], []
    
    if connection:
        try:
            cursor = connection.cursor()
            
            cursor.execute("""
                SELECT DISTINCT origin_country, origin_airport 
                FROM flights 
                WHERE available_seats > 0 AND departure_date >= CURDATE()
                ORDER BY origin_country
            """)
            origins = cursor.fetchall() or []
            
            cursor.execute("""
                SELECT DISTINCT destination_country, destination_airport 
                FROM flights 
                WHERE available_seats > 0 AND departure_date >= CURDATE()
                ORDER BY destination_country
            """)
            destinations = cursor.fetchall() or []
            
            cursor.execute("""
                SELECT flight_id, flight_number, origin_country, destination_country, 
                       origin_airport, destination_airport, departure_date, 
                       departure_time, arrival_time, aircraft_type, total_seats, 
                       available_seats, price, airline
                FROM flights 
                WHERE available_seats > 0 AND departure_date >= CURDATE()
                ORDER BY departure_date, departure_time
                LIMIT 12
            """)
            flights = cursor.fetchall() or []
            
        except Error as e:
            print(f"Database error in index: {e}")
            flash('Error loading flight data. Please try again.', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        flash('Database connection unavailable. Please try again later.', 'error')
    
    return render_template('index.html', 
                         origins=origins, 
                         destinations=destinations, 
                         flights=flights)

@app.route('/search_flights', methods=['GET', 'POST'])
def search_flights():
    """Search flights based on criteria with round trip support"""
    connection = get_db_connection()
    outbound_flights = []
    return_flights = []
    
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('index'))
    
    try:
        cursor = connection.cursor()
        
        if request.method == 'POST':
            origin = request.form.get('origin', '').strip()
            destination = request.form.get('destination', '').strip()
            departure_date = request.form.get('departure_date', '').strip()
            return_date = request.form.get('return_date', '').strip()
            trip_type = request.form.get('trip_type', 'one-way')
            min_price = request.form.get('min_price', '').strip()
            max_price = request.form.get('max_price', '').strip()
            passengers = request.form.get('passengers', '1')
            flight_class = request.form.get('class', 'economy')
            
            # Base query for outbound flights
            outbound_query = """
                SELECT flight_id, flight_number, origin_country, destination_country, 
                       origin_airport, destination_airport, departure_date, 
                       departure_time, arrival_time, aircraft_type, total_seats, 
                       available_seats, price, airline
                FROM flights 
                WHERE available_seats >= %s AND departure_date >= CURDATE()
            """
            outbound_params = [int(passengers)]
            
            if origin:
                outbound_query += " AND origin_country = %s"
                outbound_params.append(origin)
            if destination:
                outbound_query += " AND destination_country = %s"
                outbound_params.append(destination)
            if departure_date:
                outbound_query += " AND departure_date = %s"
                outbound_params.append(departure_date)
            if min_price:
                try:
                    outbound_query += " AND price >= %s"
                    outbound_params.append(float(min_price))
                except ValueError:
                    flash('Invalid minimum price format', 'error')
            if max_price:
                try:
                    outbound_query += " AND price <= %s"
                    outbound_params.append(float(max_price))
                except ValueError:
                    flash('Invalid maximum price format', 'error')
            
            outbound_query += " ORDER BY departure_date, departure_time"
            
            # Execute outbound flights query
            cursor.execute(outbound_query, outbound_params)
            outbound_flights = cursor.fetchall() or []
            
            # If round trip, search for return flights
            if trip_type == 'round-trip' and return_date and origin and destination:
                return_query = """
                    SELECT flight_id, flight_number, origin_country, destination_country, 
                           origin_airport, destination_airport, departure_date, 
                           departure_time, arrival_time, aircraft_type, total_seats, 
                           available_seats, price, airline
                    FROM flights 
                    WHERE available_seats >= %s AND departure_date = %s
                    AND origin_country = %s AND destination_country = %s
                """
                return_params = [int(passengers), return_date, destination, origin]
                
                if min_price:
                    try:
                        return_query += " AND price >= %s"
                        return_params.append(float(min_price))
                    except ValueError:
                        pass
                if max_price:
                    try:
                        return_query += " AND price <= %s"
                        return_params.append(float(max_price))
                    except ValueError:
                        pass
                
                return_query += " ORDER BY departure_date, departure_time"
                
                # Execute return flights query
                cursor.execute(return_query, return_params)
                return_flights = cursor.fetchall() or []
            
            if not outbound_flights:
                flash('No outbound flights found matching your criteria.', 'info')
            elif trip_type == 'round-trip' and not return_flights:
                flash('No return flights found for your selected date.', 'warning')
        
    except Error as e:
        print(f"Database error in search: {e}")
        flash('Error searching flights. Please try again.', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('search_results.html', 
                         outbound_flights=outbound_flights,
                         return_flights=return_flights,
                         trip_type=request.form.get('trip_type', 'one-way') if request.method == 'POST' else 'one-way',
                         search_params=request.form if request.method == 'POST' else {})

@app.route('/book/<int:flight_id>')
def book_flight(flight_id):
    """Flight booking page with round trip support"""
    if 'user_id' not in session:
        flash('Please log in to book a flight', 'error')
        return redirect(url_for('login'))
    
    # Get parameters from URL
    passengers = request.args.get('passengers', 1, type=int)
    flight_class = request.args.get('class', 'economy')
    trip_type = request.args.get('trip_type', 'one-way')
    return_date = request.args.get('return_date', '')
    return_flight_id = request.args.get('return_flight_id', '', type=int)
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('index'))
    
    try:
        cursor = connection.cursor()
        
        # Get outbound flight details
        cursor.execute("""
            SELECT flight_id, flight_number, origin_country, destination_country, 
                   origin_airport, destination_airport, departure_date, departure_time, 
                   arrival_time, aircraft_type, total_seats, available_seats, price, airline
            FROM flights 
            WHERE flight_id = %s AND available_seats >= %s
        """, (flight_id, passengers))
        
        outbound_flight = cursor.fetchone()
        if not outbound_flight:
            flash('Flight not found or insufficient seats available', 'error')
            return redirect(url_for('index'))
        
        return_flight = None
        if trip_type == 'round-trip' and return_flight_id:
            cursor.execute("""
                SELECT flight_id, flight_number, origin_country, destination_country, 
                       origin_airport, destination_airport, departure_date, departure_time, 
                       arrival_time, aircraft_type, total_seats, available_seats, price, airline
                FROM flights 
                WHERE flight_id = %s AND available_seats >= %s
            """, (return_flight_id, passengers))
            
            return_flight = cursor.fetchone()
        
        # Get booked seats for both flights
        cursor.execute("""
            SELECT seat_number 
            FROM flight_bookings 
            WHERE flight_id = %s AND booking_status = 'Confirmed'
        """, (flight_id,))
        outbound_booked_seats = [row[0] for row in cursor.fetchall()]
        
        return_booked_seats = []
        if return_flight:
            cursor.execute("""
                SELECT seat_number 
                FROM flight_bookings 
                WHERE flight_id = %s AND booking_status = 'Confirmed'
            """, (return_flight_id,))
            return_booked_seats = [row[0] for row in cursor.fetchall()]
        
    except Error as e:
        print(f"Database error in booking: {e}")
        flash('Error loading flight details', 'error')
        return redirect(url_for('index'))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('booking.html', 
                         outbound_flight=outbound_flight,
                         return_flight=return_flight,
                         outbound_booked_seats=outbound_booked_seats,
                         return_booked_seats=return_booked_seats,
                         passengers=passengers,
                         flight_class=flight_class,
                         trip_type=trip_type)

@app.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    """Process flight booking confirmation with round trip support"""
    if 'user_id' not in session:
        flash('Please log in to book a flight', 'error')
        return redirect(url_for('login'))
    
    # Check if this is a round trip booking
    outbound_flight_id = request.form.get('outbound_flight_id')
    return_flight_id = request.form.get('return_flight_id', '')
    trip_type = request.form.get('trip_type', 'one-way')
    
    # Handle both single flight and round trip bookings
    if not outbound_flight_id:
        # Legacy single flight booking
        flight_id = request.form.get('flight_id')
        selected_seats = request.form.get('selectedSeat', '').split(',')
        passenger_names = request.form.getlist('passenger_name')
        passenger_emails = request.form.getlist('passenger_email')
        passenger_phones = request.form.getlist('passenger_phone')
        
        # Handle single passenger case
        if not passenger_names:
            passenger_names = [request.form.get('passenger_name', '').strip()]
            passenger_emails = [request.form.get('passenger_email', '').strip()]
            passenger_phones = [request.form.get('passenger_phone', '').strip()]
        
        # Clean up seat numbers
        selected_seats = [seat.strip() for seat in selected_seats if seat.strip()]
        
        if not all([flight_id, selected_seats, passenger_names[0], passenger_emails[0], passenger_phones[0]]):
            flash('All fields are required', 'error')
            return redirect(url_for('book_flight', flight_id=flight_id))
        
        return process_single_flight_booking(flight_id, selected_seats, passenger_names, passenger_emails, passenger_phones)
    
    else:
        # Round trip booking
        outbound_seats = request.form.get('outbound_selectedSeats', '').split(',')
        return_seats = request.form.get('return_selectedSeats', '').split(',') if trip_type == 'round-trip' else []
        
        passenger_names = request.form.getlist('passenger_name')
        passenger_emails = request.form.getlist('passenger_email')
        passenger_phones = request.form.getlist('passenger_phone')
        
        # Clean up seat numbers
        outbound_seats = [seat.strip() for seat in outbound_seats if seat.strip()]
        return_seats = [seat.strip() for seat in return_seats if seat.strip()]
        
        if not all([outbound_flight_id, outbound_seats, passenger_names[0], passenger_emails[0], passenger_phones[0]]):
            flash('All fields are required', 'error')
            return redirect(url_for('book_flight', flight_id=outbound_flight_id))
        
        return process_round_trip_booking(outbound_flight_id, return_flight_id, trip_type, 
                                        outbound_seats, return_seats, passenger_names, 
                                        passenger_emails, passenger_phones)

def process_single_flight_booking(flight_id, selected_seats, passenger_names, passenger_emails, passenger_phones):
    """Process single flight booking"""
    if len(selected_seats) != len(passenger_names):
        flash('Number of seats must match number of passengers', 'error')
        return redirect(url_for('book_flight', flight_id=flight_id))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('book_flight', flight_id=flight_id))
    
    try:
        cursor = connection.cursor()
        
        # Get flight price
        cursor.execute("SELECT price FROM flights WHERE flight_id = %s", (flight_id,))
        flight_price_result = cursor.fetchone()
        
        if not flight_price_result:
            flash('Flight not found', 'error')
            return redirect(url_for('index'))
            
        flight_price = flight_price_result[0]
        booking_ids = []
        
        # Create booking for each passenger
        for i, (name, email, phone, seat) in enumerate(zip(passenger_names, passenger_emails, passenger_phones, selected_seats)):
            if not all([name.strip(), email.strip(), phone.strip(), seat.strip()]):
                continue
                
            # Check if seat is still available
            cursor.execute("""
                SELECT COUNT(*) 
                FROM flight_bookings 
                WHERE flight_id = %s AND seat_number = %s AND booking_status = 'Confirmed'
            """, (flight_id, seat))
            
            if cursor.fetchone()[0] > 0:
                flash(f'Seat {seat} is no longer available. Please choose another seat.', 'error')
                return redirect(url_for('book_flight', flight_id=flight_id))
            
            # Insert booking
            cursor.execute("""
                INSERT INTO flight_bookings 
                (user_id, flight_id, passenger_name, passenger_email, passenger_phone, 
                 seat_number, total_amount, booking_status, payment_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (session['user_id'], flight_id, name.strip(), email.strip(), 
                  phone.strip(), seat, flight_price, 'Confirmed', 'Pending'))
            
            booking_ids.append(cursor.lastrowid)
        
        # Update available seats
        cursor.execute("""
            UPDATE flights 
            SET available_seats = available_seats - %s 
            WHERE flight_id = %s
        """, (len(booking_ids), flight_id))
        
        connection.commit()
        
        if len(booking_ids) == 1:
            flash('Booking confirmed successfully. Please proceed to payment.', 'success')
            return redirect(url_for('payment', booking_id=booking_ids[0]))
        else:
            flash(f'{len(booking_ids)} bookings confirmed successfully. Please proceed to payment.', 'success')
            return redirect(url_for('payment', booking_id=booking_ids[0]))
        
    except Error as e:
        connection.rollback()
        print(f"Database error in single flight booking: {e}")
        flash('Booking failed. Please try again.', 'error')
        return redirect(url_for('book_flight', flight_id=flight_id))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def process_round_trip_booking(outbound_flight_id, return_flight_id, trip_type, outbound_seats, 
                             return_seats, passenger_names, passenger_emails, passenger_phones):
    """Process round trip booking"""
    if len(outbound_seats) != len(passenger_names):
        flash('Number of seats must match number of passengers', 'error')
        return redirect(url_for('book_flight', flight_id=outbound_flight_id))
    
    if trip_type == 'round-trip' and len(return_seats) != len(passenger_names):
        flash('Number of return seats must match number of passengers', 'error')
        return redirect(url_for('book_flight', flight_id=outbound_flight_id))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('book_flight', flight_id=outbound_flight_id))
    
    try:
        cursor = connection.cursor()
        
        # Get flight prices
        cursor.execute("SELECT price FROM flights WHERE flight_id = %s", (outbound_flight_id,))
        outbound_price_result = cursor.fetchone()
        
        if not outbound_price_result:
            flash('Outbound flight not found', 'error')
            return redirect(url_for('index'))
            
        outbound_price = outbound_price_result[0]
        return_price = 0
        
        if trip_type == 'round-trip' and return_flight_id:
            cursor.execute("SELECT price FROM flights WHERE flight_id = %s", (return_flight_id,))
            return_price_result = cursor.fetchone()
            if return_price_result:
                return_price = return_price_result[0]
        
        booking_ids = []
        
        # Create bookings for each passenger
        for i, (name, email, phone) in enumerate(zip(passenger_names, passenger_emails, passenger_phones)):
            if not all([name.strip(), email.strip(), phone.strip()]):
                continue
            
            # Book outbound flight
            outbound_seat = outbound_seats[i] if i < len(outbound_seats) else None
            if outbound_seat:
                # Check if seat is still available
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM flight_bookings 
                    WHERE flight_id = %s AND seat_number = %s AND booking_status = 'Confirmed'
                """, (outbound_flight_id, outbound_seat))
                
                if cursor.fetchone()[0] > 0:
                    flash(f'Outbound seat {outbound_seat} is no longer available.', 'error')
                    return redirect(url_for('book_flight', flight_id=outbound_flight_id))
                
                # Insert outbound booking
                total_amount = outbound_price + return_price if trip_type == 'round-trip' else outbound_price
                cursor.execute("""
                    INSERT INTO flight_bookings 
                    (user_id, flight_id, passenger_name, passenger_email, passenger_phone, 
                     seat_number, total_amount, booking_status, payment_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (session['user_id'], outbound_flight_id, name.strip(), email.strip(), 
                      phone.strip(), outbound_seat, total_amount, 'Confirmed', 'Pending'))
                
                booking_ids.append(cursor.lastrowid)
            
            # Book return flight if round trip
            if trip_type == 'round-trip' and return_flight_id and i < len(return_seats):
                return_seat = return_seats[i]
                if return_seat:
                    # Check if return seat is still available
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM flight_bookings 
                        WHERE flight_id = %s AND seat_number = %s AND booking_status = 'Confirmed'
                    """, (return_flight_id, return_seat))
                    
                    if cursor.fetchone()[0] > 0:
                        flash(f'Return seat {return_seat} is no longer available.', 'error')
                        return redirect(url_for('book_flight', flight_id=outbound_flight_id))
                    
                    # Insert return booking
                    cursor.execute("""
                        INSERT INTO flight_bookings 
                        (user_id, flight_id, passenger_name, passenger_email, passenger_phone, 
                         seat_number, total_amount, booking_status, payment_status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (session['user_id'], return_flight_id, name.strip(), email.strip(), 
                          phone.strip(), return_seat, 0, 'Confirmed', 'Pending'))  # Total amount already included in outbound
                    
                    booking_ids.append(cursor.lastrowid)
        
        # Update available seats
        cursor.execute("""
            UPDATE flights 
            SET available_seats = available_seats - %s 
            WHERE flight_id = %s
        """, (len(passenger_names), outbound_flight_id))
        
        if trip_type == 'round-trip' and return_flight_id:
            cursor.execute("""
                UPDATE flights 
                SET available_seats = available_seats - %s 
                WHERE flight_id = %s
            """, (len(passenger_names), return_flight_id))
        
        connection.commit()
        
        flash(f'{"Round trip" if trip_type == "round-trip" else "Flight"} booking confirmed successfully. Please proceed to payment.', 'success')
        return redirect(url_for('payment', booking_id=booking_ids[0]))
        
    except Error as e:
        connection.rollback()
        print(f"Database error in round trip booking: {e}")
        flash('Booking failed. Please try again.', 'error')
        return redirect(url_for('book_flight', flight_id=outbound_flight_id))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/payment/<int:booking_id>')
def payment(booking_id):
    """Payment page"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT b.booking_id, b.passenger_name, b.seat_number, 
                   f.flight_number, f.origin_country, f.destination_country,
                   f.departure_date, f.departure_time, b.total_amount
            FROM flight_bookings b
            JOIN flights f ON b.flight_id = f.flight_id
            WHERE b.booking_id = %s AND b.user_id = %s AND b.payment_status = 'Pending'
        """, (booking_id, session['user_id']))
        
        booking_data = cursor.fetchone()
        if not booking_data:
            flash('Booking not found or payment already completed', 'error')
            return redirect(url_for('dashboard'))
        
        booking = list(booking_data)
        
        # Convert time if needed
        if len(booking) > 7 and booking[7] is not None:
            booking[7] = convert_timedelta_to_time(booking[7])
        
    except Error as e:
        print(f"Database error in payment: {e}")
        flash('Error loading booking details', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('payment.html', booking=booking)
@app.route('/process_payment', methods=['POST'])
def process_payment():
    """Process payment"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    
    booking_id = request.form.get('booking_id')
    card_number = request.form.get('card_number', '').replace(' ', '')
    expiry_date = request.form.get('expiry_date', '').strip()
    cvv = request.form.get('cvv', '').strip()
    cardholder_name = request.form.get('cardholder_name', '').strip()
    
    if not all([booking_id, card_number, expiry_date, cvv, cardholder_name]):
        flash('All payment fields are required', 'error')
        return redirect(url_for('payment', booking_id=booking_id))
    
    if len(card_number) != 16 or not card_number.isdigit():
        flash('Card number must be 16 digits', 'error')
        return redirect(url_for('payment', booking_id=booking_id))
    
    if not re.match(r'^\d{2}/\d{2}$', expiry_date):
        flash('Expiry date must be in MM/YY format', 'error')
        return redirect(url_for('payment', booking_id=booking_id))

    
    if len(cvv) != 3 or not cvv.isdigit():
        flash('CVV must be 3 digits', 'error')
        return redirect(url_for('payment', booking_id=booking_id))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('payment', booking_id=booking_id))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE flight_bookings 
            SET payment_status = 'Paid', payment_date = %s
            WHERE booking_id = %s AND user_id = %s AND payment_status = 'Pending'
        """, (datetime.now().date(), booking_id, session['user_id']))
        
        if cursor.rowcount == 0:
            flash('Booking not found or payment already processed', 'error')
            return redirect(url_for('dashboard'))
        
        connection.commit()
        flash('Payment successful', 'success')
        return redirect(url_for('payment_success', booking_id=booking_id))
        
    except Error as e:
        connection.rollback()
        print(f"Database error in process_payment: {e}")
        flash('Payment processing failed. Please try again.', 'error')
        return redirect(url_for('payment', booking_id=booking_id))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/payment_success/<int:booking_id>')
def payment_success(booking_id):
    """Payment confirmation"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT b.booking_id, b.passenger_name, b.seat_number, b.booking_date,
                   f.flight_number, f.origin_country, f.destination_country,
                   f.origin_airport, f.destination_airport, f.departure_date, 
                   f.departure_time, f.arrival_time, b.total_amount
            FROM flight_bookings b
            JOIN flights f ON b.flight_id = f.flight_id
            WHERE b.booking_id = %s AND b.user_id = %s AND b.payment_status = 'Paid'
        """, (booking_id, session['user_id']))
        
        booking_data = cursor.fetchone()
        if not booking_data:
            flash('Booking not found', 'error')
            return redirect(url_for('dashboard'))
        
        booking = list(booking_data)
        
        # Convert times if needed
        if len(booking) > 10 and booking[10] is not None:
            booking[10] = convert_timedelta_to_time(booking[10])
        if len(booking) > 11 and booking[11] is not None:
            booking[11] = convert_timedelta_to_time(booking[11])
        
    except Error as e:
        print(f"Database error in payment_success: {e}")
        flash('Error loading booking details', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('payment_success.html', booking=booking)

# HOTEL BOOKING ROUTES
@app.route('/hotels', methods=['GET', 'POST'])
def hotels():
    """Hotel booking page with database data and search functionality"""
    connection = get_db_connection()
    hotels = []
    
    if connection:
        try:
            cursor = connection.cursor()
            
            if request.method == 'POST':
                # Handle hotel search
                location = request.form.get('location', '').strip()
                check_in = request.form.get('check_in', '').strip()
                check_out = request.form.get('check_out', '').strip()
                guests = request.form.get('guests', '1')
                room_type = request.form.get('room_type', '').strip()
                star_rating = request.form.get('star_rating', '').strip()
                min_price = request.form.get('min_price_hotel', '').strip()
                max_price = request.form.get('max_price_hotel', '').strip()
                
                query = """
                    SELECT hotel_id, hotel_name, location, star_rating, amenities, 
                           contact_info, price_per_night, availability
                    FROM hotels 
                    WHERE availability > 0
                """
                params = []
                
                if location:
                    query += " AND location LIKE %s"
                    params.append(f"%{location}%")
                
                if star_rating:
                    query += " AND star_rating >= %s"
                    params.append(int(star_rating))
                
                if min_price:
                    try:
                        query += " AND price_per_night >= %s"
                        params.append(float(min_price))
                    except ValueError:
                        flash('Invalid minimum price format', 'error')
                
                if max_price:
                    try:
                        query += " AND price_per_night <= %s"
                        params.append(float(max_price))
                    except ValueError:
                        flash('Invalid maximum price format', 'error')
                
                query += " ORDER BY star_rating DESC, price_per_night ASC LIMIT 20"
                
                cursor.execute(query, params)
                hotels_raw = cursor.fetchall() or []
                hotels = process_hotels_data(hotels_raw)
                
                if not hotels:
                    flash('No hotels found matching your criteria.', 'info')
            else:
                # Default hotel listing
                cursor.execute("""
                    SELECT hotel_id, hotel_name, location, star_rating, amenities, 
                           contact_info, price_per_night, availability
                    FROM hotels 
                    WHERE availability > 0
                    ORDER BY star_rating DESC, price_per_night ASC
                    LIMIT 12
                """)
                hotels_raw = cursor.fetchall() or []
                hotels = process_hotels_data(hotels_raw)
            
        except Error as e:
            print(f"Database error in hotels: {e}")
            flash('Error loading hotels. Please try again.', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        flash('Database connection unavailable. Please try again later.', 'error')
    
    return render_template('hotels.html', hotels=hotels)

@app.route('/book_hotel/<int:hotel_id>')
def book_hotel(hotel_id):
    """Hotel booking page"""
    if 'user_id' not in session:
        flash('Please log in to book a hotel', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('hotels'))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT hotel_id, hotel_name, location, star_rating, amenities, 
                   contact_info, price_per_night, availability
            FROM hotels 
            WHERE hotel_id = %s AND availability > 0
        """, (hotel_id,))
        
        hotel_data = cursor.fetchone()
        if not hotel_data:
            flash('Hotel not found or no longer available', 'error')
            return redirect(url_for('hotels'))
        
        # Convert hotel tuple to list and ensure price is float for template
        hotel = list(hotel_data)
        hotel[6] = decimal_to_float(hotel[6])  # Convert price_per_night to float
        
        # Add room pricing calculations
        base_price = hotel[6]
        room_prices = {
            'standard': base_price,
            'deluxe': base_price * 1.3,
            'suite': base_price * 1.8,
            'penthouse': base_price * 2.5
        }
        
    except Error as e:
        print(f"Database error in hotel booking: {e}")
        flash('Error loading hotel details', 'error')
        return redirect(url_for('hotels'))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('hotel_booking.html', hotel=hotel, room_prices=room_prices)

@app.route('/confirm_hotel_booking', methods=['POST'])
def confirm_hotel_booking():
    """Process hotel booking confirmation"""
    if 'user_id' not in session:
        flash('Please log in to book a hotel', 'error')
        return redirect(url_for('login'))
    
    hotel_id = request.form.get('hotel_id')
    check_in_date = request.form.get('check_in_date')
    check_out_date = request.form.get('check_out_date')
    room_type = request.form.get('room_type')
    guest_name = request.form.get('guest_name', '').strip()
    guest_email = request.form.get('guest_email', '').strip()
    guest_phone = request.form.get('guest_phone', '').strip()
    
    if not all([hotel_id, check_in_date, check_out_date, room_type, guest_name, guest_email, guest_phone]):
        flash('All fields are required', 'error')
        return redirect(url_for('book_hotel', hotel_id=hotel_id))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('book_hotel', hotel_id=hotel_id))
    
    try:
        cursor = connection.cursor()
        
        # Get hotel price
        cursor.execute("SELECT price_per_night FROM hotels WHERE hotel_id = %s", (hotel_id,))
        hotel_price_result = cursor.fetchone()
        
        if not hotel_price_result:
            flash('Hotel not found', 'error')
            return redirect(url_for('hotels'))
            
        base_price = decimal_to_float(hotel_price_result[0])
        
        # Calculate total price based on room type
        room_multipliers = {
            'standard': 1.0,
            'deluxe': 1.3,
            'suite': 1.8,
            'penthouse': 2.5
        }
        
        nights = (datetime.strptime(check_out_date, '%Y-%m-%d') - datetime.strptime(check_in_date, '%Y-%m-%d')).days
        total_amount = base_price * room_multipliers.get(room_type, 1.0) * nights
        
        # Insert hotel booking with payment status
        cursor.execute("""
            INSERT INTO hotel_bookings 
            (user_id, hotel_id, check_in_date, check_out_date, room_type,
             guest_name, guest_email, guest_phone, booking_date, total_amount,
             payment_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (session['user_id'], hotel_id, check_in_date, check_out_date, room_type,
              guest_name, guest_email, guest_phone, datetime.now().date(), total_amount, 'Pending'))
        
        booking_id = cursor.lastrowid
        
        # Update hotel availability
        cursor.execute("""
            UPDATE hotels 
            SET availability = availability - 1 
            WHERE hotel_id = %s
        """, (hotel_id,))
        
        connection.commit()
        flash('Hotel booking confirmed successfully! Please proceed to payment.', 'success')
        return redirect(url_for('hotel_payment', booking_id=booking_id))
        
    except Error as e:
        connection.rollback()
        print(f"Database error in confirm_hotel_booking: {e}")
        flash('Hotel booking failed. Please try again.', 'error')
        return redirect(url_for('book_hotel', hotel_id=hotel_id))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/hotel_payment/<int:booking_id>')
def hotel_payment(booking_id):
    """Hotel payment page"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT hb.booking_id, hb.guest_name, hb.room_type, 
                   h.hotel_name, h.location, hb.check_in_date, 
                   hb.check_out_date, hb.total_amount, hb.payment_status
            FROM hotel_bookings hb
            JOIN hotels h ON hb.hotel_id = h.hotel_id
            WHERE hb.booking_id = %s AND hb.user_id = %s AND hb.payment_status = 'Pending'
        """, (booking_id, session['user_id']))
        
        booking_data = cursor.fetchone()
        if not booking_data:
            flash('Booking not found or payment already completed', 'error')
            return redirect(url_for('dashboard'))
        
        booking = list(booking_data)
        
    except Error as e:
        print(f"Database error in hotel_payment: {e}")
        flash('Error loading booking details', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('hotel_payment.html', booking=booking)

@app.route('/process_hotel_payment', methods=['POST'])
def process_hotel_payment():
    """Process hotel payment"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    
    booking_id = request.form.get('booking_id')
    card_number = request.form.get('card_number', '').replace(' ', '')
    expiry_date = request.form.get('expiry_date', '').strip()
    cvv = request.form.get('cvv', '').strip()
    cardholder_name = request.form.get('cardholder_name', '').strip()
    
    if not all([booking_id, card_number, expiry_date, cvv, cardholder_name]):
        flash('All payment fields are required', 'error')
        return redirect(url_for('hotel_payment', booking_id=booking_id))
    
    if len(card_number) != 16 or not card_number.isdigit():
        flash('Card number must be 16 digits', 'error')
        return redirect(url_for('hotel_payment', booking_id=booking_id))
    
    if not re.match(r'^\d{2}/\d{2}$', expiry_date):
        flash('Expiry date must be in MM/YY format', 'error')
        return redirect(url_for('hotel_payment', booking_id=booking_id))

    
    if len(cvv) != 3 or not cvv.isdigit():
        flash('CVV must be 3 digits', 'error')
        return redirect(url_for('hotel_payment', booking_id=booking_id))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('hotel_payment', booking_id=booking_id))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE hotel_bookings 
            SET payment_status = 'Paid'
            WHERE booking_id = %s AND user_id = %s AND payment_status = 'Pending'
        """, (booking_id, session['user_id']))
        
        if cursor.rowcount == 0:
            flash('Booking not found or payment already processed', 'error')
            return redirect(url_for('dashboard'))
        
        connection.commit()
        flash('Hotel payment successful', 'success')
        return redirect(url_for('dashboard'))
        
    except Error as e:
        connection.rollback()
        print(f"Database error in process_hotel_payment: {e}")
        flash('Payment processing failed. Please try again.', 'error')
        return redirect(url_for('hotel_payment', booking_id=booking_id))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# CAR RENTAL ROUTES
@app.route('/cars', methods=['GET', 'POST'])
def cars():
    """Car rental page with database data and search functionality"""
    connection = get_db_connection()
    car_rentals = []
    
    if connection:
        try:
            cursor = connection.cursor()
            
            if request.method == 'POST':
                # Handle car search
                pickup_location = request.form.get('pickup_location', '').strip()
                pickup_date = request.form.get('pickup_date', '').strip()
                pickup_time = request.form.get('pickup_time', '').strip()
                return_date = request.form.get('return_date', '').strip()
                return_time = request.form.get('return_time', '').strip()
                car_type = request.form.get('car_type', '').strip()
                transmission = request.form.get('transmission', '').strip()
                fuel_type = request.form.get('fuel_type', '').strip()
                
                query = """
                    SELECT rental_id, company_name, location, car_types, availability, 
                           contact_info, price_per_day
                    FROM car_rentals 
                    WHERE availability > 0
                """
                params = []
                
                if pickup_location:
                    query += " AND location LIKE %s"
                    params.append(f"%{pickup_location}%")
                
                if car_type:
                    query += " AND car_types LIKE %s"
                    params.append(f"%{car_type}%")
                
                query += " ORDER BY price_per_day ASC LIMIT 20"
                
                cursor.execute(query, params)
                cars_raw = cursor.fetchall() or []
                car_rentals = process_cars_data(cars_raw)
                
                if not car_rentals:
                    flash('No car rentals found matching your criteria.', 'info')
            else:
                # Default car rental listing
                cursor.execute("""
                    SELECT rental_id, company_name, location, car_types, availability, 
                           contact_info, price_per_day
                    FROM car_rentals 
                    WHERE availability > 0
                    ORDER BY price_per_day ASC
                    LIMIT 12
                """)
                cars_raw = cursor.fetchall() or []
                car_rentals = process_cars_data(cars_raw)
            
        except Error as e:
            print(f"Database error in cars: {e}")
            flash('Error loading car rentals. Please try again.', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        flash('Database connection unavailable. Please try again later.', 'error')
    
    return render_template('cars.html', car_rentals=car_rentals)

@app.route('/book_car/<int:rental_id>')
def book_car(rental_id):
    """Car rental booking page"""
    if 'user_id' not in session:
        flash('Please log in to book a car', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('cars'))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT rental_id, company_name, location, car_types, availability, 
                   contact_info, price_per_day
            FROM car_rentals 
            WHERE rental_id = %s AND availability > 0
        """, (rental_id,))
        
        rental_data = cursor.fetchone()
        if not rental_data:
            flash('Car rental not found or no longer available', 'error')
            return redirect(url_for('cars'))
        
        # Process rental data
        rentals_processed = process_cars_data([rental_data])
        rental = rentals_processed[0] if rentals_processed else None
        
        if not rental:
            flash('Error processing rental data', 'error')
            return redirect(url_for('cars'))
        
    except Error as e:
        print(f"Database error in car booking: {e}")
        flash('Error loading car rental details', 'error')
        return redirect(url_for('cars'))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('car_booking.html', rental=rental)

@app.route('/confirm_car_booking', methods=['POST'])
def confirm_car_booking():
    """Process car rental booking confirmation"""
    if 'user_id' not in session:
        flash('Please log in to book a car', 'error')
        return redirect(url_for('login'))
    
    rental_id = request.form.get('rental_id')
    pickup_date = request.form.get('pickup_date')
    return_date = request.form.get('return_date')
    car_type = request.form.get('car_type')
    renter_name = request.form.get('renter_name', '').strip()
    renter_email = request.form.get('renter_email', '').strip()
    renter_phone = request.form.get('renter_phone', '').strip()
    
    if not all([rental_id, pickup_date, return_date, car_type, renter_name, renter_email, renter_phone]):
        flash('All fields are required', 'error')
        return redirect(url_for('book_car', rental_id=rental_id))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('book_car', rental_id=rental_id))
    
    try:
        cursor = connection.cursor()
        
        # Get rental price
        cursor.execute("SELECT price_per_day FROM car_rentals WHERE rental_id = %s", (rental_id,))
        rental_price_result = cursor.fetchone()
        
        if not rental_price_result:
            flash('Car rental not found', 'error')
            return redirect(url_for('cars'))
            
        base_price = decimal_to_float(rental_price_result[0])
        
        # Calculate total price based on car type
        car_multipliers = {
            'Economy': 1.0,
            'Compact': 1.2,
            'Mid-size': 1.4,
            'SUV': 1.8,
            'Luxury': 2.5,
            'Van': 2.0
        }
        
        days = (datetime.strptime(return_date, '%Y-%m-%d') - datetime.strptime(pickup_date, '%Y-%m-%d')).days
        total_amount = base_price * car_multipliers.get(car_type, 1.0) * days
        
        # Insert car booking with payment status
        cursor.execute("""
            INSERT INTO car_bookings 
            (user_id, rental_id, pickup_date, return_date, car_type,
             renter_name, renter_email, renter_phone, booking_date, total_amount,
             payment_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (session['user_id'], rental_id, pickup_date, return_date, car_type,
              renter_name, renter_email, renter_phone, datetime.now().date(), total_amount, 'Pending'))
        
        booking_id = cursor.lastrowid
        
        # Update car availability
        cursor.execute("""
            UPDATE car_rentals 
            SET availability = availability - 1 
            WHERE rental_id = %s
        """, (rental_id,))
        
        connection.commit()
        flash('Car rental booking confirmed successfully! Please proceed to payment.', 'success')
        return redirect(url_for('car_payment', booking_id=booking_id))
        
    except Error as e:
        connection.rollback()
        print(f"Database error in confirm_car_booking: {e}")
        flash('Car rental booking failed. Please try again.', 'error')
        return redirect(url_for('book_car', rental_id=rental_id))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/car_payment/<int:booking_id>')
def car_payment(booking_id):
    """Car payment page"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT cb.booking_id, cb.renter_name, cb.car_type, 
                   cr.company_name, cr.location, cb.pickup_date, 
                   cb.return_date, cb.total_amount, cb.payment_status
            FROM car_bookings cb
            JOIN car_rentals cr ON cb.rental_id = cr.rental_id
            WHERE cb.booking_id = %s AND cb.user_id = %s AND cb.payment_status = 'Pending'
        """, (booking_id, session['user_id']))
        
        booking_data = cursor.fetchone()
        if not booking_data:
            flash('Booking not found or payment already completed', 'error')
            return redirect(url_for('dashboard'))
        
        booking = list(booking_data)
        
    except Error as e:
        print(f"Database error in car_payment: {e}")
        flash('Error loading booking details', 'error')
        return redirect(url_for('dashboard'))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('car_payment.html', booking=booking)

@app.route('/process_car_payment', methods=['POST'])
def process_car_payment():
    """Process car payment"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    
    booking_id = request.form.get('booking_id')
    card_number = request.form.get('card_number', '').replace(' ', '')
    expiry_date = request.form.get('expiry_date', '').strip()
    cvv = request.form.get('cvv', '').strip()
    cardholder_name = request.form.get('cardholder_name', '').strip()
    
    if not all([booking_id, card_number, expiry_date, cvv, cardholder_name]):
        flash('All payment fields are required', 'error')
        return redirect(url_for('car_payment', booking_id=booking_id))
    
    if len(card_number) != 16 or not card_number.isdigit():
        flash('Card number must be 16 digits', 'error')
        return redirect(url_for('car_payment', booking_id=booking_id))
    
    if not re.match(r'^\d{2}/\d{2}', expiry_date):
        flash('Expiry date must be in MM/YY format', 'error')
        return redirect(url_for('car_payment', booking_id=booking_id))
    
    if len(cvv) != 3 or not cvv.isdigit():
        flash('CVV must be 3 digits', 'error')
        return redirect(url_for('car_payment', booking_id=booking_id))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('car_payment', booking_id=booking_id))
    
    try:
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE car_bookings 
            SET payment_status = 'Paid'
            WHERE booking_id = %s AND user_id = %s AND payment_status = 'Pending'
        """, (booking_id, session['user_id']))
        
        if cursor.rowcount == 0:
            flash('Booking not found or payment already processed', 'error')
            return redirect(url_for('dashboard'))
        
        connection.commit()
        flash('Car rental payment successful', 'success')
        return redirect(url_for('dashboard'))
        
    except Error as e:
        connection.rollback()
        print(f"Database error in process_car_payment: {e}")
        flash('Payment processing failed. Please try again.', 'error')
        return redirect(url_for('car_payment', booking_id=booking_id))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# USER AUTHENTICATION ROUTES
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('login.html')
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'error')
            return render_template('login.html')
        
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT user_id, password, first_name, last_name 
                FROM users 
                WHERE email = %s
            """, (email,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user[1], password):
                session['user_id'] = user[0]
                session['user_name'] = f"{user[2]} {user[3]}"
                flash(f'Welcome back, {user[2]}', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password', 'error')
                
        except Error as e:
            print(f"Database error in login: {e}")
            flash('Login failed. Please try again.', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not all([full_name, email, password, confirm_password]):
            flash('All fields are required', 'error')
            return render_template('signup.html')

        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            flash('Please enter a valid email address', 'error')
            return render_template('signup.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('signup.html')
        
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'error')
            return render_template('signup.html')
        
        try:
            cursor = connection.cursor()
            
            cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Email already registered. Please use a different email.', 'error')
                return render_template('signup.html')
            
            # Split full name into first and last name
            name_parts = full_name.strip().split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            password_hash = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO users (first_name, last_name, email, password)
                VALUES (%s, %s, %s, %s)
            """, (first_name, last_name, email, password_hash))
            
            connection.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Error as e:
            connection.rollback()
            print(f"Database error in signup: {e}")
            flash('Registration failed. Please try again.', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """User logout"""
    user_name = session.get('user_name', 'User')
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """User dashboard with flight, hotel, and car bookings"""
    if 'user_id' not in session:
        flash('Please log in to view your dashboard', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    flight_bookings = []
    hotel_bookings = []
    car_bookings = []
    
    if connection:
        try:
            cursor = connection.cursor()
            
            # Get flight bookings
            cursor.execute("""
                SELECT b.booking_id, b.passenger_name, b.seat_number, b.booking_date,
                       b.booking_status, b.payment_status, f.flight_number, 
                       f.origin_country, f.destination_country, f.departure_date,
                       f.departure_time, b.total_amount
                FROM flight_bookings b
                JOIN flights f ON b.flight_id = f.flight_id
                WHERE b.user_id = %s
                ORDER BY b.booking_date DESC
            """, (session['user_id'],))
            
            raw_flight_bookings = cursor.fetchall() or []
            
            for booking_data in raw_flight_bookings:
                booking = list(booking_data)
                if len(booking) > 10 and booking[10] is not None:
                    booking[10] = convert_timedelta_to_time(booking[10])
                flight_bookings.append(booking)
            
            # Get hotel bookings with payment status
            cursor.execute("""
                SELECT hb.booking_id, hb.guest_name, hb.check_in_date, hb.check_out_date,
                       hb.room_type, hb.booking_date, hb.total_amount, hb.booking_status,
                       h.hotel_name, h.location, hb.payment_status
                FROM hotel_bookings hb
                JOIN hotels h ON hb.hotel_id = h.hotel_id
                WHERE hb.user_id = %s
                ORDER BY hb.booking_date DESC
            """, (session['user_id'],))
            
            hotel_bookings = cursor.fetchall() or []
            
            # Get car bookings with payment status
            cursor.execute("""
                SELECT cb.booking_id, cb.renter_name, cb.pickup_date, cb.return_date,
                       cb.car_type, cb.booking_date, cb.total_amount, cb.booking_status,
                       cr.company_name, cr.location, cb.payment_status
                FROM car_bookings cb
                JOIN car_rentals cr ON cb.rental_id = cr.rental_id
                WHERE cb.user_id = %s
                ORDER BY cb.booking_date DESC
            """, (session['user_id'],))
            
            car_bookings = cursor.fetchall() or []
            
        except Error as e:
            print(f"Database error in dashboard: {e}")
            flash('Error loading bookings', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        flash('Database connection unavailable. Please try again later.', 'error')
    
    return render_template('dashboard.html', 
                         flight_bookings=flight_bookings,
                         hotel_bookings=hotel_bookings,
                         car_bookings=car_bookings)

@app.route('/cancel_booking/<int:booking_id>')
def cancel_booking(booking_id):
    """Cancel a booking"""
    if 'user_id' not in session:
        flash('Please log in to continue', 'error')
        return redirect(url_for('login'))
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        cursor = connection.cursor()
        
        # Fetch booking info and make sure it's valid
        cursor.execute("""
            SELECT flight_id, booking_status, payment_status 
            FROM flight_bookings 
            WHERE booking_id = %s AND user_id = %s
        """, (booking_id, session['user_id']))

        result = cursor.fetchone()
        if not result:
            flash('Booking not found', 'error')
            return redirect(url_for('dashboard'))

        flight_id, current_status, payment_status = result

        if current_status == 'Cancelled':
            flash('Booking is already cancelled', 'info')
            return redirect(url_for('dashboard'))

        # Update the booking to "Cancelled"
        cursor.execute("""
            UPDATE flight_bookings 
            SET booking_status = 'Cancelled'
            WHERE booking_id = %s AND user_id = %s
        """, (booking_id, session['user_id']))

        # Only increase available seats if booking was Paid
        if payment_status == 'Paid':
            cursor.execute("""
                UPDATE flights 
                SET available_seats = available_seats + 1
                WHERE flight_id = %s
            """, (flight_id,))

        connection.commit()
        flash('Booking cancelled successfully', 'success')
        
    except Error as e:
        connection.rollback()
        print(f"Database error in cancel_booking: {e}")
        flash('Cancellation failed. Please try again.', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return redirect(url_for('dashboard'))

# ADMIN ROUTES
@app.route('/admin')
def admin_login():
    """Admin login page"""
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_authenticate():
    """Authenticate admin user"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    # Simple admin authentication (in production, use proper authentication)
    # Default admin credentials: admin / admin123
    if username == 'admin' and password == 'admin123':
        session['admin_logged_in'] = True
        session['admin_username'] = username
        flash('Welcome to Admin Dashboard', 'success')
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Invalid admin credentials', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Logged out from admin panel', 'info')
    return redirect(url_for('admin_login'))

# Admin authentication decorator
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please login as admin to access this page', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard with statistics"""
    connection = get_db_connection()
    stats = {}
    
    if connection:
        try:
            cursor = connection.cursor()
            
            # Get statistics
            cursor.execute("SELECT COUNT(*) FROM flights WHERE departure_date >= CURDATE()")
            stats['active_flights'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM hotels WHERE availability > 0")
            stats['active_hotels'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM car_rentals WHERE availability > 0")
            stats['active_cars'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM flight_bookings WHERE booking_status = 'Confirmed'")
            stats['flight_bookings'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM hotel_bookings WHERE booking_status = 'Confirmed'")
            stats['hotel_bookings'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM car_bookings WHERE booking_status = 'Confirmed'")
            stats['car_bookings'] = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT SUM(total_amount) FROM flight_bookings 
                WHERE payment_status = 'Paid' AND booking_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            """)
            stats['revenue_flights'] = cursor.fetchone()[0] or 0
            
        except Error as e:
            print(f"Database error in admin dashboard: {e}")
            flash('Error loading statistics', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('admin/dashboard.html', stats=stats)

# FLIGHT ADMIN ROUTES WITH SEARCH
@app.route('/admin/flights')
@admin_required
def admin_flights():
    """List all flights for admin with search"""
    connection = get_db_connection()
    flights = []
    search_query = request.args.get('search', '').strip()
    
    if connection:
        try:
            cursor = connection.cursor()
            
            if search_query:
                # Search in multiple fields
                search_pattern = f"%{search_query}%"
                cursor.execute("""
                    SELECT flight_id, flight_number, origin_country, destination_country, 
                           origin_airport, destination_airport, departure_date, 
                           departure_time, arrival_time, aircraft_type, total_seats, 
                           available_seats, price, airline
                    FROM flights 
                    WHERE flight_number LIKE %s 
                       OR origin_country LIKE %s 
                       OR destination_country LIKE %s 
                       OR origin_airport LIKE %s 
                       OR destination_airport LIKE %s 
                       OR airline LIKE %s
                       OR aircraft_type LIKE %s
                    ORDER BY departure_date DESC, departure_time DESC
                """, (search_pattern, search_pattern, search_pattern, search_pattern, 
                      search_pattern, search_pattern, search_pattern))
            else:
                cursor.execute("""
                    SELECT flight_id, flight_number, origin_country, destination_country, 
                           origin_airport, destination_airport, departure_date, 
                           departure_time, arrival_time, aircraft_type, total_seats, 
                           available_seats, price, airline
                    FROM flights 
                    ORDER BY departure_date DESC, departure_time DESC
                """)
            
            flights = cursor.fetchall() or []
            
        except Error as e:
            print(f"Database error in admin flights: {e}")
            flash('Error loading flights', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('admin/flights.html', flights=flights, search_query=search_query)

@app.route('/admin/flights/add', methods=['GET', 'POST'])
@admin_required
def admin_add_flight():
    """Add new flight"""
    if request.method == 'POST':
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'error')
            return redirect(url_for('admin_flights'))
        
        try:
            cursor = connection.cursor()
            
            # Get form data
            flight_data = {
                'flight_number': request.form.get('flight_number'),
                'origin_country': request.form.get('origin_country'),
                'destination_country': request.form.get('destination_country'),
                'origin_airport': request.form.get('origin_airport'),
                'destination_airport': request.form.get('destination_airport'),
                'departure_date': request.form.get('departure_date'),
                'departure_time': request.form.get('departure_time'),
                'arrival_time': request.form.get('arrival_time'),
                'aircraft_type': request.form.get('aircraft_type'),
                'total_seats': int(request.form.get('total_seats', 0)),
                'available_seats': int(request.form.get('available_seats', 0)),
                'price': float(request.form.get('price', 0)),
                'airline': request.form.get('airline')
            }
            
            cursor.execute("""
                INSERT INTO flights 
                (flight_number, origin_country, destination_country, origin_airport, 
                 destination_airport, departure_date, departure_time, arrival_time, 
                 aircraft_type, total_seats, available_seats, price, airline)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, tuple(flight_data.values()))
            
            connection.commit()
            flash('Flight added successfully', 'success')
            return redirect(url_for('admin_flights'))
            
        except Error as e:
            connection.rollback()
            print(f"Database error in add flight: {e}")
            flash('Error adding flight', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('admin/flight_form.html', flight=None)

@app.route('/admin/flights/edit/<int:flight_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_flight(flight_id):
    """Edit existing flight"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('admin_flights'))
    
    try:
        cursor = connection.cursor()
        
        if request.method == 'POST':
            # Update flight
            flight_data = {
                'flight_number': request.form.get('flight_number'),
                'origin_country': request.form.get('origin_country'),
                'destination_country': request.form.get('destination_country'),
                'origin_airport': request.form.get('origin_airport'),
                'destination_airport': request.form.get('destination_airport'),
                'departure_date': request.form.get('departure_date'),
                'departure_time': request.form.get('departure_time'),
                'arrival_time': request.form.get('arrival_time'),
                'aircraft_type': request.form.get('aircraft_type'),
                'total_seats': int(request.form.get('total_seats', 0)),
                'available_seats': int(request.form.get('available_seats', 0)),
                'price': float(request.form.get('price', 0)),
                'airline': request.form.get('airline')
            }
            
            cursor.execute("""
                UPDATE flights SET 
                flight_number = %s, origin_country = %s, destination_country = %s,
                origin_airport = %s, destination_airport = %s, departure_date = %s,
                departure_time = %s, arrival_time = %s, aircraft_type = %s,
                total_seats = %s, available_seats = %s, price = %s, airline = %s
                WHERE flight_id = %s
            """, (*flight_data.values(), flight_id))
            
            connection.commit()
            flash('Flight updated successfully', 'success')
            return redirect(url_for('admin_flights'))
        
        else:
            # Get flight data
            cursor.execute("""
                SELECT flight_id, flight_number, origin_country, destination_country, 
                       origin_airport, destination_airport, departure_date, 
                       departure_time, arrival_time, aircraft_type, total_seats, 
                       available_seats, price, airline
                FROM flights WHERE flight_id = %s
            """, (flight_id,))
            
            flight = cursor.fetchone()
            if not flight:
                flash('Flight not found', 'error')
                return redirect(url_for('admin_flights'))
                
    except Error as e:
        if request.method == 'POST':
            connection.rollback()
        print(f"Database error in edit flight: {e}")
        flash('Error processing flight', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('admin/flight_form.html', flight=flight)

@app.route('/admin/flights/delete/<int:flight_id>')
@admin_required
def admin_delete_flight(flight_id):
    """Delete flight"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('admin_flights'))
    
    try:
        cursor = connection.cursor()
        
        # Check if flight has bookings
        cursor.execute("""
            SELECT COUNT(*) FROM flight_bookings 
            WHERE flight_id = %s AND booking_status = 'Confirmed'
        """, (flight_id,))
        
        booking_count = cursor.fetchone()[0]
        if booking_count > 0:
            flash(f'Cannot delete flight with {booking_count} active bookings', 'error')
        else:
            cursor.execute("DELETE FROM flights WHERE flight_id = %s", (flight_id,))
            connection.commit()
            flash('Flight deleted successfully', 'success')
            
    except Error as e:
        connection.rollback()
        print(f"Database error in delete flight: {e}")
        flash('Error deleting flight', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return redirect(url_for('admin_flights'))

# HOTEL ADMIN ROUTES WITH SEARCH
@app.route('/admin/hotels')
@admin_required
def admin_hotels():
    """List all hotels for admin with search"""
    connection = get_db_connection()
    hotels = []
    search_query = request.args.get('search', '').strip()
    
    if connection:
        try:
            cursor = connection.cursor()
            
            if search_query:
                # Search in multiple fields
                search_pattern = f"%{search_query}%"
                cursor.execute("""
                    SELECT hotel_id, hotel_name, location, star_rating, amenities, 
                           contact_info, price_per_night, availability
                    FROM hotels 
                    WHERE hotel_name LIKE %s 
                       OR location LIKE %s 
                       OR amenities LIKE %s
                       OR contact_info LIKE %s
                    ORDER BY hotel_name
                """, (search_pattern, search_pattern, search_pattern, search_pattern))
            else:
                cursor.execute("""
                    SELECT hotel_id, hotel_name, location, star_rating, amenities, 
                           contact_info, price_per_night, availability
                    FROM hotels 
                    ORDER BY hotel_name
                """)
            
            hotels = cursor.fetchall() or []
            
        except Error as e:
            print(f"Database error in admin hotels: {e}")
            flash('Error loading hotels', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('admin/hotels.html', hotels=hotels, search_query=search_query)

@app.route('/admin/hotels/add', methods=['GET', 'POST'])
@admin_required
def admin_add_hotel():
    """Add new hotel"""
    if request.method == 'POST':
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'error')
            return redirect(url_for('admin_hotels'))
        
        try:
            cursor = connection.cursor()
            
            hotel_data = {
                'hotel_name': request.form.get('hotel_name'),
                'location': request.form.get('location'),
                'star_rating': int(request.form.get('star_rating', 3)),
                'amenities': request.form.get('amenities'),
                'contact_info': request.form.get('contact_info'),
                'price_per_night': float(request.form.get('price_per_night', 0)),
                'availability': int(request.form.get('availability', 0))
            }
            
            cursor.execute("""
                INSERT INTO hotels 
                (hotel_name, location, star_rating, amenities, contact_info, 
                 price_per_night, availability)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, tuple(hotel_data.values()))
            
            connection.commit()
            flash('Hotel added successfully', 'success')
            return redirect(url_for('admin_hotels'))
            
        except Error as e:
            connection.rollback()
            print(f"Database error in add hotel: {e}")
            flash('Error adding hotel', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('admin/hotel_form.html', hotel=None)

@app.route('/admin/hotels/edit/<int:hotel_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_hotel(hotel_id):
    """Edit existing hotel"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('admin_hotels'))
    
    try:
        cursor = connection.cursor()
        
        if request.method == 'POST':
            hotel_data = {
                'hotel_name': request.form.get('hotel_name'),
                'location': request.form.get('location'),
                'star_rating': int(request.form.get('star_rating', 3)),
                'amenities': request.form.get('amenities'),
                'contact_info': request.form.get('contact_info'),
                'price_per_night': float(request.form.get('price_per_night', 0)),
                'availability': int(request.form.get('availability', 0))
            }
            
            cursor.execute("""
                UPDATE hotels SET 
                hotel_name = %s, location = %s, star_rating = %s,
                amenities = %s, contact_info = %s, price_per_night = %s, 
                availability = %s
                WHERE hotel_id = %s
            """, (*hotel_data.values(), hotel_id))
            
            connection.commit()
            flash('Hotel updated successfully', 'success')
            return redirect(url_for('admin_hotels'))
        
        else:
            cursor.execute("""
                SELECT hotel_id, hotel_name, location, star_rating, amenities, 
                       contact_info, price_per_night, availability
                FROM hotels WHERE hotel_id = %s
            """, (hotel_id,))
            
            hotel = cursor.fetchone()
            if not hotel:
                flash('Hotel not found', 'error')
                return redirect(url_for('admin_hotels'))
                
    except Error as e:
        if request.method == 'POST':
            connection.rollback()
        print(f"Database error in edit hotel: {e}")
        flash('Error processing hotel', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('admin/hotel_form.html', hotel=hotel)

@app.route('/admin/hotels/delete/<int:hotel_id>')
@admin_required
def admin_delete_hotel(hotel_id):
    """Delete hotel"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('admin_hotels'))
    
    try:
        cursor = connection.cursor()
        
        # Check if hotel has bookings
        cursor.execute("""
            SELECT COUNT(*) FROM hotel_bookings 
            WHERE hotel_id = %s AND booking_status = 'Confirmed'
        """, (hotel_id,))
        
        booking_count = cursor.fetchone()[0]
        if booking_count > 0:
            flash(f'Cannot delete hotel with {booking_count} active bookings', 'error')
        else:
            cursor.execute("DELETE FROM hotels WHERE hotel_id = %s", (hotel_id,))
            connection.commit()
            flash('Hotel deleted successfully', 'success')
            
    except Error as e:
        connection.rollback()
        print(f"Database error in delete hotel: {e}")
        flash('Error deleting hotel', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return redirect(url_for('admin_hotels'))

# CAR ADMIN ROUTES WITH SEARCH
@app.route('/admin/cars')
@admin_required
def admin_cars():
    """List all car rentals for admin with search"""
    connection = get_db_connection()
    cars = []
    search_query = request.args.get('search', '').strip()
    
    if connection:
        try:
            cursor = connection.cursor()
            
            if search_query:
                # Search in multiple fields
                search_pattern = f"%{search_query}%"
                cursor.execute("""
                    SELECT rental_id, company_name, location, car_types, availability, 
                           contact_info, price_per_day
                    FROM car_rentals 
                    WHERE company_name LIKE %s 
                       OR location LIKE %s 
                       OR car_types LIKE %s
                       OR contact_info LIKE %s
                    ORDER BY company_name
                """, (search_pattern, search_pattern, search_pattern, search_pattern))
            else:
                cursor.execute("""
                    SELECT rental_id, company_name, location, car_types, availability, 
                           contact_info, price_per_day
                    FROM car_rentals 
                    ORDER BY company_name
                """)
            
            cars = cursor.fetchall() or []
            
        except Error as e:
            print(f"Database error in admin cars: {e}")
            flash('Error loading car rentals', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('admin/cars.html', cars=cars, search_query=search_query)

@app.route('/admin/cars/add', methods=['GET', 'POST'])
@admin_required
def admin_add_car():
    """Add new car rental"""
    if request.method == 'POST':
        connection = get_db_connection()
        if not connection:
            flash('Database connection error', 'error')
            return redirect(url_for('admin_cars'))
        
        try:
            cursor = connection.cursor()
            
            car_data = {
                'company_name': request.form.get('company_name'),
                'location': request.form.get('location'),
                'car_types': request.form.get('car_types'),
                'availability': int(request.form.get('availability', 0)),
                'contact_info': request.form.get('contact_info'),
                'price_per_day': float(request.form.get('price_per_day', 0))
            }
            
            cursor.execute("""
                INSERT INTO car_rentals 
                (company_name, location, car_types, availability, contact_info, price_per_day)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, tuple(car_data.values()))
            
            connection.commit()
            flash('Car rental added successfully', 'success')
            return redirect(url_for('admin_cars'))
            
        except Error as e:
            connection.rollback()
            print(f"Database error in add car: {e}")
            flash('Error adding car rental', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('admin/car_form.html', car=None)

@app.route('/admin/cars/edit/<int:rental_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_car(rental_id):
    """Edit existing car rental"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('admin_cars'))
    
    try:
        cursor = connection.cursor()
        
        if request.method == 'POST':
            car_data = {
                'company_name': request.form.get('company_name'),
                'location': request.form.get('location'),
                'car_types': request.form.get('car_types'),
                'availability': int(request.form.get('availability', 0)),
                'contact_info': request.form.get('contact_info'),
                'price_per_day': float(request.form.get('price_per_day', 0))
            }
            
            cursor.execute("""
                UPDATE car_rentals SET 
                company_name = %s, location = %s, car_types = %s,
                availability = %s, contact_info = %s, price_per_day = %s
                WHERE rental_id = %s
            """, (*car_data.values(), rental_id))
            
            connection.commit()
            flash('Car rental updated successfully', 'success')
            return redirect(url_for('admin_cars'))
        
        else:
            cursor.execute("""
                SELECT rental_id, company_name, location, car_types, availability, 
                       contact_info, price_per_day
                FROM car_rentals WHERE rental_id = %s
            """, (rental_id,))
            
            car = cursor.fetchone()
            if not car:
                flash('Car rental not found', 'error')
                return redirect(url_for('admin_cars'))
                
    except Error as e:
        if request.method == 'POST':
            connection.rollback()
        print(f"Database error in edit car: {e}")
        flash('Error processing car rental', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return render_template('admin/car_form.html', car=car)

@app.route('/admin/cars/delete/<int:rental_id>')
@admin_required
def admin_delete_car(rental_id):
    """Delete car rental"""
    connection = get_db_connection()
    if not connection:
        flash('Database connection error', 'error')
        return redirect(url_for('admin_cars'))
    
    try:
        cursor = connection.cursor()
        
        # Check if car has bookings
        cursor.execute("""
            SELECT COUNT(*) FROM car_bookings 
            WHERE rental_id = %s AND booking_status = 'Confirmed'
        """, (rental_id,))
        
        booking_count = cursor.fetchone()[0]
        if booking_count > 0:
            flash(f'Cannot delete car rental with {booking_count} active bookings', 'error')
        else:
            cursor.execute("DELETE FROM car_rentals WHERE rental_id = %s", (rental_id,))
            connection.commit()
            flash('Car rental deleted successfully', 'success')
            
    except Error as e:
        connection.rollback()
        print(f"Database error in delete car: {e}")
        flash('Error deleting car rental', 'error')
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
    
    return redirect(url_for('admin_cars'))


@app.route('/admin/search')
@admin_required
def admin_global_search():
    """Global search across all entities"""
    search_query = request.args.get('q', '').strip()
    results = {'flights': [], 'hotels': [], 'cars': []}
    
    if not search_query:
        return render_template('admin/search_results.html', results=results, search_query=search_query)
    
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            search_pattern = f"%{search_query}%"
            
            # Search flights
            cursor.execute("""
                SELECT flight_id, flight_number, origin_country, destination_country, 
                       departure_date, airline
                FROM flights 
                WHERE flight_number LIKE %s 
                   OR origin_country LIKE %s 
                   OR destination_country LIKE %s 
                   OR airline LIKE %s
                LIMIT 10
            """, (search_pattern, search_pattern, search_pattern, search_pattern))
            results['flights'] = cursor.fetchall() or []
            
            # Search hotels
            cursor.execute("""
                SELECT hotel_id, hotel_name, location, star_rating
                FROM hotels 
                WHERE hotel_name LIKE %s 
                   OR location LIKE %s
                LIMIT 10
            """, (search_pattern, search_pattern))
            results['hotels'] = cursor.fetchall() or []
            
            # Search cars
            cursor.execute("""
                SELECT rental_id, company_name, location
                FROM car_rentals 
                WHERE company_name LIKE %s 
                   OR location LIKE %s
                LIMIT 10
            """, (search_pattern, search_pattern))
            results['cars'] = cursor.fetchall() or []
            
        except Error as e:
            print(f"Database error in global search: {e}")
            flash('Error performing search', 'error')
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    return render_template('admin/search_results.html', results=results, search_query=search_query)


# ERROR HANDLERS
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("Starting AirPlanned Application...")
    app.run(debug=True, host='0.0.0.0', port=5000)
# ERROR HANDLERS
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("Starting AirPlanned Application...")
    app.run(debug=True, host='0.0.0.0', port=5000)