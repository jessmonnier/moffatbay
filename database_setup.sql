-- Create the database, ensure it can handle unicode & emojis
CREATE DATABASE IF NOT EXISTS moffatbay CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Switch to it
USE moffatbay;

-- Create user - REPLACE THE PLACEHOLDERS and then uncomment
CREATE USER IF NOT EXISTS 'PLACEHOLDER_USER'@'localhost' IDENTIFIED BY 'PLACEHOLDER_PASSWORD';
GRANT ALL PRIVILEGES ON moffatbay.* TO 'PLACEHOLDER_USER'@'localhost';
FLUSH PRIVILEGES;


-- Billing Method Table
DROP TABLE IF EXISTS billing_methods;
CREATE TABLE billing_methods(
	billingID int primary key auto_increment,
    customer_id int not null,
    type ENUM('Paypal','Apple Pay','Cash App','Credit Card','Shop','Other') not null, -- Fixed Payment methods
    name varchar(48)
	
  CONSTRAINT fk_billing_customer
		FOREIGN KEY (customer_id) REFERENCES customers(customerId)
        -- If customer updates or deletes information automatically update and delete
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- Rooms Table
CREATE TABLE IF NOT EXISTS rooms (
    roomId INT PRIMARY KEY AUTO_INCREMENT,                   -- Unique ID for each room (auto-incremented)
    room_number VARCHAR(10) NOT NULL UNIQUE,                 -- Room label or number (e.g., "101", "A-12")
    room_type ENUM('Single', 'Double', 'Queen', 'King', 'Suite') NOT NULL, -- Room category or bed size
    beds TINYINT UNSIGNED NOT NULL DEFAULT 1,                -- Number of beds in the room
    max_occupancy TINYINT UNSIGNED NOT NULL DEFAULT 2,       -- Maximum number of guests allowed
    rate_per_night DECIMAL(10,2) NOT NULL,                   -- Cost per night (used to calculate total stay charges)
    description TEXT,                                        -- Optional description (e.g., "Ocean view with balcony")
    status ENUM('Available', 'Occupied', 'Cleaning', 'Maintenance') 
           NOT NULL DEFAULT 'Available',                     -- Current room status (for availability tracking)
    amenities VARCHAR(255),                                  -- Optional list of amenities (e.g., "WiFi, Mini-fridge, TV")
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,          -- Date/time the record was created
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
               ON UPDATE CURRENT_TIMESTAMP                   -- Automatically updates when record changes
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
