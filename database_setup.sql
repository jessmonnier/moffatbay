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