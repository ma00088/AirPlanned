-- AirPlanned Database Schema
-- Complete database structure with all tables and sample data

CREATE DATABASE IF NOT EXISTS airplanned_db;
USE airplanned_db;

-- Users table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    registration_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email)
);

-- Flights table
CREATE TABLE flights (
    flight_id INT AUTO_INCREMENT PRIMARY KEY,
    flight_number VARCHAR(10) UNIQUE NOT NULL,
    origin_country VARCHAR(50) NOT NULL,
    destination_country VARCHAR(50) NOT NULL,
    origin_airport VARCHAR(10) NOT NULL,
    destination_airport VARCHAR(10) NOT NULL,
    departure_date DATE NOT NULL,
    departure_time TIME NOT NULL,
    arrival_time TIME NOT NULL,
    aircraft_type VARCHAR(50) NOT NULL,
    total_seats INT NOT NULL,
    available_seats INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    airline VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_origin_dest (origin_country, destination_country),
    INDEX idx_departure_date (departure_date),
    INDEX idx_airline (airline),
    INDEX idx_price (price)
);

-- Flight bookings table
CREATE TABLE flight_bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    flight_id INT NOT NULL,
    passenger_name VARCHAR(100) NOT NULL,
    passenger_email VARCHAR(100) NOT NULL,
    passenger_phone VARCHAR(20) NOT NULL,
    seat_number VARCHAR(10) NOT NULL,
    booking_date DATE NOT NULL,
    booking_status ENUM('Confirmed', 'Cancelled') DEFAULT 'Confirmed',
    payment_status ENUM('Pending', 'Paid', 'Refunded') DEFAULT 'Pending',
    payment_date DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (flight_id) REFERENCES flights(flight_id) ON DELETE CASCADE,
    INDEX idx_user_bookings (user_id),
    INDEX idx_flight_bookings (flight_id),
    INDEX idx_booking_status (booking_status),
    INDEX idx_payment_status (payment_status),
    UNIQUE KEY unique_flight_seat (flight_id, seat_number, booking_status)
);

-- Hotels table
CREATE TABLE hotels (
    hotel_id INT AUTO_INCREMENT PRIMARY KEY,
    hotel_name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    country VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    address TEXT,
    star_rating INT CHECK (star_rating >= 1 AND star_rating <= 5),
    amenities TEXT,
    description TEXT,
    contact_info VARCHAR(255),
    email VARCHAR(100),
    phone VARCHAR(20),
    website VARCHAR(255),
    price_per_night DECIMAL(10, 2) NOT NULL,
    available_rooms INT NOT NULL,
    total_rooms INT NOT NULL,
    check_in_time TIME DEFAULT '15:00:00',
    check_out_time TIME DEFAULT '11:00:00',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_location (city, country),
    INDEX idx_star_rating (star_rating),
    INDEX idx_price_per_night (price_per_night)
);

-- Hotel bookings table
CREATE TABLE hotel_bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    hotel_id INT NOT NULL,
    guest_name VARCHAR(100) NOT NULL,
    guest_email VARCHAR(100) NOT NULL,
    guest_phone VARCHAR(20) NOT NULL,
    check_in_date DATE NOT NULL,
    check_out_date DATE NOT NULL,
    room_type VARCHAR(50) NOT NULL,
    number_of_rooms INT DEFAULT 1,
    number_of_guests INT DEFAULT 1,
    special_requests TEXT,
    booking_date DATE NOT NULL,
    booking_status ENUM('Confirmed', 'Cancelled', 'Checked-In', 'Checked-Out') DEFAULT 'Confirmed',
    payment_status ENUM('Pending', 'Paid', 'Refunded') DEFAULT 'Pending',
    payment_date DATE NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id) ON DELETE CASCADE,
    INDEX idx_user_hotel_bookings (user_id),
    INDEX idx_hotel_bookings (hotel_id),
    INDEX idx_check_in_date (check_in_date)
);

