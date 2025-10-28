-- Create the database, ensure it can handle unicode & emojis
CREATE DATABASE IF NOT EXISTS moffatbay CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Switch to it
USE moffatbay;

-- Create user - REPLACE THE PLACEHOLDERS and then uncomment
CREATE USER IF NOT EXISTS 'PLACEHOLDER_USER'@'localhost' IDENTIFIED BY 'PLACEHOLDER_PASSWORD';
GRANT ALL PRIVILEGES ON moffatbay.* TO 'PLACEHOLDER_USER'@'localhost';
FLUSH PRIVILEGES;