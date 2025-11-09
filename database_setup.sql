-- Create the database, ensure it can handle unicode & emojis
CREATE DATABASE IF NOT EXISTS moffatbay CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Switch to it
USE moffatbay;

-- Create user - REPLACE THE PLACEHOLDERS and then uncomment
CREATE USER IF NOT EXISTS 'PLACEHOLDER_USER'@'localhost' IDENTIFIED BY 'PLACEHOLDER_PASSWORD';
GRANT ALL PRIVILEGES ON moffatbay.* TO 'PLACEHOLDER_USER'@'localhost';
FLUSH PRIVILEGES;

-- Customers table
DROP TABLE IF EXISTS customers;
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
DROP TABLE IF EXISTS billing_methods;
CREATE TABLE billing_methods(
	billing_id int primary key auto_increment,
    customer_id int not null,
    type ENUM('Paypal','Apple Pay','Cash App','Credit Card','Shop') not null, -- Fixed Payment methods
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
DROP TABLE IF EXISTS room_types;
CREATE TABLE room_types(
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(25) NOT NULL,
    price_per_night DECIMAL(7,2) NOT NULL,
    beds INT NOT NULL,
    max_guests INT NOT NULL,
    description TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Rooms Table
DROP TABLE IF EXISTS rooms;
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
DROP TABLE IF EXISTS reservations;
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
        ON DELETE SET NULL
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