-- Car rentals table
CREATE TABLE car_rentals (
    rental_id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    car_make VARCHAR(50) NOT NULL,
    car_model VARCHAR(50) NOT NULL,
    car_year INT,
    car_type VARCHAR(50) NOT NULL,
    transmission ENUM('Automatic', 'Manual') DEFAULT 'Automatic',
    fuel_type ENUM('Gasoline', 'Electric', 'Hybrid', 'Diesel') DEFAULT 'Gasoline',
    location VARCHAR(100) NOT NULL,
    country VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    airport_code VARCHAR(10),
    price_per_day DECIMAL(10, 2) NOT NULL,
    available_cars INT NOT NULL,
    total_cars INT NOT NULL,
    features TEXT,
    mileage_limit INT DEFAULT 200,
    minimum_age INT DEFAULT 21,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_car_location (city, country),
    INDEX idx_car_type (car_type),
    INDEX idx_price_per_day (price_per_day),
    INDEX idx_company (company_name)
);

-- Car bookings table
CREATE TABLE car_bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    rental_id INT NOT NULL,
    renter_name VARCHAR(100) NOT NULL,
    renter_email VARCHAR(100) NOT NULL,
    renter_phone VARCHAR(20) NOT NULL,
    driver_license VARCHAR(50) NOT NULL,
    pickup_location VARCHAR(100) NOT NULL,
    return_location VARCHAR(100) NOT NULL,
    pickup_date DATE NOT NULL,
    pickup_time TIME NOT NULL,
    return_date DATE NOT NULL,
    return_time TIME NOT NULL,
    special_requests TEXT,
    booking_date DATE NOT NULL,
    booking_status ENUM('Confirmed', 'Cancelled', 'Picked-Up', 'Returned') DEFAULT 'Confirmed',
    payment_status ENUM('Pending', 'Paid', 'Refunded') DEFAULT 'Pending',
    payment_date DATE NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (rental_id) REFERENCES car_rentals(rental_id) ON DELETE CASCADE,
    INDEX idx_user_car_bookings (user_id),
    INDEX idx_car_rental_bookings (rental_id),
    INDEX idx_pickup_date (pickup_date)
);

