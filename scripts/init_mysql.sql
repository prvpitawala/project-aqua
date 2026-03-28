-- Create database (run in MySQL/phpMyAdmin)
CREATE DATABASE IF NOT EXISTS aqua_db;
USE aqua_db;

-- Admin users table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Plants (Anubias & Fern, Background Plant, Bucephalandra, Carpeting plant, Cryptocoryne, Epiphyte plants, Floating plants, Ludwigia Varieties, Midground Plant, Moss, Rare plants, Rotala Varieties, Other)
CREATE TABLE IF NOT EXISTS plants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10, 2) NOT NULL DEFAULT 0,
    category VARCHAR(80) NOT NULL,
    weight VARCHAR(80) DEFAULT NULL,
    image1 LONGBLOB,
    image1_type VARCHAR(20),
    image2 LONGBLOB,
    image2_type VARCHAR(20),
    image3 LONGBLOB,
    image3_type VARCHAR(20),
    description TEXT,
    care_level VARCHAR(40) DEFAULT NULL,
    co2_condition VARCHAR(40) DEFAULT NULL,
    light_condition VARCHAR(40) DEFAULT NULL,
    in_stock TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tools (test kits, nets, scrapers, etc.)
CREATE TABLE IF NOT EXISTS tools (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10, 2) NOT NULL DEFAULT 0,
    category VARCHAR(80) NOT NULL,
    weight VARCHAR(80) DEFAULT NULL,
    image1 LONGBLOB,
    image1_type VARCHAR(20),
    image2 LONGBLOB,
    image2_type VARCHAR(20),
    image3 LONGBLOB,
    image3_type VARCHAR(20),
    description TEXT,
    in_stock TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Foods (Flakes, Pellets, Freeze-dried, Treats)
CREATE TABLE IF NOT EXISTS foods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10, 2) NOT NULL DEFAULT 0,
    category VARCHAR(80) NOT NULL,
    weight VARCHAR(80) DEFAULT NULL,
    image1 LONGBLOB,
    image1_type VARCHAR(20),
    image2 LONGBLOB,
    image2_type VARCHAR(20),
    image3 LONGBLOB,
    image3_type VARCHAR(20),
    description TEXT,
    in_stock TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weight-based delivery: only up to weight (kg), base price (LKR), per extra kg (LKR)
CREATE TABLE IF NOT EXISTS delivery_base_per_kg (
    id INT AUTO_INCREMENT PRIMARY KEY,
    max_weight_kg DECIMAL(10, 2) NOT NULL DEFAULT 1.5,
    base_price DECIMAL(10, 2) NOT NULL DEFAULT 450,
    extra_per_kg DECIMAL(10, 2) NOT NULL DEFAULT 100,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
INSERT IGNORE INTO delivery_base_per_kg (id, max_weight_kg, base_price, extra_per_kg) VALUES (1, 1.5, 450, 100);

-- Contact messages
CREATE TABLE IF NOT EXISTS contact_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL,
    subject VARCHAR(300) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- High-quality images: LONGBLOB supports up to 4 GB per image.
-- If uploading very large images, increase MySQL max_allowed_packet:
--   SET GLOBAL max_allowed_packet = 67108864;  -- 64 MB
--
-- Add weight column to existing tables (run if tables already exist):
-- ALTER TABLE plants ADD COLUMN weight VARCHAR(80) DEFAULT NULL AFTER category;
-- ALTER TABLE tools ADD COLUMN weight VARCHAR(80) DEFAULT NULL AFTER category;
-- ALTER TABLE foods ADD COLUMN weight VARCHAR(80) DEFAULT NULL AFTER category;
--
-- Add in_stock column (run if tables already exist):
-- ALTER TABLE plants ADD COLUMN in_stock TINYINT(1) NOT NULL DEFAULT 1 AFTER description;
-- ALTER TABLE tools ADD COLUMN in_stock TINYINT(1) NOT NULL DEFAULT 1 AFTER description;
-- ALTER TABLE foods ADD COLUMN in_stock TINYINT(1) NOT NULL DEFAULT 1 AFTER description;
--
-- Add care_level column to plants (run if table already exists):
-- ALTER TABLE plants ADD COLUMN care_level VARCHAR(40) DEFAULT NULL AFTER description;
--
-- Add co2_condition and light_condition to plants (run if table already exists):
-- ALTER TABLE plants ADD COLUMN co2_condition VARCHAR(40) DEFAULT NULL AFTER care_level;
-- ALTER TABLE plants ADD COLUMN light_condition VARCHAR(40) DEFAULT NULL AFTER co2_condition;
--
-- Note: Use create_admin.py to add admin users with hashed passwords.
-- Do NOT store plain passwords in the database.
