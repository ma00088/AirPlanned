-- =====================================================
-- AirPlanned Flight Booking System - Complete Database
-- University Project - Bahrain Focus
-- Following Exact Schema Diagram - CLEAN VERSION
-- =====================================================

-- MySQL Workbench Forward Engineering
SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema airplanned_db
-- -----------------------------------------------------
DROP SCHEMA IF EXISTS `airplanned_db`;
CREATE SCHEMA `airplanned_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `airplanned_db`;

-- -----------------------------------------------------
-- Table `airplanned_db`.`users`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `airplanned_db`.`users` (
  `user_id` INT NOT NULL AUTO_INCREMENT,
  `first_name` VARCHAR(50) NOT NULL,
  `last_name` VARCHAR(50) NOT NULL,
  `email` VARCHAR(100) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `phone_number` VARCHAR(20) NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE INDEX `email_UNIQUE` (`email` ASC))
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `airplanned_db`.`flights`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `airplanned_db`.`flights` (
  `flight_id` INT NOT NULL AUTO_INCREMENT,
  `flight_number` VARCHAR(10) NOT NULL,
  `origin_country` VARCHAR(50) NOT NULL,
  `destination_country` VARCHAR(50) NOT NULL,
  `origin_airport` VARCHAR(10) NOT NULL,
  `destination_airport` VARCHAR(10) NOT NULL,
  `departure_date` DATE NOT NULL,
  `departure_time` TIME NOT NULL,
  `arrival_time` TIME NOT NULL,
  `aircraft_type` VARCHAR(50) NOT NULL,
  `total_seats` INT NOT NULL,
  `available_seats` INT NOT NULL,
  `price` DECIMAL(10,2) NOT NULL,
  `airline` VARCHAR(50) NOT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`flight_id`),
  UNIQUE INDEX `flight_number_UNIQUE` (`flight_number` ASC),
  INDEX `idx_origin_dest` (`origin_country` ASC, `destination_country` ASC),
  INDEX `idx_departure_date` (`departure_date` ASC))
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `airplanned_db`.`hotels`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `airplanned_db`.`hotels` (
  `hotel_id` INT NOT NULL AUTO_INCREMENT,
  `hotel_name` VARCHAR(100) NOT NULL,
  `location` VARCHAR(100) NOT NULL,
  `star_rating` INT NULL,
  `amenities` TEXT NULL,
  `contact_info` VARCHAR(255) NULL,
  `price_per_night` DECIMAL(10,2) NOT NULL,
  `availability` INT NOT NULL DEFAULT 0,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`hotel_id`),
  CONSTRAINT `chk_star_rating` CHECK ((`star_rating` >= 1) AND (`star_rating` <= 5)))
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `airplanned_db`.`car_rentals`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `airplanned_db`.`car_rentals` (
  `rental_id` INT NOT NULL AUTO_INCREMENT,
  `company_name` VARCHAR(100) NOT NULL,
  `location` VARCHAR(100) NOT NULL,
  `car_types` TEXT NOT NULL,
  `availability` INT NOT NULL DEFAULT 0,
  `contact_info` VARCHAR(255) NULL,
  `price_per_day` DECIMAL(10,2) NOT NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`rental_id`))
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `airplanned_db`.`flight_bookings`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `airplanned_db`.`flight_bookings` (
  `booking_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `flight_id` INT NOT NULL,
  `booking_date` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `seat_number` VARCHAR(10) NOT NULL,
  `payment_status` ENUM('Pending', 'Paid', 'Cancelled', 'Refunded') NULL DEFAULT 'Pending',
  `total_amount` DECIMAL(10,2) NOT NULL,
  `passenger_name` VARCHAR(100) NOT NULL,
  `passenger_email` VARCHAR(100) NOT NULL,
  `passenger_phone` VARCHAR(20) NOT NULL,
  `booking_status` ENUM('Confirmed', 'Cancelled') NULL DEFAULT 'Confirmed',
  `payment_date` DATE NULL,
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`booking_id`),
  INDEX `fk_flight_bookings_users_idx` (`user_id` ASC),
  INDEX `fk_flight_bookings_flights_idx` (`flight_id` ASC),
  CONSTRAINT `fk_flight_bookings_users`
    FOREIGN KEY (`user_id`)
    REFERENCES `airplanned_db`.`users` (`user_id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_flight_bookings_flights`
    FOREIGN KEY (`flight_id`)
    REFERENCES `airplanned_db`.`flights` (`flight_id`)
    ON DELETE CASCADE)
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `airplanned_db`.`hotel_bookings`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `airplanned_db`.`hotel_bookings` (
  `booking_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `hotel_id` INT NOT NULL,
  `check_in_date` DATE NOT NULL,
  `check_out_date` DATE NOT NULL,
  `room_type` VARCHAR(50) NOT NULL,
  `payment_status` ENUM('Pending', 'Paid', 'Cancelled', 'Refunded') NULL DEFAULT 'Pending',
  `total_amount` DECIMAL(10,2) NOT NULL,
  `guest_name` VARCHAR(100) NOT NULL,
  `guest_email` VARCHAR(100) NOT NULL,
  `guest_phone` VARCHAR(20) NOT NULL,
  `booking_date` DATE NOT NULL,
  `booking_status` ENUM('Confirmed', 'Cancelled', 'Checked-In', 'Checked-Out') NULL DEFAULT 'Confirmed',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`booking_id`),
  INDEX `fk_hotel_bookings_users_idx` (`user_id` ASC),
  INDEX `fk_hotel_bookings_hotels_idx` (`hotel_id` ASC),
  CONSTRAINT `fk_hotel_bookings_users`
    FOREIGN KEY (`user_id`)
    REFERENCES `airplanned_db`.`users` (`user_id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_hotel_bookings_hotels`
    FOREIGN KEY (`hotel_id`)
    REFERENCES `airplanned_db`.`hotels` (`hotel_id`)
    ON DELETE CASCADE)
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `airplanned_db`.`car_bookings`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `airplanned_db`.`car_bookings` (
  `booking_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `rental_id` INT NOT NULL,
  `pickup_date` DATE NOT NULL,
  `return_date` DATE NOT NULL,
  `car_type` VARCHAR(50) NOT NULL,
  `payment_status` ENUM('Pending', 'Paid', 'Cancelled', 'Refunded') NULL DEFAULT 'Pending',
  `total_amount` DECIMAL(10,2) NOT NULL,
  `renter_name` VARCHAR(100) NOT NULL,
  `renter_email` VARCHAR(100) NOT NULL,
  `renter_phone` VARCHAR(20) NOT NULL,
  `booking_date` DATE NOT NULL,
  `booking_status` ENUM('Confirmed', 'Cancelled', 'Picked-Up', 'Returned') NULL DEFAULT 'Confirmed',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`booking_id`),
  INDEX `fk_car_bookings_users_idx` (`user_id` ASC),
  INDEX `fk_car_bookings_rentals_idx` (`rental_id` ASC),
  CONSTRAINT `fk_car_bookings_users`
    FOREIGN KEY (`user_id`)
    REFERENCES `airplanned_db`.`users` (`user_id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_car_bookings_rentals`
    FOREIGN KEY (`rental_id`)
    REFERENCES `airplanned_db`.`car_rentals` (`rental_id`)
    ON DELETE CASCADE)
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `airplanned_db`.`support_tickets`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `airplanned_db`.`support_tickets` (
  `ticket_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `subject` VARCHAR(200) NOT NULL,
  `description` TEXT NOT NULL,
  `status` ENUM('Open', 'In Progress', 'Resolved', 'Closed') NULL DEFAULT 'Open',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ticket_id`),
  INDEX `fk_support_tickets_users_idx` (`user_id` ASC),
  CONSTRAINT `fk_support_tickets_users`
    FOREIGN KEY (`user_id`)
    REFERENCES `airplanned_db`.`users` (`user_id`)
    ON DELETE CASCADE)
