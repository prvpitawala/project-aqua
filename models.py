"""Database models and auth logic for Aqua."""
import os
import pymysql
from werkzeug.security import check_password_hash

# Load MySQL config from instance or env
try:
    from instance.config import (
        MYSQL_HOST, MYSQL_PORT, MYSQL_USER,
        MYSQL_PASSWORD, MYSQL_DATABASE
    )
except ImportError:
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'aqua_db')


def get_db_connection():
    """Return a MySQL connection for the Aqua database."""
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor
    )


def verify_admin(username: str, password: str) -> bool:
    """
    Check username and password against the admins table.
    Returns True if credentials are valid, False otherwise.
    """
    if not username or not password:
        return False
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                'SELECT password_hash FROM admins WHERE username = %s',
                (username.strip(),)
            )
            row = cur.fetchone()
        conn.close()
        if row and check_password_hash(row['password_hash'], password):
            return True
        return False
    except Exception:
        return False


def get_plants():
    """Fetch all plants from the database (without blob data for listing)."""
    return _get_plants_items()


def get_plant_by_id(plant_id):
    """Fetch a single plant by id. Returns dict or None."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                '''SELECT id, name, price, category, weight, description, care_level, co2_condition, light_condition, in_stock,
                   CASE WHEN image1 IS NOT NULL THEN 1 ELSE 0 END AS has_image1,
                   CASE WHEN image2 IS NOT NULL THEN 1 ELSE 0 END AS has_image2,
                   CASE WHEN image3 IS NOT NULL THEN 1 ELSE 0 END AS has_image3
                   FROM plants WHERE id = %s''',
                (plant_id,)
            )
            row = cur.fetchone()
        conn.close()
        if not row:
            return None
        d = dict(row)
        if 'in_stock' in d and d['in_stock'] is not None:
            d['in_stock'] = bool(d['in_stock'])
        return d
    except Exception:
        return None


def _get_plants_items():
    """Fetch plants including care_level."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                '''SELECT id, name, price, category, weight, description, care_level, co2_condition, light_condition, in_stock,
                   CASE WHEN image1 IS NOT NULL THEN 1 ELSE 0 END AS has_image1
                   FROM plants ORDER BY created_at DESC'''
            )
            rows = cur.fetchall()
        conn.close()
        out = []
        for r in rows:
            d = dict(r)
            if 'in_stock' in d and d['in_stock'] is not None:
                d['in_stock'] = bool(d['in_stock'])
            out.append(d)
        return out
    except Exception:
        return []


def get_plant_image(plant_id, slot):
    """Get image blob and type for a plant. slot must be 1, 2, or 3."""
    return _get_item_image('plants', plant_id, slot)


def add_plant(name, price, category, description, images=None, weight=None, in_stock=True, care_level=None, co2_condition=None, light_condition=None):
    """Insert a new plant. images is ((img1, type1), (img2, type2), (img3, type3)). Returns (new_id, None) or (None, error_message)."""
    return _add_plant_item(name, price, category, description, weight, in_stock, care_level, co2_condition, light_condition, images)


def update_plant(plant_id, name, price, category, description, weight=None, in_stock=True, care_level=None, co2_condition=None, light_condition=None):
    """Update a plant. Returns True on success, False on error."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                '''UPDATE plants SET name=%s, price=%s, category=%s, description=%s, weight=%s, in_stock=%s, care_level=%s, co2_condition=%s, light_condition=%s
                   WHERE id=%s''',
                (name, price, category, description or '', (weight or '').strip() or None, 1 if in_stock else 0, (care_level or '').strip() or None, (co2_condition or '').strip() or None, (light_condition or '').strip() or None, plant_id)
            )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def _add_plant_item(name, price, category, description, weight=None, in_stock=True, care_level=None, co2_condition=None, light_condition=None, images=None):
    """Insert a new plant. images is ((img1, type1), (img2, type2), (img3, type3)). Returns (new_id, None) or (None, error_message)."""
    def _img(i):
        return images[i] if images and len(images) > i else (None, None)
    img1, img1_t = _img(0)
    img2, img2_t = _img(1)
    img3, img3_t = _img(2)
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                '''INSERT INTO plants (name, price, category, weight, description, care_level, co2_condition, light_condition, image1, image1_type, image2, image2_type, image3, image3_type, in_stock)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (name, price, category, (weight or '').strip() or None, description or '', (care_level or '').strip() or None, (co2_condition or '').strip() or None, (light_condition or '').strip() or None, img1, img1_t, img2, img2_t, img3, img3_t, 1 if in_stock else 0)
            )
            new_id = cur.lastrowid
        conn.commit()
        conn.close()
        return (new_id, None)
    except Exception as e:
        return (None, str(e))


