"""
Fetch product metadata and image URLs from minipuraaqua.lk and save to JSON.

Usage:
  python scripts/export_minipura_catalog.py
  python scripts/export_minipura_catalog.py --count 50
"""
from __future__ import annotations

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.minipura_sources import DEFAULT_COUNT, fetch_catalog, save_catalog


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Export Minipura catalog JSON for seed.py")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT, help="Items per category (default: 50)")
    args = parser.parse_args()

    print(f"Fetching {args.count} plants, tools, and foods from minipuraaqua.lk ...")
    try:
        catalog = fetch_catalog(args.count)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    plants = len(catalog.get("plants", []))
    tools = len(catalog.get("tools", []))
    foods = len(catalog.get("foods", []))
    if plants < args.count or tools < args.count or foods < args.count:
        print(f"WARNING: Expected {args.count} each; got plants={plants}, tools={tools}, foods={foods}")

    path = save_catalog(catalog)
    print(f"Saved catalog to {path}")
    print(f"  plants: {plants}")
    print(f"  tools:  {tools}")
    print(f"  foods:  {foods}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
