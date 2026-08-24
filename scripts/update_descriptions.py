"""
Update product descriptions in the database from minipuraaqua.lk.

Matches products by name and writes unique full descriptions
without re-downloading images.

Usage:
  python scripts/update_descriptions.py
  python scripts/update_descriptions.py --count 50
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import import_minipura as mp


def update_table_descriptions(cur, table: str, products: list[dict]) -> tuple[int, int]:
    updated = 0
    missing = 0

    for product in products:
        name = mp.strip_html(product["name"])
        description = mp.build_product_description(product)
        cur.execute(f"SELECT id FROM {table} WHERE name = %s LIMIT 1", (name,))
        row = cur.fetchone()
        if not row:
            missing += 1
            safe_print(f"  Skipped (not in DB): {name[:70]}")
            continue

        cur.execute(f"UPDATE {table} SET description = %s WHERE id = %s", (description, row["id"]))
        updated += 1
        mp.safe_print(f"  Updated: {name[:70]} ({len(description)} chars)")

    return updated, missing


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Update descriptions from minipuraaqua.lk")
    parser.add_argument("--count", type=int, default=mp.DEFAULT_COUNT)
    args = parser.parse_args()

    mp.safe_print(f"Fetching product descriptions from minipuraaqua.lk ...")
    try:
        plants = mp.fetch_products("aqua-plants", args.count)
        foods = mp.fetch_products("fish-feed", args.count)
        tools = mp.fetch_products("aquascaping-product", args.count, exclude_slugs={"fish-feed"})
    except Exception as exc:
        mp.safe_print(f"ERROR: Could not fetch products: {exc}")
        return 1

    try:
        conn = mp.get_connection()
    except Exception as exc:
        mp.safe_print(f"ERROR: Database connection failed: {exc}")
        return 1

    totals = {"updated": 0, "missing": 0}
    try:
        with conn.cursor() as cur:
            for label, table, products in (
                ("plants", "plants", plants),
                ("tools", "tools", tools),
                ("foods", "foods", foods),
            ):
                mp.safe_print(f"Updating {label}...")
                updated, missing = update_table_descriptions(cur, table, products)
                totals["updated"] += updated
                totals["missing"] += missing
        conn.commit()
    except Exception as exc:
        conn.rollback()
        mp.safe_print(f"ERROR: {exc}")
        return 1
    finally:
        conn.close()

    mp.safe_print("Description update completed.")
    mp.safe_print(f"  updated: {totals['updated']}")
    mp.safe_print(f"  not found in DB: {totals['missing']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