ENGINE = InnoDB;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

-- =====================================================
-- DATA INSERTION
-- =====================================================

-- Users
START TRANSACTION;
INSERT INTO `airplanned_db`.`users` (`first_name`, `last_name`, `email`, `password`, `phone_number`) VALUES 
('Ahmed', 'Al-Khalifa', 'ahmed.alkhalifa@example.com', 'pbkdf2:sha256:600000$salt123$abcd1234efgh5678', '+973-3333-1111'),
('Fatima', 'Al-Zahra', 'fatima.alzahra@example.com', 'pbkdf2:sha256:600000$salt456$ijkl9012mnop3456', '+973-3333-2222'),
('Mohammed', 'bin Rashid', 'mohammed.binrashid@example.com', 'pbkdf2:sha256:600000$salt789$qrst7890uvwx1234', '+971-5555-3333'),
('Aisha', 'Al-Sabah', 'aisha.alsabah@example.com', 'pbkdf2:sha256:600000$salt101$zxcv4567asdf8901', '+965-9999-4444'),
('John', 'Doe', 'john.doe@example.com', 'pbkdf2:sha256:600000$salt112$poiu2345mnbv6789', '+1-555-123-4567'),
('Jane', 'Smith', 'jane.smith@example.com', 'pbkdf2:sha256:600000$salt131$lkjh1357qwer9135', '+1-555-987-6543');
COMMIT;

