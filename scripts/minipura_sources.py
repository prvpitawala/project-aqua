"""
Shared helpers for fetching product data and images from minipuraaqua.lk.

Uses the public WooCommerce Store API:
  https://minipuraaqua.lk/wp-json/wc/store/v1/products
"""
from __future__ import annotations

import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "https://minipuraaqua.lk"
API_ROOT = f"{BASE_URL}/wp-json/wc/store/v1"
USER_AGENT = "aqua-seed/1.0 (+local dev)"
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

CATALOG_JSON_PATH = Path(__file__).resolve().parent / "data" / "minipura_catalog.json"

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U0001F600-\U0001F64F"
    "\uFE0F"
    "\u200D"
    "]+",
    flags=re.UNICODE,
)


def strip_emojis(text: str) -> str:
    if not text:
        return ""
    return _EMOJI_RE.sub("", text)


def strip_html(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def html_to_formatted_text(text: str) -> str:
    if not text:
        return ""

    text = html.unescape(text)
    text = re.sub(r"<\s*br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"</\s*(p|div|h[1-6]|li|tr|blockquote)\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<\s*li[^>]*>", "• ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)

    lines: list[str] = []
    prev_blank = False
    for raw_line in text.splitlines():
        line = strip_emojis(re.sub(r"[ \t]+", " ", raw_line).strip())
        if not line:
            if not prev_blank:
                lines.append("")
            prev_blank = True
            continue
        lines.append(line)
        prev_blank = False

    return "\n".join(lines).strip()


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


def build_product_description(product: dict, max_length: int = 4000) -> str:
    long_desc = html_to_formatted_text(product.get("description", ""))
    short_desc = html_to_formatted_text(product.get("short_description", ""))
    name = strip_html(product.get("name", ""))

    if len(long_desc) >= 120:
        return long_desc[:max_length]

    parts: list[str] = []
    if name:
        parts.append(name + ".")
    if short_desc:
        parts.append(short_desc)
    if long_desc and long_desc not in short_desc:
        parts.append(long_desc)

    combined = "\n\n".join(parts).strip()
    if len(combined) >= 80:
        return combined[:max_length]

    extras: list[str] = []
    tags = tag_slugs(product)
    co2 = pick_tag_value(tags, CO2_TAGS)
    light = pick_tag_value(tags, LIGHT_TAGS)
    care = pick_care_level(product)
    weight = pick_weight(product)
    if co2:
        extras.append(co2)
    if light:
        extras.append(light)
    if care:
        extras.append(care)
    if weight:
        extras.append(f"Pack size: {weight}")

    fallback = f"{name}.\n\nQuality aquarium product available at Minipura Aqua, Sri Lanka."
    if extras:
        fallback += "\n\n" + "\n".join(f"• {item}" for item in extras)
    return fallback[:max_length]


def product_image_url(product: dict) -> str:
    image = product["images"][0]
    return image.get("src") or image.get("thumbnail") or ""


def plant_record(product: dict) -> dict:
    tags = tag_slugs(product)
    return {
        "name": strip_html(product["name"]),
        "price": price_lkr(product),
        "category": pick_plant_category(product),
        "weight": pick_weight(product),
        "description": build_product_description(product),
        "care_level": pick_care_level(product),
        "co2_condition": pick_tag_value(tags, CO2_TAGS),
        "light_condition": pick_tag_value(tags, LIGHT_TAGS),
        "image_url": product_image_url(product),
        "in_stock": bool(product.get("is_in_stock")),
        "source_url": product.get("permalink") or BASE_URL,
    }


def tool_record(product: dict) -> dict:
    return {
        "name": strip_html(product["name"]),
        "price": price_lkr(product),
        "category": pick_tool_category(product),
        "weight": pick_weight(product),
        "description": build_product_description(product),
        "image_url": product_image_url(product),
        "in_stock": bool(product.get("is_in_stock")),
        "source_url": product.get("permalink") or BASE_URL,
    }


def food_record(product: dict) -> dict:
    name = strip_html(product["name"])
    return {
        "name": name,
        "price": price_lkr(product),
        "category": pick_food_category(name),
        "weight": pick_weight(product),
        "description": build_product_description(product),
        "image_url": product_image_url(product),
        "in_stock": bool(product.get("is_in_stock")),
        "source_url": product.get("permalink") or BASE_URL,
    }


def fetch_catalog(count: int = DEFAULT_COUNT) -> dict:
    plants = fetch_products("aqua-plants", count)
    foods = fetch_products("fish-feed", count)
    tools = fetch_products("aquascaping-product", count, exclude_slugs={"fish-feed"})
    return {
        "source": BASE_URL,
        "api": API_ROOT,
        "count": count,
        "plants": [plant_record(p) for p in plants],
        "tools": [tool_record(p) for p in tools],
        "foods": [food_record(p) for p in foods],
    }


def load_catalog(path: Path | None = None) -> dict:
    catalog_path = path or CATALOG_JSON_PATH
    with open(catalog_path, encoding="utf-8") as handle:
        return json.load(handle)


def save_catalog(catalog: dict, path: Path | None = None) -> Path:
    catalog_path = path or CATALOG_JSON_PATH
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    with open(catalog_path, "w", encoding="utf-8") as handle:
        json.dump(catalog, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return catalog_path
