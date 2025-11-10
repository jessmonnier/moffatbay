-- Create the database, ensure it can handle unicode & emojis
CREATE DATABASE IF NOT EXISTS moffatbay CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Switch to it
USE moffatbay;

-- Create user - REPLACE THE PLACEHOLDERS and then uncomment
CREATE USER IF NOT EXISTS 'PLACEHOLDER_USER'@'localhost' IDENTIFIED BY 'PLACEHOLDER_PASSWORD';
GRANT ALL PRIVILEGES ON moffatbay.* TO 'PLACEHOLDER_USER'@'localhost';
FLUSH PRIVILEGES;

-- Disable FK checks temporarily so all drops succeed
SET FOREIGN_KEY_CHECKS = 0;

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS reservations;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS room_types;
DROP TABLE IF EXISTS billing_methods;
DROP TABLE IF EXISTS customers;

-- Re-enable FK checks
SET FOREIGN_KEY_CHECKS = 1;

-- Customers table
CREATE TABLE customers(
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(35) NOT NULL,
    last_name VARCHAR(35) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    phone_number VARCHAR(25) NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    address_country VARCHAR(35),
    address_street VARCHAR(254),
    address_city VARCHAR(35),
    address_state VARCHAR(35),
    address_zipcode VARCHAR(25),
    default_billing_id INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Billing Method Table
CREATE TABLE billing_methods(
	billing_id int primary key auto_increment,
    customer_id int not null,
    type ENUM('Paypal','Apple Pay','Cash App','Credit Card','Gift Card') not null, -- Fixed Payment methods
    name varchar(48),
    address_country VARCHAR(35),
    address_street VARCHAR(254),
    address_city VARCHAR(35),
    address_state VARCHAR(35),
    address_zipcode VARCHAR(25),
	
  CONSTRAINT fk_billing_customer
		FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        -- If customer updates or deletes information automatically update and delete
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Set up foreign key relationship between customers table and default_billing_id
ALTER TABLE customers
ADD CONSTRAINT fk_default_billing
FOREIGN KEY (default_billing_id)
REFERENCES billing_methods(billing_id)
ON DELETE SET NULL;

-- Room Types table
CREATE TABLE room_types(
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(25) NOT NULL,
    price_per_night DECIMAL(7,2) NOT NULL,
    beds INT NOT NULL,
    max_guests INT NOT NULL,
    description TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Rooms Table
CREATE TABLE rooms (
    room_id INT PRIMARY KEY AUTO_INCREMENT,
    room_number VARCHAR(20) NOT NULL UNIQUE,
    room_type INT,
    status ENUM('Available', 'Occupied', 'Cleaning', 'Maintenance') 
           NOT NULL DEFAULT 'Available',                     -- Current room status (for availability tracking)
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
               ON UPDATE CURRENT_TIMESTAMP,                   -- Automatically updates when record changes

CONSTRAINT fk_room_type
		FOREIGN KEY (room_type) REFERENCES room_types(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Reservations Table
CREATE TABLE reservations(
    reservation_id CHAR(36) PRIMARY KEY DEFAULT (UUID()), -- make a better user-facing res ID
    customer_id INT,
    guest_first_name VARCHAR(35) NOT NULL,                -- by default these guest fields will auto-populate
    guest_last_name VARCHAR(35) NOT NULL,                 -- in the web app, but gives option to change them
    guest_phone VARCHAR(25) NOT NULL,
    guest_email VARCHAR(254) NOT NULL,
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    expiration_time DATETIME,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
               ON UPDATE CURRENT_TIMESTAMP,
    status ENUM('Hold', 'Confirmed', 'Cancelled')
            NOT NULL DEFAULT 'Hold',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    room_type INT,
    room_id INT,

  CONSTRAINT fk_reservation_customer_id
		FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        ON DELETE NO ACTION         -- set null is handled by trigger later in script
        ON UPDATE CASCADE,
  CONSTRAINT fk_reservation_room_type
		FOREIGN KEY (room_type) REFERENCES room_types(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
  CONSTRAINT fk_reservation_room_id
		FOREIGN KEY (room_id) REFERENCES rooms(room_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Trigger: automatically cancel reservations if a customer is deleted
DELIMITER $$

CREATE TRIGGER trg_cancel_reservations_on_customer_delete
BEFORE DELETE ON customers
FOR EACH ROW
BEGIN
  UPDATE reservations
  SET status = 'Cancelled', customer_id = NULL
  WHERE customer_id = OLD.customer_id;
END$$

DELIMITER ;

-- Populate the database; data largely generated by ChatGPT but adjusted to match TDD

-- Customers first; has one circular foreign key but we can skip it for now
INSERT INTO customers
(first_name, last_name, email, phone_number, password_hash, 
 address_country, address_street, address_city, address_state, address_zipcode)
VALUES
('Brian', 'Murphy', 'brian.murphy@example.com', '555-210-9982',
 'HASHEDPASS123456', 'USA', '102 Beach Ave', 'San Juan Island', 'WA', '98250'),
('Maria', 'Lopez', 'maria.lopez@example.com', '555-334-1122',
 'HASHEDPASSABCDE', 'USA', '44 Harbor View Rd', 'Friday Harbor', 'WA', '98250'),
('Carla', 'Mendoza', 'carla@mendozatravel.com', '555-221-5644',
 'HASHEDPASS778899', 'USA', '900 Maple Dr', 'Seattle', 'WA', '98101');

-- Next room types since it has no dependencies
INSERT INTO room_types (name, price_per_night, beds, max_guests, description)
VALUES
('Double Full Beds', 120.00, 2, 4, 'Two full beds with island view.'),
('Queen', 135.00, 1, 2, 'Single queen bed overlooking the bay.'),
('Double Queen Beds', 150.00, 2, 4, 'Two queen beds, partial ocean view.'),
('King', 160.00, 1, 2, 'Large king room with premium amenities.');

-- Now rooms, two of each type for now
INSERT INTO rooms (room_number, room_type, status)
VALUES
('101', 1, 'Available'),
('102', 1, 'Cleaning'),

('201', 2, 'Available'),
('202', 2, 'Occupied'),

('301', 3, 'Available'),
('302', 3, 'Maintenance'),

('401', 4, 'Available'),
('402', 4, 'Occupied');

-- Reservations (has the most dependencies)
INSERT INTO reservations
(customer_id, guest_first_name, guest_last_name, guest_phone, guest_email,
 expiration_time, status, start_date, end_date, room_type, room_id)
VALUES
-- Reservation 1 (customer #1)
(1, 'Brian', 'Murphy', '555-210-9982', 'brian.murphy@example.com',
 NULL, 'Confirmed',
 '2025-06-12', '2025-06-15', 2, (select room_id from rooms where room_number = "201" limit 1)),
-- Reservation 2 (customer #2)
(2, 'Maria', 'Lopez', '555-334-1122', 'maria.lopez@example.com',
 DATE_ADD(NOW(), INTERVAL 1 DAY), 'Hold',
 '2025-07-02', '2025-07-06', 4, (select room_id from rooms where room_number = "401" limit 1)),
-- Reservation 3 (customer #3, but she's a travel agent so it's for a client)
(3, 'David', 'Chen', '555-221-5644', 'david.chen@example.com',
 NULL, 'Confirmed',
 '2025-08-20', '2025-08-25', 1, (select room_id from rooms where room_number = "101" limit 1));

 -- Add one billing method per existing customer
INSERT INTO billing_methods (customer_id, type, name, address_country, address_street, address_city, address_state, address_zipcode)
VALUES
-- Customer 1: Brian Murphy
(1, 'Credit Card', 'My Visa - ...1234', 'USA', '102 Beach Ave', 'San Juan Island', 'WA', '98250'),
-- Customer 2: Maria Lopez
(2, 'Paypal', 'Paypal', 'USA', '44 Harbor View Rd', 'Friday Harbor', 'WA', '98250'),
-- Customer 3: Carla Mendoza
(3, 'Credit Card', 'Company Visa - ...4321', 'USA', '900 Maple Dr', 'Seattle', 'WA', '98101');

-- Now update each customer's default_billing_id to the corresponding billing_id
UPDATE customers 
SET default_billing_id = (
    SELECT billing_id FROM billing_methods 
    WHERE billing_methods.customer_id = customers.customer_id
)
WHERE customer_id IN (1, 2, 3);

-- Display table contents
SELECT * FROM customers;
SELECT * FROM billing_methods;
SELECT * FROM reservations;
SELECT * FROM room_types;
SELECT * FROM rooms;