-- Flights
START TRANSACTION;

INSERT INTO `airplanned_db`.`flights` 
(`flight_number`, `origin_country`, `destination_country`, `origin_airport`, `destination_airport`, `departure_date`, `departure_time`, `arrival_time`, `aircraft_type`, `total_seats`, `available_seats`, `price`, `airline`) 
VALUES

-- ADDITIONAL GULF/REGIONAL FLIGHTS FROM BAHRAIN
('GF010', 'Manama', 'Jeddah', 'BAH', 'JED', CURDATE(), '12:30:00', '14:45:00', 'Airbus A320', 150, 140, 119.99, 'Gulf Air'),
('GF011', 'Manama', 'Muscat', 'BAH', 'MCT', CURDATE(), '08:00:00', '09:30:00', 'Airbus A320', 150, 135, 109.99, 'Gulf Air'),
('GF012', 'Manama', 'Cairo', 'BAH', 'CAI', CURDATE(), '15:20:00', '18:00:00', 'Airbus A321', 180, 160, 159.99, 'Gulf Air'),
('GF013', 'Manama', 'Beirut', 'BAH', 'BEY', DATE_ADD(CURDATE(), INTERVAL 1 DAY), '13:45:00', '16:15:00', 'Boeing 737', 160, 145, 149.99, 'Gulf Air'),
('GF014', 'Manama', 'Istanbul', 'BAH', 'IST', DATE_ADD(CURDATE(), INTERVAL 2 DAY), '02:15:00', '06:30:00', 'Boeing 737', 160, 140, 199.99, 'Gulf Air'),
('GF015', 'Manama', 'Tehran', 'BAH', 'IKA', DATE_ADD(CURDATE(), INTERVAL 3 DAY), '10:30:00', '13:00:00', 'Airbus A320', 150, 130, 139.99, 'Gulf Air'),
('GF016', 'Manama', 'Amman', 'BAH', 'AMM', DATE_ADD(CURDATE(), INTERVAL 4 DAY), '07:45:00', '10:00:00', 'Airbus A321', 180, 160, 159.99, 'Gulf Air'),
('GF017', 'Manama', 'Baghdad', 'BAH', 'BGW', DATE_ADD(CURDATE(), INTERVAL 5 DAY), '09:00:00', '11:30:00', 'Boeing 737', 160, 150, 129.99, 'Gulf Air'),

-- RETURN FLIGHTS TO BAHRAIN
('GF018', 'Jeddah', 'Manama', 'JED', 'BAH', CURDATE(), '17:00:00', '19:15:00', 'Airbus A320', 150, 140, 119.99, 'Gulf Air'),
('GF019', 'Muscat', 'Manama', 'MCT', 'BAH', CURDATE(), '10:30:00', '12:00:00', 'Airbus A320', 150, 135, 109.99, 'Gulf Air'),
('GF020', 'Cairo', 'Manama', 'CAI', 'BAH', CURDATE(), '19:45:00', '22:15:00', 'Airbus A321', 180, 160, 159.99, 'Gulf Air'),
('GF021', 'Beirut', 'Manama', 'BEY', 'BAH', DATE_ADD(CURDATE(), INTERVAL 1 DAY), '17:30:00', '20:00:00', 'Boeing 737', 160, 145, 149.99, 'Gulf Air'),
('GF022', 'Istanbul', 'Manama', 'IST', 'BAH', DATE_ADD(CURDATE(), INTERVAL 2 DAY), '07:45:00', '12:00:00', 'Boeing 737', 160, 140, 199.99, 'Gulf Air'),

-- WIDER INTERNATIONAL FLIGHTS
('GF023', 'Manama', 'Frankfurt', 'BAH', 'FRA', DATE_ADD(CURDATE(), INTERVAL 6 DAY), '04:30:00', '10:00:00', 'Boeing 787', 280, 250, 499.99, 'Gulf Air'),
('GF024', 'Manama', 'Bangkok', 'BAH', 'BKK', DATE_ADD(CURDATE(), INTERVAL 7 DAY), '23:00:00', '07:45:00', 'Boeing 787', 280, 245, 599.99, 'Gulf Air'),
('GF025', 'Manama', 'Delhi', 'BAH', 'DEL', DATE_ADD(CURDATE(), INTERVAL 8 DAY), '16:20:00', '21:15:00', 'Airbus A321', 180, 160, 219.99, 'Gulf Air'),
('GF026', 'Delhi', 'Manama', 'DEL', 'BAH', DATE_ADD(CURDATE(), INTERVAL 9 DAY), '01:15:00', '05:30:00', 'Airbus A321', 180, 155, 219.99, 'Gulf Air'),

