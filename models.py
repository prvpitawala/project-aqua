"""Database models and auth logic for Aqua."""
import os

from dotenv import load_dotenv

load_dotenv()

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


def get_tool_by_id(tool_id):
    """Fetch a single tool by id. Returns dict or None."""
    return _get_item_by_id('tools', tool_id)


def get_tool_image(tool_id, slot):
    """Get image blob and type for a tool. slot must be 1, 2, or 3."""
    return _get_item_image('tools', tool_id, slot)


def add_tool(name, price, category, description, image1=None, image1_type=None, image2=None, image2_type=None, image3=None, image3_type=None, weight=None, in_stock=True):
    """Insert a new tool. Returns (new_id, None) or (None, error_message)."""
    return _add_item('tools', name, price, category, description, image1, image1_type, image2, image2_type, image3, image3_type, weight, in_stock)


def update_tool(tool_id, name, price, category, description, weight=None, in_stock=True):
    """Update a tool. Returns True on success, False on error."""
    return _update_item('tools', tool_id, name, price, category, description, weight, in_stock)


def get_foods():
    """Fetch all foods from the database."""
    return _get_items('foods')


def get_food_by_id(food_id):
    """Fetch a single food by id. Returns dict or None."""
    return _get_item_by_id('foods', food_id)


def get_food_image(food_id, slot):
    """Get image blob and type for a food. slot must be 1, 2, or 3."""
    return _get_item_image('foods', food_id, slot)


def add_food(name, price, category, description, image1=None, image1_type=None, image2=None, image2_type=None, image3=None, image3_type=None, weight=None, in_stock=True):
    """Insert a new food. Returns (new_id, None) or (None, error_message)."""
    return _add_item('foods', name, price, category, description, image1, image1_type, image2, image2_type, image3, image3_type, weight, in_stock)


def update_food(food_id, name, price, category, description, weight=None, in_stock=True):
    """Update a food. Returns True on success, False on error."""
    return _update_item('foods', food_id, name, price, category, description, weight, in_stock)


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


def _get_item_by_id(table, item_id):
    """Fetch a single catalog item by id."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                f'''SELECT id, name, price, category, weight, description, in_stock,
                   CASE WHEN image1 IS NOT NULL THEN 1 ELSE 0 END AS has_image1,
                   CASE WHEN image2 IS NOT NULL THEN 1 ELSE 0 END AS has_image2,
                   CASE WHEN image3 IS NOT NULL THEN 1 ELSE 0 END AS has_image3
                   FROM {table} WHERE id = %s''',
                (item_id,),
            )
            row = cur.fetchone()
        conn.close()
        if not row:
            return None
        d = dict(row)
        if d.get('in_stock') is not None:
            d['in_stock'] = bool(d['in_stock'])
        return d
    except Exception:
        return None


def _update_item_images(table, item_id, images):
    """Update image blobs for slots that received a new upload."""
    if not images:
        return True
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            for slot in (1, 2, 3):
                pair = images[slot - 1] if len(images) >= slot else (None, None)
                data, mime = pair if pair else (None, None)
                if data:
                    cur.execute(
                        f"UPDATE {table} SET image{slot}=%s, image{slot}_type=%s WHERE id=%s",
                        (data, mime, item_id),
                    )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def _update_item(table, item_id, name, price, category, description, weight=None, in_stock=True):
    """Update a tool or food row."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                f'''UPDATE {table} SET name=%s, price=%s, category=%s, description=%s, weight=%s, in_stock=%s
                   WHERE id=%s''',
                (
                    name,
                    price,
                    category,
                    description or '',
                    (weight or '').strip() or None,
                    1 if in_stock else 0,
                    item_id,
                ),
            )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


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


def get_contact_message_by_id(message_id):
    """Fetch a single contact message by id."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, name, email, subject, message, created_at FROM contact_messages WHERE id = %s',
                (message_id,),
            )
            row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None


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


def ensure_product_files_table():
    """Create product_files table if it does not exist yet."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS product_files (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_type VARCHAR(20) NOT NULL,
                    product_id INT NOT NULL,
                    file_name VARCHAR(255) NOT NULL,
                    file_type VARCHAR(100) DEFAULT NULL,
                    file_size INT NOT NULL DEFAULT 0,
                    file_data LONGBLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_product (product_type, product_id)
                )
                '''
            )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def get_product_files(product_type, product_id):
    """Return metadata for files attached to a catalog product (no blob data)."""
    ensure_product_files_table()
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT id, file_name, file_type, file_size, created_at
                FROM product_files
                WHERE product_type = %s AND product_id = %s
                ORDER BY id ASC
                ''',
                (product_type, product_id),
            )
            rows = cur.fetchall()
        conn.close()
        return rows
    except Exception:
        return []


def get_product_file_by_id(file_id):
    """Return a single file record including blob data, or None."""
    ensure_product_files_table()
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT id, product_type, product_id, file_name, file_type, file_size, file_data
                FROM product_files
                WHERE id = %s
                ''',
                (file_id,),
            )
            row = cur.fetchone()
        conn.close()
        return row
    except Exception:
        return None


