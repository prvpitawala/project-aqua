"""
Export home-page top-selling product images to static/images/home/.

Picks the second product in each catalog (same logic as the home page) and
writes image1 to disk so the storefront can serve files from /static instead
of the database image routes.

Usage:
  python scripts/export_home_top_images.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from models import get_food_image, get_foods, get_plant_image, get_plants, get_tool_image, get_tools

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'static',
    'images',
    'home',
)

MIME_EXT = {
    'image/jpeg': '.jpg',
    'image/jpg': '.jpg',
    'image/png': '.png',
    'image/webp': '.webp',
    'image/gif': '.gif',
}

EXPORTS = (
    ('top-plant', get_plants, get_plant_image),
    ('top-accessory', get_tools, get_tool_image),
    ('top-food', get_foods, get_food_image),
)


def pick_second(rows):
    if not rows:
        return None
    return rows[1] if len(rows) > 1 else rows[0]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for basename, get_list, get_image in EXPORTS:
        item = pick_second(get_list())
        if not item:
            print(f'Skip {basename}: no products in catalog')
            continue
        data, mime = get_image(item['id'], 1)
        if not data:
            data, mime = get_image(item['id'], 2)
        if not data:
            print(f'Skip {basename}: no image for {item["name"]!r} (id={item["id"]})')
            continue
        ext = MIME_EXT.get((mime or '').lower(), '.jpg')
        path = os.path.join(OUTPUT_DIR, basename + ext)
        with open(path, 'wb') as f:
            f.write(data)
        print(f'Wrote {path} ({len(data)} bytes, {item["name"]!r})')


if __name__ == '__main__':
    main()
