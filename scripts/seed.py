"""
Seed the Aqua database with starter data.

Prerequisites:
  1. Run scripts/init_mysql.sql in phpMyAdmin or MySQL CLI
  2. Activate the virtual environment and install requirements

Usage:
  python scripts/seed.py
  python scripts/seed.py --admin-user admin --admin-password admin123
  python scripts/seed.py --force
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

import pymysql
from werkzeug.security import generate_password_hash

try:
    from instance.config import (
        MYSQL_HOST,
        MYSQL_PORT,
        MYSQL_USER,
        MYSQL_PASSWORD,
        MYSQL_DATABASE,
    )
except ImportError:
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "aqua_db")


def get_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor,
    )


def seed_admin(cur, username: str, password: str) -> None:
    cur.execute("SELECT id FROM admins WHERE username = %s", (username,))
    if cur.fetchone():
        print(f'Skipped admin "{username}" (already exists).')
        return

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
        ON DUPLICATE KEY UPDATE
            max_weight_kg = VALUES(max_weight_kg),
            base_price = VALUES(base_price),
            extra_per_kg = VALUES(extra_per_kg)
        """
    )
    print("Seeded delivery settings.")


def table_count(cur, table: str) -> int:
    cur.execute(f"SELECT COUNT(*) AS count FROM {table}")
    return int(cur.fetchone()["count"])


def seed_plants(cur) -> None:
    plants = [
        {
            "name": "Java Moss",
            "price": 850.00,
            "category": "Moss",
            "weight": "portion",
            "description": "Easy foreground moss for beginners. Attach to driftwood or rocks.",
            "care_level": "Easy",
            "co2_condition": "Low",
            "light_condition": "Low",
            "in_stock": 1,
        },
        {
            "name": "Anubias Nana",
            "price": 1200.00,
            "category": "Anubias & Fern",
            "weight": "pot",
            "description": "Hardy epiphyte plant. Do not bury the rhizome.",
            "care_level": "Easy",
            "co2_condition": "Low",
            "light_condition": "Low",
            "in_stock": 1,
        },
        {
            "name": "Dwarf Hairgrass",
            "price": 950.00,
            "category": "Carpeting plant",
            "weight": "pot",
            "description": "Popular carpeting plant for aquascapes.",
            "care_level": "Medium",
            "co2_condition": "Medium",
            "light_condition": "High",
            "in_stock": 1,
        },
    ]

    for plant in plants:
        cur.execute(
            """
            INSERT INTO plants (
                name, price, category, weight, description,
                care_level, co2_condition, light_condition, in_stock
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                plant["name"],
                plant["price"],
                plant["category"],
                plant["weight"],
                plant["description"],
                plant["care_level"],
                plant["co2_condition"],
                plant["light_condition"],
                plant["in_stock"],
            ),
        )
    print(f"Seeded {len(plants)} plants.")


def seed_tools(cur) -> None:
    tools = [
        {
            "name": "Aquarium Net - Small",
            "price": 450.00,
            "category": "Other product",
            "weight": "1 pc",
            "description": "Fine mesh net for shrimp and small fish.",
            "in_stock": 1,
        },
        {
            "name": "Glass Algae Scraper",
            "price": 1800.00,
            "category": "Other product",
            "weight": "1 pc",
            "description": "Magnetic scraper for aquarium glass cleaning.",
            "in_stock": 1,
        },
    ]

    for tool in tools:
        cur.execute(
            """
            INSERT INTO tools (name, price, category, weight, description, in_stock)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                tool["name"],
                tool["price"],
                tool["category"],
                tool["weight"],
                tool["description"],
                tool["in_stock"],
            ),
        )
    print(f"Seeded {len(tools)} tools.")


def seed_foods(cur) -> None:
    foods = [
        {
            "name": "Tropical Flakes",
            "price": 650.00,
            "category": "Flakes",
            "weight": "50 g",
            "description": "Daily flake food for community tropical fish.",
            "in_stock": 1,
        },
        {
            "name": "Shrimp Pellets",
            "price": 900.00,
            "category": "Pellets",
            "weight": "30 g",
            "description": "Sinking pellets for shrimp and bottom feeders.",
            "in_stock": 1,
        },
    ]

    for food in foods:
        cur.execute(
            """
            INSERT INTO foods (name, price, category, weight, description, in_stock)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                food["name"],
                food["price"],
                food["category"],
                food["weight"],
                food["description"],
                food["in_stock"],
            ),
        )
    print(f"Seeded {len(foods)} foods.")


def seed_catalog(cur, force: bool) -> None:
    for table, seed_fn in (
        ("plants", seed_plants),
        ("tools", seed_tools),
        ("foods", seed_foods),
    ):
        count = table_count(cur, table)
        if count and not force:
            print(f"Skipped {table} ({count} row(s) already exist). Use --force to add more.")
            continue
        seed_fn(cur)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the Aqua database.")
    parser.add_argument("--admin-user", default="admin", help="Admin username (default: admin)")
    parser.add_argument(
        "--admin-password",
        default="admin123",
        help="Admin password (default: admin123)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Insert sample products even when tables already have rows",
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
            seed_delivery_settings(cur)
            seed_admin(cur, args.admin_user, args.admin_password)
            seed_catalog(cur, args.force)
        conn.commit()
    except Exception as exc:
        conn.rollback()
        print(f"ERROR: {exc}")
        return 1
    finally:
        conn.close()

    print("Seed completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
