"""
Import real product data and images from minipuraaqua.lk into aqua_db.

Uses the public WooCommerce Store API:
  https://minipuraaqua.lk/wp-json/wc/store/v1/products

Usage:
  python scripts/import_minipura.py
  python scripts/import_minipura.py --count 50
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

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

BASE_URL = "https://minipuraaqua.lk"
API_ROOT = f"{BASE_URL}/wp-json/wc/store/v1"
USER_AGENT = "aqua-import/1.0 (+local dev seed)"
DEFAULT_COUNT = 50

PLANT_CATEGORY_BY_SLUG = {
    "anubias-fern": "Anubias & Fern",
    "background-plant": "Background Plant",
    "bucephalandra": "Bucephalandra",
    "carperting-plants": "Carpeting plant",
    "cryptocoryne": "Cryptocoryne",
    "epiphyte-plant": "Epiphyte plants",
    "floating-plants": "Floating plants",
    "ludwigia-varieties": "Ludwigia Varieties",
    "midground-plant": "Midground Plant",
    "moss": "Moss",
    "rare-plants": "Rare plants",
    "rotala-varieties": "Rotala Varieties",
}

TOOL_CATEGORY_BY_SLUG = {
    "aquarium-soil-substrates": "Aquarium Soil",
    "aquarium-pump": "water Pump",
    "aquarium-filter-media": "Filter Media",
    "filters-filter-media": "Filter Media",
    "co2-accessaries": "CO2 accessaries",
    "fertilizers-treatments": "Fertilizers & Treatment",
    "temperature-accessories": "Temperature accessories",
    "air-pump-accessories": "Air pumps",
}

CARE_BY_SLUG = {
    "easy-care-plants": "Easy care",
    "medium-care-plants": "Medium care",
    "hight-tech-plants": "High tech",
}

CO2_TAGS = {"high-co2": "High CO2", "medium-co2": "Medium CO2", "low-co2": "Low CO2"}
LIGHT_TAGS = {
    "high-light": "High Light",
    "medium-light": "Medium Light",
    "low-light": "Low Light",
}


def get_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor,
    )


def strip_html(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def safe_print(message: str) -> None:
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode("ascii", "replace").decode("ascii"))


def api_get(path: str, params: dict | None = None) -> tuple[object, dict]:
    query = urllib.parse.urlencode(params or {})
    url = f"{API_ROOT}{path}"
    if query:
        url = f"{url}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.loads(response.read().decode("utf-8"))
        headers = {k.lower(): v for k, v in response.headers.items()}
        return payload, headers


def fetch_products(category_slug: str, limit: int, exclude_slugs: set[str] | None = None) -> list[dict]:
    exclude_slugs = exclude_slugs or set()
    results: list[dict] = []
    page = 1

    while len(results) < limit:
        payload, _ = api_get(
            "/products",
            {"category": category_slug, "per_page": 100, "page": page},
        )
        if not payload:
            break

        for product in payload:
            category_slugs = {cat["slug"] for cat in product.get("categories", [])}
            if category_slugs & exclude_slugs:
                continue
            if not product.get("images"):
                continue
            results.append(product)
            if len(results) >= limit:
                break

        if len(payload) < 100:
            break
        page += 1
        time.sleep(0.2)

    return results[:limit]


def download_image(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45) as response:
        data = response.read()
        mime = response.headers.get_content_type() or "image/jpeg"
        if mime not in ("image/jpeg", "image/png", "image/gif", "image/webp"):
            mime = "image/jpeg"
        return data, mime[:20]


def price_lkr(product: dict) -> float:
    prices = product.get("prices") or {}
    minor = int(prices.get("currency_minor_unit", 2))
    return round(int(prices["price"]) / (10**minor), 2)


def category_slugs(product: dict) -> set[str]:
    return {cat["slug"] for cat in product.get("categories", [])}


def tag_slugs(product: dict) -> set[str]:
    return {tag["slug"] for tag in product.get("tags", [])}


def pick_mapped_category(product: dict, mapping: dict[str, str], default: str) -> str:
    for slug, label in mapping.items():
        if slug in category_slugs(product):
            return label
    return default


def pick_plant_category(product: dict) -> str:
    return pick_mapped_category(product, PLANT_CATEGORY_BY_SLUG, "Other")


def pick_tool_category(product: dict) -> str:
    return pick_mapped_category(product, TOOL_CATEGORY_BY_SLUG, "Other product")


def pick_food_category(name: str) -> str:
    lowered = name.lower()
    if "flake" in lowered:
        return "Flakes"
    if "pellet" in lowered or "pallet" in lowered:
        return "Pellets"
    if "freeze" in lowered or "frozen" in lowered:
        return "Freeze-dried"
    if "treat" in lowered or "worm" in lowered:
        return "Treats"
    return "Pellets"


def pick_care_level(product: dict) -> str | None:
    slugs = category_slugs(product)
    for slug, label in CARE_BY_SLUG.items():
        if slug in slugs:
            return label
    return None


def pick_tag_value(tag_set: set[str], mapping: dict[str, str]) -> str | None:
    for slug, label in mapping.items():
        if slug in tag_set:
            return label
    return None


def pick_weight(product: dict) -> str | None:
    short = strip_html(product.get("short_description", ""))
    match = re.search(r"\b(\d+(?:\.\d+)?\s*(?:g|kg|ml|l|cm|pc|pcs|pot|portion|bunch|cup))\b", short, re.I)
    if match:
        return match.group(1)
    for attr in product.get("attributes", []):
        if attr.get("name", "").lower() == "size" and attr.get("terms"):
            return attr["terms"][0].get("name")
    return None


def reset_tables(cur) -> None:
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in ("contact_messages", "plants", "tools", "foods", "admins", "delivery_base_per_kg"):
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
            strip_html(product.get("short_description") or product.get("description", ""))[:2000],
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
            strip_html(product.get("short_description") or product.get("description", ""))[:2000],
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
            strip_html(product.get("short_description") or product.get("description", ""))[:2000],
            image_data,
            image_type,
            1 if product.get("is_in_stock") else 0,
        ),
    )


def import_group(cur, label: str, products: list[dict], insert_fn) -> int:
    imported = 0
    for index, product in enumerate(products, start=1):
        image_url = product["images"][0].get("src") or product["images"][0].get("thumbnail")
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