-- ADDITIONAL REGIONAL AIRLINES
('KU101', 'Kuwait City', 'Manama', 'KWI', 'BAH', DATE_ADD(CURDATE(), INTERVAL 1 DAY), '09:30:00', '10:45:00', 'Airbus A320', 150, 140, 84.99, 'Kuwait Airways'),
('KU102', 'Manama', 'Kuwait City', 'BAH', 'KWI', DATE_ADD(CURDATE(), INTERVAL 1 DAY), '11:30:00', '12:45:00', 'Airbus A320', 150, 140, 84.99, 'Kuwait Airways'),
('QR105', 'Doha', 'Manama', 'DOH', 'BAH', DATE_ADD(CURDATE(), INTERVAL 2 DAY), '10:00:00', '11:00:00', 'Airbus A320', 150, 135, 75.99, 'Qatar Airways'),
('QR106', 'Manama', 'Doha', 'BAH', 'DOH', DATE_ADD(CURDATE(), INTERVAL 2 DAY), '13:30:00', '14:30:00', 'Airbus A320', 150, 135, 75.99, 'Qatar Airways'),

-- LONG HAUL – GULF AIR AND OTHERS
('GF030', 'Manama', 'Singapore', 'BAH', 'SIN', DATE_ADD(CURDATE(), INTERVAL 10 DAY), '22:10:00', '09:00:00', 'Boeing 787', 280, 250, 699.99, 'Gulf Air'),
('GF031', 'Singapore', 'Manama', 'SIN', 'BAH', DATE_ADD(CURDATE(), INTERVAL 11 DAY), '22:55:00', '04:35:00', 'Boeing 787', 280, 250, 699.99, 'Gulf Air'),
('BA301', 'Manama', 'London', 'BAH', 'LHR', DATE_ADD(CURDATE(), INTERVAL 12 DAY), '02:45:00', '08:30:00', 'Boeing 787', 280, 240, 689.99, 'British Airways'),
('BA302', 'London', 'Manama', 'LHR', 'BAH', DATE_ADD(CURDATE(), INTERVAL 13 DAY), '22:00:00', '06:00:00', 'Boeing 787', 280, 235, 689.99, 'British Airways'),
('LH401', 'Frankfurt', 'Manama', 'FRA', 'BAH', DATE_ADD(CURDATE(), INTERVAL 14 DAY), '14:00:00', '20:30:00', 'Airbus A350', 300, 280, 499.99, 'Lufthansa'),
('LH402', 'Manama', 'Frankfurt', 'BAH', 'FRA', DATE_ADD(CURDATE(), INTERVAL 15 DAY), '02:10:00', '08:30:00', 'Airbus A350', 300, 275, 499.99, 'Lufthansa');

COMMIT;


-- Hotels
START TRANSACTION;
INSERT INTO `airplanned_db`.`hotels` (`hotel_name`, `location`, `star_rating`, `amenities`, `contact_info`, `price_per_night`, `availability`) VALUES 
('Four Seasons Bahrain Bay', 'Manama, Bahrain', 5, 'WiFi, Pool, Spa, Restaurant, Beach Access, Fitness Center', '+973-1711-5000', 249.99, 40),
('Gulf Hotel Bahrain', 'Manama, Bahrain', 4, 'WiFi, Pool, Restaurant, Gym, Conference Rooms', '+973-1771-3000', 129.99, 60),
('The Ritz-Carlton Bahrain', 'Manama, Bahrain', 5, 'WiFi, Private Beach, Spa, Multiple Restaurants, Pool', '+973-1758-0000', 399.99, 25),
('The St. Regis Doha', 'Doha, Qatar', 5, 'WiFi, Pool, Spa, Fine Dining, Business Center, Butler Service', '+974-4446-0000', 299.99, 35),
('Conrad Dubai', 'Dubai, UAE', 5, 'WiFi, Pool, Spa, Rooftop Bar, Fitness Center', '+971-4-444-3444', 199.99, 50),
('Atlantis The Palm Dubai', 'Dubai, UAE', 5, 'WiFi, Aquaventure Waterpark, Dolphin Bay, Multiple Restaurants', '+971-4-426-2000', 349.99, 35),
('The Regency Kuwait', 'Kuwait City, Kuwait', 5, 'WiFi, Pool, Spa, Multiple Restaurants, Business Center', '+965-2572-2222', 179.99, 40),
('Four Seasons Riyadh', 'Riyadh, Saudi Arabia', 5, 'WiFi, Pool, Spa, Fine Dining, Business Center', '+966-11-215-0000', 229.99, 35);
COMMIT;