-- Airlines table (for reference)
CREATE TABLE airlines (
    airline_id INT AUTO_INCREMENT PRIMARY KEY,
    airline_code VARCHAR(10) UNIQUE NOT NULL,
    airline_name VARCHAR(100) NOT NULL,
    country VARCHAR(50),
    website VARCHAR(255),
    contact_phone VARCHAR(20),
    logo_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Airports table (for reference)
CREATE TABLE airports (
    airport_id INT AUTO_INCREMENT PRIMARY KEY,
    airport_code VARCHAR(10) UNIQUE NOT NULL,
    airport_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL,
    timezone VARCHAR(50),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_airport_location (city, country)
);

-- Insert sample airlines
INSERT INTO airlines (airline_code, airline_name, country, contact_phone) VALUES
('AA', 'American Airlines', 'United States', '1-800-433-7300'),
('UA', 'United Airlines', 'United States', '1-800-864-8331'),
('DL', 'Delta Airlines', 'United States', '1-800-221-1212'),
('BA', 'British Airways', 'United Kingdom', '+44-844-493-0787'),
('AF', 'Air France', 'France', '+33-3654'),
('LH', 'Lufthansa', 'Germany', '+49-69-86799799'),
('EK', 'Emirates', 'United Arab Emirates', '+971-600-555555'),
('QF', 'Qantas', 'Australia', '+61-131-313');

-- Insert sample airports
INSERT INTO airports (airport_code, airport_name, city, country, timezone) VALUES
('JFK', 'John F. Kennedy International Airport', 'New York', 'United States', 'America/New_York'),
('LAX', 'Los Angeles International Airport', 'Los Angeles', 'United States', 'America/Los_Angeles'),
('ORD', 'O\'Hare International Airport', 'Chicago', 'United States', 'America/Chicago'),
('MIA', 'Miami International Airport', 'Miami', 'United States', 'America/New_York'),
('LHR', 'Heathrow Airport', 'London', 'United Kingdom', 'Europe/London'),
('CDG', 'Charles de Gaulle Airport', 'Paris', 'France', 'Europe/Paris'),
('FCO', 'Leonardo da Vinci Airport', 'Rome', 'Italy', 'Europe/Rome'),
('FRA', 'Frankfurt Airport', 'Frankfurt', 'Germany', 'Europe/Berlin'),
('NRT', 'Narita International Airport', 'Tokyo', 'Japan', 'Asia/Tokyo'),
('DXB', 'Dubai International Airport', 'Dubai', 'United Arab Emirates', 'Asia/Dubai'),
('SYD', 'Sydney Kingsford Smith Airport', 'Sydney', 'Australia', 'Australia/Sydney'),
('AKL', 'Auckland Airport', 'Auckland', 'New Zealand', 'Pacific/Auckland');

-- Insert sample flights
INSERT INTO flights (flight_number, origin_country, destination_country, origin_airport, destination_airport, departure_date, departure_time, arrival_time, aircraft_type, total_seats, available_seats, price, airline) VALUES
('AA101', 'New York', 'Los Angeles', 'JFK', 'LAX', '2025-08-15', '08:00:00', '11:30:00', 'Boeing 737', 150, 120, 299.99, 'American Airlines'),
('UA202', 'Los Angeles', 'Chicago', 'LAX', 'ORD', '2025-08-15', '14:00:00', '19:45:00', 'Airbus A320', 180, 165, 249.99, 'United Airlines'),
('DL303', 'Chicago', 'Miami', 'ORD', 'MIA', '2025-08-16', '10:30:00', '14:15:00', 'Boeing 757', 200, 180, 199.99, 'Delta Airlines'),
('BA404', 'London', 'Paris', 'LHR', 'CDG', '2025-08-17', '07:15:00', '09:45:00', 'Airbus A319', 140, 125, 89.99, 'British Airways'),
('AF505', 'Paris', 'Rome', 'CDG', 'FCO', '2025-08-18', '16:20:00', '18:30:00', 'Airbus A321', 190, 170, 129.99, 'Air France'),
('LH606', 'Frankfurt', 'Tokyo', 'FRA', 'NRT', '2025-08-19', '13:45:00', '08:30:00', 'Boeing 777', 350, 300, 899.99, 'Lufthansa'),
('EK707', 'Dubai', 'Sydney', 'DXB', 'SYD', '2025-08-20', '22:15:00', '17:45:00', 'Airbus A380', 500, 450, 1299.99, 'Emirates'),
('QF808', 'Sydney', 'Auckland', 'SYD', 'AKL', '2025-08-21', '11:00:00', '16:20:00', 'Boeing 787', 250, 200, 349.99, 'Qantas'),
('AA109', 'New York', 'Miami', 'JFK', 'MIA', '2025-08-22', '09:15:00', '12:45:00', 'Boeing 737', 150, 140, 189.99, 'American Airlines'),
('UA210', 'Chicago', 'Los Angeles', 'ORD', 'LAX', '2025-08-23', '16:30:00', '19:15:00', 'Airbus A320', 180, 175, 279.99, 'United Airlines'),
('DL311', 'Miami', 'New York', 'MIA', 'JFK', '2025-08-24', '14:20:00', '17:30:00', 'Boeing 757', 200, 190, 219.99, 'Delta Airlines'),
('BA412', 'Paris', 'London', 'CDG', 'LHR', '2025-08-25', '18:00:00', '18:45:00', 'Airbus A319', 140, 135, 79.99, 'British Airways');

-- Insert sample hotels
INSERT INTO hotels (hotel_name, location, country, city, star_rating, amenities, description, price_per_night, available_rooms, total_rooms) VALUES
('Grand Plaza Hotel', 'Manhattan, New York', 'United States', 'New York', 5, 'WiFi, Pool, Gym, Spa, Restaurant, Room Service, Concierge', 'Luxurious accommodations in the heart of Manhattan with stunning city views and world-class amenities.', 299.99, 50, 200),
('Ocean View Resort', 'Santa Monica, Los Angeles', 'United States', 'Los Angeles', 4, 'WiFi, Pool, Beach Access, Restaurant, Spa, Fitness Center', 'Beachfront resort with direct ocean access and breathtaking sunset views from every room.', 199.99, 30, 150),
('City Center Inn', 'Downtown Chicago', 'United States', 'Chicago', 3, 'WiFi, Parking, Restaurant, Business Center, Fitness Center', 'Comfortable business hotel in downtown Chicago, perfect for business travelers and city explorers.', 129.99, 40, 120),
('Luxury Suites', 'South Beach, Miami', 'United States', 'Miami', 5, 'WiFi, Pool, Spa, Butler Service, Private Beach, Fine Dining', 'Ultra-luxury suites with personalized butler service and exclusive access to private amenities.', 399.99, 20, 80),
('Budget Stay', 'The Strip, Las Vegas', 'United States', 'Las Vegas', 2, 'WiFi, Parking, Casino Access, Restaurant', 'Clean and affordable accommodations perfect for budget-conscious travelers visiting Las Vegas.', 79.99, 60, 300),
('Historic Grand Hotel', 'Back Bay, Boston', 'United States', 'Boston', 4, 'WiFi, Fine Dining, Library, Concierge, Fitness Center, Business Center', 'Historic landmark hotel with classic charm and modern amenities in the heart of Boston.', 249.99, 35, 100),
('The Ritz London', 'Piccadilly, London', 'United Kingdom', 'London', 5, 'WiFi, Spa, Fine Dining, Butler Service, Afternoon Tea, Concierge', 'Iconic luxury hotel in the heart of London offering unparalleled service and elegance.', 599.99, 25, 130),
('Hotel Le Bristol', '8th Arrondissement, Paris', 'France', 'Paris', 5, 'WiFi, Spa, Michelin Star Restaurant, Pool, Fitness Center, Pet Services', 'Palace hotel on Rue du Faubourg Saint-Honoré with exquisite French luxury and service.', 799.99, 15, 188);

-- Insert sample car rentals
INSERT INTO car_rentals (company_name, car_make, car_model, car_year, car_type, transmission, fuel_type, location, country, city, price_per_day, available_cars, total_cars, features) VALUES
('Enterprise', 'Toyota', 'Corolla', 2023, 'Economy', 'Automatic', 'Gasoline', 'JFK Airport', 'United States', 'New York', 29.99, 15, 25, 'AC, Radio, Bluetooth, USB Ports'),
('Hertz', 'Honda', 'Civic', 2023, 'Compact', 'Automatic', 'Gasoline', 'LAX Airport', 'United States', 'Los Angeles', 34.99, 20, 30, 'AC, Radio, Bluetooth, Backup Camera'),
('Avis', 'Ford', 'Explorer', 2023, 'SUV', 'Automatic', 'Gasoline', 'ORD Airport', 'United States', 'Chicago', 59.99, 10, 15, 'AC, GPS, 4WD, 7 Seats, Bluetooth'),
('Budget', 'BMW', '3 Series', 2023, 'Luxury', 'Automatic', 'Gasoline', 'MIA Airport', 'United States', 'Miami', 89.99, 5, 10, 'AC, GPS, Leather Seats, Sunroof, Premium Sound'),
('National', 'Honda', 'Odyssey', 2023, 'Van', 'Automatic', 'Gasoline', 'LAS Airport', 'United States', 'Las Vegas', 49.99, 8, 12, 'AC, GPS, 8 Seats, Sliding Doors, Entertainment System'),
('Hertz', 'Tesla', 'Model 3', 2023, 'Electric', 'Automatic', 'Electric', 'SFO Airport', 'United States', 'San Francisco', 79.99, 12, 20, 'Autopilot, Supercharger Access, Premium Interior, Mobile Connector'),
('Enterprise', 'Chevrolet', 'Malibu', 2023, 'Midsize', 'Automatic', 'Gasoline', 'BOS Airport', 'United States', 'Boston', 39.99, 18, 25, 'AC, Radio, Bluetooth, Backup Camera, Cruise Control'),
('Avis', 'Jeep', 'Wrangler', 2023, 'SUV', 'Manual', 'Gasoline', 'PHX Airport', 'United States', 'Phoenix', 69.99, 6, 10, 'AC, 4WD, Removable Doors, All-Terrain Tires, Bluetooth');

-- Create a test user (password is 'password123')
INSERT INTO users (full_name, email, password_hash, registration_date) VALUES
('John Doe', 'john.doe@example.com', 'scrypt:32768:8:1$w5XZJ6d2g8K9N7mL$b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1', '2025-07-01'),
('Jane Smith', 'jane.smith@example.com', 'scrypt:32768:8:1$w5XZJ6d2g8K9N7mL$b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1', '2025-07-02'),
('Mike Johnson', 'mike.johnson@example.com', 'scrypt:32768:8:1$w5XZJ6d2g8K9N7mL$b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1', '2025-07-03');

-- Insert some sample bookings
INSERT INTO flight_bookings (user_id, flight_id, passenger_name, passenger_email, passenger_phone, seat_number, booking_date, booking_status, payment_status, payment_date) VALUES
(1, 1, 'John Doe', 'john.doe@example.com', '+1-555-123-4567', '12A', '2025-07-10', 'Confirmed', 'Paid', '2025-07-10'),
(2, 3, 'Jane Smith', 'jane.smith@example.com', '+1-555-987-6543', '15C', '2025-07-11', 'Confirmed', 'Paid', '2025-07-11'),
(3, 5, 'Mike Johnson', 'mike.johnson@example.com', '+1-555-456-7890', '8B', '2025-07-12', 'Confirmed', 'Pending', NULL);

-- Create indexes for better performance
CREATE INDEX idx_flights_search ON flights (origin_country, destination_country, departure_date, available_seats);
CREATE INDEX idx_bookings_user_status ON flight_bookings (user_id, booking_status, payment_status);
CREATE INDEX idx_hotels_search ON hotels (city, country, star_rating, price_per_night);
CREATE INDEX idx_cars_search ON car_rentals (city, country, car_type, price_per_day);

-- Create views for common queries
CREATE VIEW available_flights AS
SELECT 
    f.*,
    a_origin.airport_name as origin_airport_name,
    a_dest.airport_name as destination_airport_name
FROM flights f
LEFT JOIN airports a_origin ON f.origin_airport = a_origin.airport_code
LEFT JOIN airports a_dest ON f.destination_airport = a_dest.airport_code
WHERE f.available_seats > 0 
AND f.departure_date >= CURDATE();

CREATE VIEW booking_summary AS
SELECT 
    b.*,
    f.flight_number,
    f.origin_country,
    f.destination_country,
    f.departure_date,
    f.departure_time,
    f.price,
    u.full_name as user_name,
    u.email as user_email
FROM flight_bookings b
JOIN flights f ON b.flight_id = f.flight_id
JOIN users u ON b.user_id = u.user_id;

-- Set up triggers for maintaining data consistency
DELIMITER //

CREATE TRIGGER update_seat_availability_after_booking
AFTER INSERT ON flight_bookings
FOR EACH ROW
BEGIN
    IF NEW.booking_status = 'Confirmed' THEN
        UPDATE flights 
        SET available_seats = available_seats - 1 
        WHERE flight_id = NEW.flight_id;
    END IF;
END//

CREATE TRIGGER update_seat_availability_after_cancellation
AFTER UPDATE ON flight_bookings
FOR EACH ROW
BEGIN
    IF OLD.booking_status = 'Confirmed' AND NEW.booking_status = 'Cancelled' THEN
        UPDATE flights 
        SET available_seats = available_seats + 1 
        WHERE flight_id = NEW.flight_id;
    END IF;
END//

DELIMITER ;

-- Insert additional sample data for testing
INSERT INTO flights (flight_number, origin_country, destination_country, origin_airport, destination_airport, departure_date, departure_time, arrival_time, aircraft_type, total_seats, available_seats, price, airline) VALUES
('AA150', 'Los Angeles', 'New York', 'LAX', 'JFK', '2025-08-26', '06:00:00', '14:30:00', 'Boeing 777', 300, 285, 399.99, 'American Airlines'),
('UA250', 'Chicago', 'Miami', 'ORD', 'MIA', '2025-08-27', '11:15:00', '15:45:00', 'Airbus A321', 185, 170, 229.99, 'United Airlines'),
('DL350', 'Miami', 'Los Angeles', 'MIA', 'LAX', '2025-08-28', '13:30:00', '16:45:00', 'Boeing 757', 200, 195, 319.99, 'Delta Airlines');