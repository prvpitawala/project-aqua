"""
Import real product data and images from minipuraaqua.lk into aqua_db.

Uses the public WooCommerce Store API:
  https://minipuraaqua.lk/wp-json/wc/store/v1/products

For a full seed with sample orders and contact messages, prefer:
  python scripts/seed.py --reset

Usage:
  python scripts/import_minipura.py
  python scripts/import_minipura.py --count 50
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

import pymysql
from werkzeug.security import generate_password_hash

from scripts.minipura_sources import (
    BASE_URL,
    DEFAULT_COUNT,
    build_product_description,
    download_image,
    fetch_products,
    pick_care_level,
    pick_food_category,
    pick_plant_category,
    pick_tag_value,
    pick_tool_category,
    pick_weight,
    price_lkr,
    product_image_url,
    strip_html,
    tag_slugs,
    CO2_TAGS,
    LIGHT_TAGS,
)

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


def get_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor,
    )


def safe_print(message: str) -> None:
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode("ascii", "replace").decode("ascii"))


def reset_tables(cur) -> None:
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in ("order_items", "orders", "contact_messages", "plants", "tools", "foods", "admins", "delivery_base_per_kg"):
        cur.execute(f"TRUNCATE TABLE {table}")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")


def seed_support_tables(cur, admin_user: str, admin_password: str) -> None:
    cur.execute(
        """
        INSERT INTO delivery_base_per_kg (id, max_weight_kg, base_price, extra_per_kg)
        VALUES (1, 1.50, 450.00, 100.00)
        """
    )
    cur.execute(
        "INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
        (admin_user, generate_password_hash(admin_password)),
    )


def insert_plant(cur, product: dict, image_data: bytes, image_type: str) -> None:
    tags = tag_slugs(product)
    cur.execute(
        """
        INSERT INTO plants (
            name, price, category, weight, description,
            care_level, co2_condition, light_condition,
            image1, image1_type, in_stock
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            strip_html(product["name"]),
            price_lkr(product),
            pick_plant_category(product),
            pick_weight(product),
            build_product_description(product),
            pick_care_level(product),
            pick_tag_value(tags, CO2_TAGS),
            pick_tag_value(tags, LIGHT_TAGS),
            image_data,
            image_type,
            1 if product.get("is_in_stock") else 0,
        ),
    )


def insert_tool(cur, product: dict, image_data: bytes, image_type: str) -> None:
    cur.execute(
        """
        INSERT INTO tools (
            name, price, category, weight, description,
            image1, image1_type, in_stock
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            strip_html(product["name"]),
            price_lkr(product),
            pick_tool_category(product),
            pick_weight(product),
            build_product_description(product),
            image_data,
            image_type,
            1 if product.get("is_in_stock") else 0,
        ),
    )


def insert_food(cur, product: dict, image_data: bytes, image_type: str) -> None:
    name = strip_html(product["name"])
    cur.execute(
        """
        INSERT INTO foods (
            name, price, category, weight, description,
            image1, image1_type, in_stock
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            name,
            price_lkr(product),
            pick_food_category(name),
            pick_weight(product),
            build_product_description(product),
            image_data,
            image_type,
            1 if product.get("is_in_stock") else 0,
        ),
    )


def import_group(cur, label: str, products: list[dict], insert_fn) -> int:
    imported = 0
    for index, product in enumerate(products, start=1):
        image_url = product_image_url(product)
        try:
            image_data, image_type = download_image(image_url)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"  Warning: skipped image for {product['name'][:50]}: {exc}")
            continue

        insert_fn(cur, product, image_data, image_type)
        imported += 1
        safe_print(
            f"  [{label}] {index}/{len(products)} {strip_html(product['name'])[:60]} ({len(image_data)} bytes)"
        )
        time.sleep(0.15)

    return imported


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Import products from minipuraaqua.lk")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help="Items per table (default: 50)")
    parser.add_argument("--admin-user", default="admin")
    parser.add_argument("--admin-password", default="admin123")
    args = parser.parse_args()

    print(f"Fetching up to {args.count} products per category from {BASE_URL} ...")
    try:
        plants = fetch_products("aqua-plants", args.count)
        foods = fetch_products("fish-feed", args.count)
        tools = fetch_products("aquascaping-product", args.count, exclude_slugs={"fish-feed"})
    except Exception as exc:
        print(f"ERROR: Could not fetch products: {exc}")
        return 1

    print(f"Found {len(plants)} plants, {len(tools)} tools, {len(foods)} foods")

    if not plants or not tools or not foods:
        print("ERROR: Not enough products returned from the store API.")
        return 1

    try:
        conn = get_connection()
    except Exception as exc:
        print(f"ERROR: Database connection failed: {exc}")
        return 1

    try:
        with conn.cursor() as cur:
            reset_tables(cur)
            seed_support_tables(cur, args.admin_user, args.admin_password)
            print("Importing plants...")
            plant_count = import_group(cur, "plant", plants, insert_plant)
            print("Importing tools/accessories...")
            tool_count = import_group(cur, "tool", tools, insert_tool)
            print("Importing foods...")
            food_count = import_group(cur, "food", foods, insert_food)
        conn.commit()
    except Exception as exc:
        conn.rollback()
        print(f"ERROR: {exc}")
        return 1
    finally:
        conn.close()

    print("Import completed.")
    print(f"  plants: {plant_count}")
    print(f"  tools:  {tool_count}")
    print(f"  foods:  {food_count}")
    print(f"  admin:  {args.admin_user} / {args.admin_password}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