def add_product_file(product_type, product_id, file_name, file_data, file_type, file_size):
    """Attach a document to a catalog product. Returns new file id or None."""
    ensure_product_files_table()
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO product_files (product_type, product_id, file_name, file_type, file_size, file_data)
                VALUES (%s, %s, %s, %s, %s, %s)
                ''',
                (product_type, product_id, file_name, file_type, file_size, file_data),
            )
            new_id = cur.lastrowid
        conn.commit()
        conn.close()
        return new_id
    except Exception:
        return None


def delete_product_files(product_type, product_id, file_ids):
    """Delete files that belong to the given product. Returns number deleted."""
    if not file_ids:
        return 0
    ensure_product_files_table()
    placeholders = ','.join(['%s'] * len(file_ids))
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                f'''
                DELETE FROM product_files
                WHERE product_type = %s AND product_id = %s AND id IN ({placeholders})
                ''',
                (product_type, product_id, *file_ids),
            )
            deleted = cur.rowcount
        conn.commit()
        conn.close()
        return deleted
    except Exception:
        return 0


def ensure_orders_tables():
    """Create orders tables if they do not exist yet."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_name VARCHAR(200) NOT NULL,
                    customer_email VARCHAR(255) NOT NULL,
                    customer_phone VARCHAR(50) DEFAULT NULL,
                    delivery_address TEXT DEFAULT NULL,
                    notes TEXT DEFAULT NULL,
                    subtotal DECIMAL(10, 2) NOT NULL DEFAULT 0,
                    delivery_fee DECIMAL(10, 2) NOT NULL DEFAULT 0,
                    total DECIMAL(10, 2) NOT NULL DEFAULT 0,
                    status VARCHAR(40) NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )
            cur.execute(
                '''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT NOT NULL,
                    product_type VARCHAR(20) NOT NULL,
                    product_id INT NOT NULL,
                    product_name VARCHAR(200) NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    quantity INT NOT NULL DEFAULT 1,
                    line_total DECIMAL(10, 2) NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
                )
                '''
            )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def create_order(customer_name, customer_email, customer_phone, delivery_address, notes, items):
    """
    Save a customer order and line items.
    items: list of dicts with keys type, id, name, price, quantity, weightKg (optional).
    Returns (order_id, None) or (None, error_message).
    """
    if not customer_name or not customer_email:
        return (None, 'Name and email are required.')
    if not items:
        return (None, 'Cart is empty.')

    ensure_orders_tables()

    subtotal = 0.0
    total_weight = 0.0
    normalized = []
    for item in items:
        try:
            qty = int(item.get('quantity', 1))
        except (TypeError, ValueError):
            qty = 1
        if qty < 1:
            continue
        try:
            price = float(item.get('price', 0))
        except (TypeError, ValueError):
            price = 0.0
        name = (item.get('name') or '').strip()
        product_type = (item.get('type') or 'product').strip().lower()
        try:
            product_id = int(item.get('id', 0))
        except (TypeError, ValueError):
            product_id = 0
        if not name:
            continue
        try:
            weight_kg = float(item.get('weightKg') or 0)
        except (TypeError, ValueError):
            weight_kg = 0.0
        line_total = price * qty
        subtotal += line_total
        total_weight += weight_kg * qty
        normalized.append({
            'product_type': product_type,
            'product_id': product_id,
            'product_name': name,
            'unit_price': price,
            'quantity': qty,
            'line_total': line_total,
        })

    if not normalized:
        return (None, 'No valid items in cart.')

    delivery_fee = float(calculate_delivery_by_weight(total_weight))
    total = subtotal + delivery_fee

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO orders (
                    customer_name, customer_email, customer_phone, delivery_address, notes,
                    subtotal, delivery_fee, total, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''',
                (
                    customer_name.strip(),
                    customer_email.strip(),
                    (customer_phone or '').strip() or None,
                    (delivery_address or '').strip() or None,
                    (notes or '').strip() or None,
                    round(subtotal, 2),
                    round(delivery_fee, 2),
                    round(total, 2),
                    'pending',
                ),
            )
            order_id = cur.lastrowid
            for row in normalized:
                cur.execute(
                    '''
                    INSERT INTO order_items (
                        order_id, product_type, product_id, product_name,
                        unit_price, quantity, line_total
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''',
                    (
                        order_id,
                        row['product_type'],
                        row['product_id'],
                        row['product_name'],
                        row['unit_price'],
                        row['quantity'],
                        row['line_total'],
                    ),
                )
        conn.commit()
        conn.close()
        return (order_id, None)
    except Exception as e:
        return (None, str(e))


