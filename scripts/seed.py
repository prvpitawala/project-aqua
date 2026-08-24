"""
Seed the Aqua database with full demo data.

Prerequisites:
  1. Run scripts/init_mysql.sql in phpMyAdmin or MySQL CLI
  2. Activate the virtual environment and install requirements

Usage:
  python scripts/seed.py --reset
  python scripts/seed.py --reset --no-images
  python scripts/seed.py --admin-user admin --admin-password admin123
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

import pymysql
from werkzeug.security import generate_password_hash

try:
    from instance.config import (
        MYSQL_DATABASE,
        MYSQL_HOST,
        MYSQL_PASSWORD,
        MYSQL_PORT,
        MYSQL_USER,
    )
except ImportError:
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "aqua_db")

ITEM_COUNT = 50

PLANT_CATEGORIES = [
    "Anubias & Fern",
    "Background Plant",
    "Bucephalandra",
    "Carpeting plant",
    "Cryptocoryne",
    "Epiphyte plants",
    "Floating plants",
    "Ludwigia Varieties",
    "Midground Plant",
    "Moss",
    "Rare plants",
    "Rotala Varieties",
    "Other",
]
TOOL_CATEGORIES = [
    "Aquarium Soil",
    "water Pump",
    "Filter Media",
    "CO2 accessaries",
    "Fertilizers & Treatment",
    "Temperature accessories",
    "Air pumps",
    "Other product",
]
FOOD_CATEGORIES = ["Flakes", "Pellets", "Freeze-dried", "Treats"]
CO2_OPTIONS = ["High CO2", "Medium CO2", "Low CO2"]
LIGHT_OPTIONS = ["High Light", "Medium Light", "Low Light"]
CARE_LEVELS = ["Easy care", "Medium care", "High tech"]
WEIGHTS = ["portion", "pot", "bunch", "cup", "50 g", "100 g", "1 pc", "250 ml"]

# Tiny valid JPEG used when image download is skipped or fails.
PLACEHOLDER_JPEG = bytes(
    [
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01,
        0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43, 0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
        0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20,
        0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29, 0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27,
        0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01,
        0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04,
        0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
        0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D, 0x01, 0x02, 0x03, 0x00,
        0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06, 0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32,
        0x81, 0x91, 0xA1, 0x08, 0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
        0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x34, 0x35,
        0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55,
        0x56, 0x57, 0x58, 0x59, 0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
        0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x92, 0x93, 0x94,
        0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2,
        0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
        0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6,
        0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA,
        0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD5, 0xDB, 0x20, 0xA8, 0xF1, 0x45, 0x00,
        0xFF, 0xD9,
    ]
)

_IMAGE_CACHE: dict[str, tuple[bytes, str]] = {}


def get_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor,
    )


def fetch_image(seed: str, use_network: bool) -> tuple[bytes, str]:
    if not use_network:
        return PLACEHOLDER_JPEG, "image/jpeg"
    if seed in _IMAGE_CACHE:
        return _IMAGE_CACHE[seed]

    url = f"https://picsum.photos/seed/{seed}/400/400"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "aqua-seed/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            data = response.read()
            mime = response.headers.get_content_type() or "image/jpeg"
            if data:
                _IMAGE_CACHE[seed] = (data, mime)
                return data, mime
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"  Warning: could not download image for {seed}: {exc}")

    _IMAGE_CACHE[seed] = (PLACEHOLDER_JPEG, "image/jpeg")
    return PLACEHOLDER_JPEG, "image/jpeg"


def reset_tables(cur) -> None:
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in (
        "contact_messages",
        "plants",
        "tools",
        "foods",
        "admins",
        "delivery_base_per_kg",
    ):
        cur.execute(f"TRUNCATE TABLE {table}")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    print("Cleared existing seed tables.")


def seed_admin(cur, username: str, password: str) -> None:
    cur.execute(
        "INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
        (username, generate_password_hash(password)),
    )
    print(f'Created admin user "{username}".')


def seed_delivery_settings(cur) -> None:
    cur.execute(
        """
        INSERT INTO delivery_base_per_kg (id, max_weight_kg, base_price, extra_per_kg)
        VALUES (1, 1.50, 450.00, 100.00)
        """
    )
    print("Seeded delivery settings.")


def seed_contact_messages(cur) -> None:
    base_time = datetime.now() - timedelta(days=14)
    messages = [
        ("Aqua Customer", "customer1@example.com", "Plant availability", "Do you have Anubias in stock this week?"),
        ("Sam Perera", "sam.perera@example.com", "Delivery question", "How much is delivery for a 2 kg order to Colombo?"),
        ("Nimali Jay", "nimali@example.com", "Bulk order", "Can I place a bulk order for carpeting plants?"),
        ("Ravi Kumar", "ravi@example.com", "CO2 setup", "Which accessories do you recommend for a beginner CO2 kit?"),
        ("Dilani Silva", "dilani@example.com", "Food recommendation", "What food is best for neon tetras and shrimp together?"),
        ("Guest User", "guest@example.com", "Store hours", "What are your opening hours on weekends?"),
        ("Kasun Mendis", "kasun@example.com", "Order follow-up", "I placed an order yesterday. Can you confirm dispatch?"),
        ("Ishara Fonseka", "ishara@example.com", "Plant care", "How much light does Dwarf Hairgrass need?"),
    ]
    for index, (name, email, subject, message) in enumerate(messages, start=1):
        created_at = base_time + timedelta(days=index)
        cur.execute(
            """
            INSERT INTO contact_messages (name, email, subject, message, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (name, email, subject, message, created_at),
        )
    print(f"Seeded {len(messages)} contact messages.")


