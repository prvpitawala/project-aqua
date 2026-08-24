-- AquaStore database schema (aqua_db)
--
-- Run this once in phpMyAdmin or the MySQL CLI before seeding:
--   mysql -u root < scripts/init_mysql.sql
--
-- Then populate demo data:
--   python scripts/seed.py --reset
--
-- Create admin users with hashed passwords (do not insert plain text):
--   python scripts/create_admin.py admin admin123

CREATE DATABASE IF NOT EXISTS aqua_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE aqua_db;

-- ---------------------------------------------------------------------------
-- Admin authentication
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Catalog: aquatic plants
-- Categories: Anubias & Fern, Background Plant, Bucephalandra, Carpeting plant,
-- Cryptocoryne, Epiphyte plants, Floating plants, Ludwigia Varieties,
-- Midground Plant, Moss, Rare plants, Rotala Varieties, Other
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS plants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    category VARCHAR(80) NOT NULL,
    weight VARCHAR(80) DEFAULT NULL,
    image1 LONGBLOB,
    image1_type VARCHAR(20) DEFAULT NULL,
    image2 LONGBLOB,
    image2_type VARCHAR(20) DEFAULT NULL,
    image3 LONGBLOB,
    image3_type VARCHAR(20) DEFAULT NULL,
    description TEXT,
    care_level VARCHAR(40) DEFAULT NULL,
    co2_condition VARCHAR(40) DEFAULT NULL,
    light_condition VARCHAR(40) DEFAULT NULL,
    in_stock TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Catalog: tools / accessories
-- Categories: Aquarium Soil, water Pump, Filter Media, CO2 accessaries,
-- Fertilizers & Treatment, Temperature accessories, Air pumps, Other product
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tools (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    category VARCHAR(80) NOT NULL,
    weight VARCHAR(80) DEFAULT NULL,
    image1 LONGBLOB,
    image1_type VARCHAR(20) DEFAULT NULL,
    image2 LONGBLOB,
    image2_type VARCHAR(20) DEFAULT NULL,
    image3 LONGBLOB,
    image3_type VARCHAR(20) DEFAULT NULL,
    description TEXT,
    in_stock TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Catalog: fish food
-- Categories: Flakes, Pellets, Freeze-dried, Treats
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS foods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    category VARCHAR(80) NOT NULL,
    weight VARCHAR(80) DEFAULT NULL,
    image1 LONGBLOB,
    image1_type VARCHAR(20) DEFAULT NULL,
    image2 LONGBLOB,
    image2_type VARCHAR(20) DEFAULT NULL,
    image3 LONGBLOB,
    image3_type VARCHAR(20) DEFAULT NULL,
    description TEXT,
    in_stock TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Catalog document attachments (admin uploads: PDF, TXT, CSV, etc.)
-- product_type: plant | tool | food
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_type VARCHAR(20) NOT NULL,
    product_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(100) DEFAULT NULL,
    file_size INT NOT NULL DEFAULT 0,
    file_data LONGBLOB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_product (product_type, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Delivery pricing (cart + checkout)
-- Up to max_weight_kg costs base_price; each extra full kg adds extra_per_kg
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS delivery_base_per_kg (
    id INT AUTO_INCREMENT PRIMARY KEY,
    max_weight_kg DECIMAL(10, 2) NOT NULL DEFAULT 1.50,
    base_price DECIMAL(10, 2) NOT NULL DEFAULT 450.00,
    extra_per_kg DECIMAL(10, 2) NOT NULL DEFAULT 100.00,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO delivery_base_per_kg (id, max_weight_kg, base_price, extra_per_kg)
VALUES (1, 1.50, 450.00, 100.00);

-- ---------------------------------------------------------------------------
-- Contact form messages
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contact_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL,
    subject VARCHAR(300) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Customer orders (checkout)
-- status: pending | completed
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(200) NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(50) DEFAULT NULL,
    delivery_address TEXT DEFAULT NULL,
    notes TEXT DEFAULT NULL,
    subtotal DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    delivery_fee DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    total DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(40) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_type VARCHAR(20) NOT NULL,
    product_id INT NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    line_total DECIMAL(10, 2) NOT NULL,
    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- Notes
-- ---------------------------------------------------------------------------
-- Product images are stored as LONGBLOB in image1..image3 (served by Flask routes).
-- For large uploads, increase MySQL max_allowed_packet if needed:
--   SET GLOBAL max_allowed_packet = 67108864;  -- 64 MB