-- Car Rentals
START TRANSACTION;
INSERT INTO `airplanned_db`.`car_rentals` (`company_name`, `location`, `car_types`, `availability`, `contact_info`, `price_per_day`) VALUES 
('Avis Bahrain', 'Bahrain International Airport', 'Economy (Toyota Corolla), Compact (Honda Civic), Mid-size (Nissan Altima), SUV (Ford Explorer)', 31, '+973-1732-2200', 35.99),
('Hertz Bahrain', 'Manama City Center', 'Economy (Hyundai Elantra), Compact (Honda Civic), Luxury (BMW 3 Series)', 25, '+973-1732-3300', 42.99),
('Europcar Qatar', 'Hamad International Airport', 'Economy (Toyota Corolla), Full-size (Toyota Camry), Luxury (BMW 3 Series)', 28, '+974-4010-6666', 65.99),
('Enterprise UAE', 'Dubai International Airport', 'Economy (Toyota Corolla), SUV (Ford Explorer), Luxury (Mercedes E-Class)', 35, '+971-4-224-5555', 89.99),
('Thrifty Kuwait', 'Kuwait International Airport', 'Economy (Hyundai Elantra), Compact (Honda Civic), Mid-size (Toyota Camry)', 30, '+965-2434-5500', 45.99),
('Budget Saudi', 'King Khalid International Airport', 'Economy (Hyundai Elantra), SUV (Toyota Prado), Luxury (Mercedes C-Class)', 18, '+966-11-221-7700', 69.99);
COMMIT;

-- Sample Bookings
START TRANSACTION;
INSERT INTO `airplanned_db`.`flight_bookings` (`user_id`, `flight_id`, `seat_number`, `total_amount`, `passenger_name`, `passenger_email`, `passenger_phone`, `payment_status`) VALUES 
(1, 1, '12A', 89.99, 'Ahmed Al-Khalifa', 'ahmed.alkhalifa@example.com', '+973-3333-1111', 'Paid'),
(2, 3, '15B', 65.99, 'Fatima Al-Zahra', 'fatima.alzahra@example.com', '+973-3333-2222', 'Pending'),
(3, 9, '8C', 95.99, 'Mohammed bin Rashid', 'mohammed.binrashid@example.com', '+971-5555-3333', 'Paid');
COMMIT;

-- Support Tickets
START TRANSACTION;
INSERT INTO `airplanned_db`.`support_tickets` (`user_id`, `subject`, `description`, `status`) VALUES 
(1, 'Flight Seat Change Request', 'I would like to change my seat from 12A to a window seat if possible.', 'Open'),
(2, 'Payment Issue', 'My payment is showing as pending but the amount has been deducted from my account.', 'In Progress'),
(3, 'Hotel Booking Confirmation', 'I have not received my hotel booking confirmation email.', 'Resolved');
COMMIT;

-- Add compatibility fields for app.py
START TRANSACTION;
ALTER TABLE users 
ADD COLUMN full_name VARCHAR(100) GENERATED ALWAYS AS (CONCAT(first_name, ' ', last_name)) STORED,
ADD COLUMN password_hash VARCHAR(255) GENERATED ALWAYS AS (password) STORED,
ADD COLUMN registration_date DATE GENERATED ALWAYS AS (DATE(created_at)) STORED;
COMMIT;

-- Final Message
SELECT 'AirPlanned Database Setup Complete!' as 'Status',
       (SELECT COUNT(*) FROM flights) as 'Total_Flights',
       (SELECT COUNT(*) FROM hotels) as 'Total_Hotels',
       (SELECT COUNT(*) FROM users) as 'Test_Users';

SELECT 'Today\'s Available Flights:' as 'Ready_For_Testing';
SELECT flight_number, origin_country, destination_country, departure_time, airline, available_seats, price 
FROM flights 
WHERE departure_date = CURDATE() 
ORDER BY departure_time;

-- =====================================================
-- READY FOR YOUR APP.PY!
-- =====================================================