def get_orders_paginated(page=1, per_page=15):
    """Fetch one page of orders. Returns (orders, total, total_pages, current_page)."""
    ensure_orders_tables()
    normalize_order_statuses()
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) AS n FROM orders')
            total = int(cur.fetchone()['n'])
            total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
            page = max(1, min(int(page), total_pages))
            offset = (page - 1) * per_page
            cur.execute(
                '''
                SELECT o.id, o.customer_name, o.customer_email, o.customer_phone,
                       o.subtotal, o.delivery_fee, o.total, o.status, o.created_at,
                       COUNT(oi.id) AS item_count
                FROM orders o
                LEFT JOIN order_items oi ON oi.order_id = o.id
                GROUP BY o.id
                ORDER BY o.created_at DESC
                LIMIT %s OFFSET %s
                ''',
                (int(per_page), int(offset)),
            )
            rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows] if rows else [], total, total_pages, page
    except Exception:
        return [], 0, 1, 1


def get_order_by_id(order_id):
    """Fetch a single order with its line items."""
    ensure_orders_tables()
    normalize_order_statuses()
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT id, customer_name, customer_email, customer_phone,
                       delivery_address, notes, subtotal, delivery_fee, total,
                       status, created_at
                FROM orders WHERE id = %s
                ''',
                (order_id,),
            )
            order = cur.fetchone()
            if not order:
                conn.close()
                return None
            cur.execute(
                '''
                SELECT id, product_type, product_id, product_name,
                       unit_price, quantity, line_total
                FROM order_items WHERE order_id = %s ORDER BY id
                ''',
                (order_id,),
            )
            items = cur.fetchall()
        conn.close()
        result = dict(order)
        result['items'] = [dict(i) for i in items] if items else []
        return result
    except Exception:
        return None


ORDER_STATUSES = ('pending', 'completed')


def normalize_order_statuses():
    """Map legacy order statuses to pending or completed only."""
    ensure_orders_tables()
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE orders SET status = 'completed' WHERE status IN ('completed', 'confirmed')"
            )
            cur.execute(
                "UPDATE orders SET status = 'pending' WHERE status IS NULL OR status NOT IN ('pending', 'completed')"
            )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def get_order_status_counts():
    """Return total counts for pending and completed orders."""
    normalize_order_statuses()
    counts = {'pending': 0, 'completed': 0, 'total': 0}
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) AS n FROM orders')
            counts['total'] = int(cur.fetchone()['n'])
            cur.execute(
                "SELECT status, COUNT(*) AS n FROM orders WHERE status IN ('pending', 'completed') GROUP BY status"
            )
            for row in cur.fetchall():
                counts[row['status']] = int(row['n'])
        conn.close()
    except Exception:
        pass
    return counts


def update_order_status(order_id, status):
    """Update order status. Returns True on success."""
    allowed = set(ORDER_STATUSES)
    status = (status or '').strip().lower()
    if status not in allowed:
        return False
    ensure_orders_tables()
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('UPDATE orders SET status = %s WHERE id = %s', (status, order_id))
            updated = cur.rowcount > 0
        conn.commit()
        conn.close()
        return updated
    except Exception:
        return False


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