def insert_catalog_item(
    cur,
    table: str,
    name: str,
    price: float,
    category: str,
    weight: str,
    description: str,
    in_stock: int,
    image_data: bytes,
    image_type: str,
    plant_fields: dict | None = None,
) -> None:
    if table == "plants" and plant_fields:
        cur.execute(
            """
            INSERT INTO plants (
                name, price, category, weight, description,
                care_level, co2_condition, light_condition,
                image1, image1_type, in_stock
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                name,
                price,
                category,
                weight,
                description,
                plant_fields["care_level"],
                plant_fields["co2_condition"],
                plant_fields["light_condition"],
                image_data,
                image_type,
                in_stock,
            ),
        )
        return

    cur.execute(
        f"""
        INSERT INTO {table} (
            name, price, category, weight, description,
            image1, image1_type, in_stock
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (name, price, category, weight, description, image_data, image_type, in_stock),
    )


def seed_plants(cur, use_images: bool) -> None:
    print(f"Seeding {ITEM_COUNT} plants...")
    for index in range(1, ITEM_COUNT + 1):
        category = PLANT_CATEGORIES[(index - 1) % len(PLANT_CATEGORIES)]
        image_data, image_type = fetch_image(f"aqua-plant-{index}", use_images)
        insert_catalog_item(
            cur,
            "plants",
            name=f"Aqua Plant {index}",
            price=round(450 + ((index - 1) % 5) * 175, 2),
            category=category,
            weight=WEIGHTS[(index - 1) % len(WEIGHTS)],
            description=(
                f"Beautiful {category.lower()} for your aquarium. "
                "Easy to care for and thrives in most water conditions."
            ),
            in_stock=0 if index % 10 == 7 else 1,
            image_data=image_data,
            image_type=image_type,
            plant_fields={
                "care_level": CARE_LEVELS[(index - 1) % len(CARE_LEVELS)],
                "co2_condition": CO2_OPTIONS[(index - 1) % len(CO2_OPTIONS)],
                "light_condition": LIGHT_OPTIONS[(index - 1) % len(LIGHT_OPTIONS)],
            },
        )
    print(f"Seeded {ITEM_COUNT} plants.")


def seed_tools(cur, use_images: bool) -> None:
    print(f"Seeding {ITEM_COUNT} tools/accessories...")
    for index in range(1, ITEM_COUNT + 1):
        category = TOOL_CATEGORIES[(index - 1) % len(TOOL_CATEGORIES)]
        image_data, image_type = fetch_image(f"aqua-tool-{index}", use_images)
        insert_catalog_item(
            cur,
            "tools",
            name=f"Aquarium Accessory {index}",
            price=round(550 + ((index - 1) % 6) * 225, 2),
            category=category,
            weight=WEIGHTS[(index - 1) % len(WEIGHTS)],
            description="Quality aquarium accessory for your tank. Reliable and durable.",
            in_stock=0 if index % 10 == 3 else 1,
            image_data=image_data,
            image_type=image_type,
        )
    print(f"Seeded {ITEM_COUNT} tools.")


def seed_foods(cur, use_images: bool) -> None:
    print(f"Seeding {ITEM_COUNT} foods...")
    for index in range(1, ITEM_COUNT + 1):
        category = FOOD_CATEGORIES[(index - 1) % len(FOOD_CATEGORIES)]
        image_data, image_type = fetch_image(f"aqua-food-{index}", use_images)
        insert_catalog_item(
            cur,
            "foods",
            name=f"Aquarium Food {index}",
            price=round(350 + ((index - 1) % 4) * 125, 2),
            category=category,
            weight=WEIGHTS[(index - 1) % len(WEIGHTS)],
            description=f"Nutritional fish food for healthy aquariums. Category: {category.lower()}.",
            in_stock=0 if index % 10 == 5 else 1,
            image_data=image_data,
            image_type=image_type,
        )
    print(f"Seeded {ITEM_COUNT} foods.")


def table_count(cur, table: str) -> int:
    cur.execute(f"SELECT COUNT(*) AS count FROM {table}")
    return int(cur.fetchone()["count"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the Aqua database.")
    parser.add_argument("--admin-user", default="admin", help="Admin username (default: admin)")
    parser.add_argument("--admin-password", default="admin123", help="Admin password (default: admin123)")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear seed tables and insert a fresh full dataset",
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Store a tiny placeholder image instead of downloading photos",
    )
    args = parser.parse_args()

    try:
        conn = get_connection()
    except Exception as exc:
        print(f"ERROR: Could not connect to MySQL: {exc}")
        print("Make sure XAMPP MySQL is running and scripts/init_mysql.sql was applied.")
        return 1

    try:
        with conn.cursor() as cur:
            if args.reset:
                reset_tables(cur)
            elif table_count(cur, "plants") >= ITEM_COUNT:
                print(
                    "Database already has seed data. Use --reset to replace it with a fresh dataset."
                )
                return 0

            if not args.reset and table_count(cur, "plants") > 0:
                print("Partial data found. Re-run with --reset for a clean full seed.")
                return 1

            seed_delivery_settings(cur)
            seed_admin(cur, args.admin_user, args.admin_password)
            seed_contact_messages(cur)
            use_images = not args.no_images
            seed_plants(cur, use_images)
            seed_tools(cur, use_images)
            seed_foods(cur, use_images)
        conn.commit()
    except Exception as exc:
        conn.rollback()
        print(f"ERROR: {exc}")
        return 1
    finally:
        conn.close()

    print("Seed completed successfully.")
    print(f"  plants: {ITEM_COUNT}")
    print(f"  tools:  {ITEM_COUNT}")
    print(f"  foods:  {ITEM_COUNT}")
    print(f"  admin:  {args.admin_user} / {args.admin_password}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