def _add_item(table, name, price, category, description, image1=None, image1_type=None, image2=None, image2_type=None, image3=None, image3_type=None, weight=None, in_stock=True):
    """Generic insert for plants, tools, or foods. Returns (new_id, None) or (None, error_message)."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                f'''INSERT INTO {table} (name, price, category, weight, description, image1, image1_type, image2, image2_type, image3, image3_type, in_stock)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (name, price, category, (weight or '').strip() or None, description or '', image1, image1_type, image2, image2_type, image3, image3_type, 1 if in_stock else 0)
            )
            new_id = cur.lastrowid
        conn.commit()
        conn.close()
        return (new_id, None)
    except Exception as e:
        return (None, str(e))


def get_tools():
    """Fetch all tools from the database."""
    return _get_items('tools')


def get_tool_image(tool_id, slot):
    """Get image blob and type for a tool. slot must be 1, 2, or 3."""
    return _get_item_image('tools', tool_id, slot)


def add_tool(name, price, category, description, image1=None, image1_type=None, image2=None, image2_type=None, image3=None, image3_type=None, weight=None, in_stock=True):
    """Insert a new tool. Returns (new_id, None) or (None, error_message)."""
    return _add_item('tools', name, price, category, description, image1, image1_type, image2, image2_type, image3, image3_type, weight, in_stock)


def get_foods():
    """Fetch all foods from the database."""
    return _get_items('foods')


def get_food_image(food_id, slot):
    """Get image blob and type for a food. slot must be 1, 2, or 3."""
    return _get_item_image('foods', food_id, slot)


def add_food(name, price, category, description, image1=None, image1_type=None, image2=None, image2_type=None, image3=None, image3_type=None, weight=None, in_stock=True):
    """Insert a new food. Returns (new_id, None) or (None, error_message)."""
    return _add_item('foods', name, price, category, description, image1, image1_type, image2, image2_type, image3, image3_type, weight, in_stock)


def _get_items(table):
    """Generic fetch for plants, tools, or foods (without blob data)."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                f'SELECT id, name, price, category, weight, description, in_stock, '
                f'CASE WHEN image1 IS NOT NULL THEN 1 ELSE 0 END AS has_image1 '
                f'FROM {table} ORDER BY created_at DESC'
            )
            rows = cur.fetchall()
        conn.close()
        out = []
        for r in rows:
            d = dict(r)
            if 'in_stock' in d and d['in_stock'] is not None:
                d['in_stock'] = bool(d['in_stock'])
            out.append(d)
        return out
    except Exception:
        return []


def get_delivery_base_per_kg():
    """Fetch the base + per kg delivery rule (one row). Returns dict or None."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, max_weight_kg, base_price, extra_per_kg FROM delivery_base_per_kg ORDER BY id LIMIT 1'
            )
            row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None


def update_delivery_base_per_kg(max_weight_kg, base_price, extra_per_kg):
    """Update or create the base + per kg rule. Returns True on success."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM delivery_base_per_kg LIMIT 1')
            row = cur.fetchone()
            if row:
                cur.execute(
                    'UPDATE delivery_base_per_kg SET max_weight_kg = %s, base_price = %s, extra_per_kg = %s WHERE id = %s',
                    (float(max_weight_kg), float(base_price), float(extra_per_kg), row['id'])
                )
            else:
                cur.execute(
                    'INSERT INTO delivery_base_per_kg (max_weight_kg, base_price, extra_per_kg) VALUES (%s, %s, %s)',
                    (float(max_weight_kg), float(base_price), float(extra_per_kg))
                )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def calculate_delivery_by_weight(weight_kg):
    """
    Calculate delivery charge (LKR) for a given weight using the base + per kg rule.
    Up to max_weight_kg = base_price; each extra full kg = extra_per_kg.
    """
    rule = get_delivery_base_per_kg()
    if not rule:
        return 0
    try:
        w = float(weight_kg)
    except (TypeError, ValueError):
        return 0
    base = float(rule['base_price'])
    max_w = float(rule['max_weight_kg'])
    extra = float(rule['extra_per_kg'])
    if w <= max_w:
        return base
    import math
    extra_kg = math.ceil(w - max_w)
    return base + extra_kg * extra


def get_contact_messages():
    """Fetch all contact messages from the database, newest first."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, name, email, subject, message, created_at FROM contact_messages ORDER BY created_at DESC'
            )
            rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows] if rows else []
    except Exception:
        return []


def get_contact_messages_paginated(page=1, per_page=15):
    """
    Fetch one page of contact messages from the DB (LIMIT/OFFSET).
    Returns (messages, total_count, total_pages, current_page).
    Only the current page is loaded from the database.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) AS n FROM contact_messages')
            total = int(cur.fetchone()['n'])
            total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
            page = max(1, min(int(page), total_pages))
            offset = (page - 1) * per_page
            cur.execute(
                'SELECT id, name, email, subject, message, created_at FROM contact_messages ORDER BY created_at DESC LIMIT %s OFFSET %s',
                (int(per_page), int(offset))
            )
            rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows] if rows else [], total, total_pages, page
    except Exception:
        return [], 0, 1, 1


def save_contact_message(name, email, subject, message):
    """Save a contact form message to the database. Returns (id, None) or (None, error)."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO contact_messages (name, email, subject, message) VALUES (%s, %s, %s, %s)',
                (name.strip(), email.strip(), subject.strip(), message.strip())
            )
            new_id = cur.lastrowid
        conn.commit()
        conn.close()
        return (new_id, None)
    except Exception as e:
        return (None, str(e))


def _get_item_image(table, item_id, slot):
    """Get image blob and type for an item. slot must be 1, 2, or 3."""
    if slot not in (1, 2, 3):
        return (None, None)
    try:
        col = f'image{slot}'
        mime_col = f'image{slot}_type'
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                f'SELECT {col} AS data, {mime_col} AS mime FROM {table} WHERE id = %s',
                (item_id,)
            )
            row = cur.fetchone()
        conn.close()
        return (row['data'], row['mime']) if row and row.get('data') else (None, None)
    except Exception:
        return (None, None)
