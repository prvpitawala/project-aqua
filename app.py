import os
from dotenv import load_dotenv

load_dotenv()

from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response, flash, get_flashed_messages

from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64 MB for image uploads

MSG_NAME_CATEGORY_REQUIRED = 'Name and category are required.'
MIME_JPEG = 'image/jpeg'
CATALOG_PER_PAGE_DEFAULT = 20
CATALOG_PER_PAGE_OPTIONS = (10, 20, 50)
CATALOG_TABLE_TYPES = {
    'plants': 'plant',
    'tools': 'tool',
    'foods': 'food',
}
ALLOWED_CATALOG_DOC_EXTENSIONS = {'.txt', '.csv', '.md', '.pdf', '.doc', '.docx'}
ALLOWED_CATALOG_DOC_MIMES = {
    'text/plain', 'text/csv', 'text/markdown', 'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}
HOME_TESTIMONIALS = (
    {
        'quote': 'The plants arrived healthy and well packaged. My aquascape finally looks the way I wanted — great quality and fast delivery.',
        'name': 'Dilshan Perera',
        'detail': 'Planted tank hobbyist · Colombo',
        'rating': 5,
    },
    {
        'quote': 'I ordered CO₂ accessories and fish food in one go. Everything was in stock, fairly priced, and the checkout was straightforward.',
        'name': 'Anuki Fernando',
        'detail': 'Aquascaper · Kandy',
        'rating': 5,
    },
    {
        'quote': 'As a beginner, I appreciated the clear product info and helpful recommendations. AquaStore made setting up my first tank much easier.',
        'name': 'Ravindu Jayawardena',
        'detail': 'First-time aquarium owner · Galle',
        'rating': 5,
    },
    {
        'quote': 'Excellent selection of carpet plants and fertilizers. Delivery to Negombo was quick and every stem was in perfect condition.',
        'name': 'Nethmi Silva',
        'detail': 'Nano tank enthusiast · Negombo',
        'rating': 4,
    },
    {
        'quote': 'We buy fish food and filter media for our shop from AquaStore regularly. Consistent quality and reliable stock every time.',
        'name': 'Kasun Wickramasinghe',
        'detail': 'Pet shop owner · Matara',
        'rating': 5,
    },
)


def paginate_list(items, page, per_page=CATALOG_PER_PAGE_DEFAULT):
    """Slice a list for the requested page. Returns (page_items, total, total_pages, current_page)."""
    total = len(items)
    total_pages = max(1, (total + per_page - 1) // per_page) if total else 1
    current_page = max(1, min(page or 1, total_pages))
    start = (current_page - 1) * per_page
    return items[start:start + per_page], total, total_pages, current_page


def _resolve_catalog_per_page():
    """Resolve items-per-page from query or session. Resets to page 1 when per_page changes."""
    per_page_arg = request.args.get('per_page', type=int)
    page = request.args.get('page', 1, type=int)
    prev_per_page = session.get('catalog_per_page', CATALOG_PER_PAGE_DEFAULT)
    if per_page_arg is not None and per_page_arg in CATALOG_PER_PAGE_OPTIONS:
        session['catalog_per_page'] = per_page_arg
        if per_page_arg != prev_per_page:
            page = 1
    per_page = session.get('catalog_per_page', CATALOG_PER_PAGE_DEFAULT)
    if per_page not in CATALOG_PER_PAGE_OPTIONS:
        per_page = CATALOG_PER_PAGE_DEFAULT
    return per_page, page


def _session_per_page_for_path():
    """Return the session-backed per_page value for the current request path."""
    if request.path.startswith('/admin/orders'):
        return session.get('orders_per_page', 10)
    if request.path.startswith('/admin/messages'):
        return session.get('messages_per_page', 10)
    return session.get('catalog_per_page', CATALOG_PER_PAGE_DEFAULT)


@app.context_processor
def inject_pagination_helpers():
    def page_url(page_num):
        params = []
        has_per_page = False
        for key in request.args:
            if key == 'page':
                continue
            if key == 'per_page':
                has_per_page = True
            for val in request.args.getlist(key):
                params.append((key, val))
        if not has_per_page:
            per_page = _session_per_page_for_path()
            if per_page:
                params.append(('per_page', str(per_page)))
        params.append(('page', str(page_num)))
        qs = urlencode(params)
        return request.path + ('?' + qs if qs else '')

    return dict(
        page_url=page_url,
        per_page_options=CATALOG_PER_PAGE_OPTIONS,
        catalog_per_page_default=CATALOG_PER_PAGE_DEFAULT,
        plant_categories=PLANT_CATEGORIES,
        accessory_categories=ACCESSORY_CATEGORIES,
        food_categories=FOOD_CATEGORIES,
        plant_price_ranges=PLANT_PRICE_RANGES,
        food_price_ranges=FOOD_PRICE_RANGES,
        accessory_price_ranges=ACCESSORY_PRICE_RANGES,
    )


@app.route('/')
def index():
    return render_template(
        'public.html',
        top_products=get_top_selling(),
        category_images=get_category_preview_images(),
        testimonials=HOME_TESTIMONIALS,
    )


@app.route('/public')
def public():
    return redirect(url_for('index'))


PLANT_CATEGORIES = [
    'Anubias & Fern', 'Background Plant', 'Bucephalandra', 'Carpeting plant',
    'Cryptocoryne', 'Epiphyte plants', 'Floating plants', 'Ludwigia Varieties',
    'Midground Plant', 'Moss', 'Rare plants', 'Rotala Varieties', 'Other'
]
ACCESSORY_CATEGORIES = [
    'Aquarium Soil', 'water Pump', 'Filter Media', 'CO2 accessaries',
    'Fertilizers & Treatment', 'Temperature accessories', 'Air pumps', 'Other product'
]
FOOD_CATEGORIES = ['Flakes', 'Pellets', 'Freeze-dried', 'Treats']
PLANT_PRICE_RANGES = (
    {'id': '0-500', 'label': 'Under LKR 500'},
    {'id': '500-1000', 'label': 'LKR 500 - 1000'},
    {'id': '1000-2000', 'label': 'LKR 1000 - 2000'},
    {'id': '2000-5000', 'label': 'LKR 2000 - 5000'},
    {'id': '5000+', 'label': 'More than LKR 5000'},
)
FOOD_PRICE_RANGES = (
    {'id': '0-500', 'label': 'Under LKR 500'},
    {'id': '500-1000', 'label': 'LKR 500 - 1000'},
    {'id': '1000-1500', 'label': 'LKR 1000 - 1500'},
    {'id': '2000-5000', 'label': 'LKR 2000 - 5000'},
    {'id': '5000+', 'label': 'More than LKR 5000'},
)
ACCESSORY_PRICE_RANGES = (
    {'id': '0-1000', 'label': 'Under LKR 1000'},
    {'id': '1000-2000', 'label': 'LKR 1000 - 2000'},
    {'id': '2000-3000', 'label': 'LKR 2000 - 3000'},
    {'id': '2000-5000', 'label': 'LKR 2000 - 5000'},
    {'id': '5000+', 'label': 'More than LKR 5000'},
)


def _filter_by_category(items, categories):
    if not categories:
        return items
    return [item for item in items if item.get('category') in categories]


def _attach_catalog_images(items, endpoint):
    for item in items:
        if item.get('has_image1'):
            item['image'] = url_for(endpoint, id=item['id'], slot=1)
        else:
            item['image'] = ''


def _attach_order_item_images(items):
    """Attach primary catalog image URLs to order line items when still available."""
    from models import get_food_image, get_plant_image, get_tool_image

    image_fetchers = {
        'plant': ('serve_plant_image', get_plant_image),
        'accessory': ('serve_tool_image', get_tool_image),
        'tool': ('serve_tool_image', get_tool_image),
        'food': ('serve_food_image', get_food_image),
    }
    for item in items:
        product_type = (item.get('product_type') or '').strip().lower()
        product_id = item.get('product_id')
        entry = image_fetchers.get(product_type)
        item['image'] = ''
        if not entry or not product_id:
            continue
        endpoint, get_image = entry
        data, _mime = get_image(product_id, 1)
        if data:
            item['image'] = url_for(endpoint, id=product_id, slot=1)


def _attach_catalog_detail_images(item, endpoint):
    """Attach primary image and all gallery slots for product detail pages."""
    images = []
    for slot in (1, 2, 3):
        if item.get(f'has_image{slot}'):
            images.append({
                'slot': slot,
                'url': url_for(endpoint, id=item['id'], slot=slot),
            })
    item['images'] = images
    item['image'] = images[0]['url'] if images else ''


def _filter_plants(plants, co2, light, stock, categories):
    if categories:
        plants = _filter_by_category(plants, categories)
    if co2:
        plants = [p for p in plants if (p.get('co2_condition') or '') in co2]
    if light:
        plants = [p for p in plants if (p.get('light_condition') or '') in light]
    return _filter_items_by_stock(plants, stock)


@app.route('/aqua-plants')
def aqua_plants():
    from models import get_plants_paginated
    co2 = request.args.getlist('co2')
    light = request.args.getlist('light')
    stock = request.args.getlist('stock')
    categories = request.args.getlist('category')
    prices = request.args.getlist('price')
    per_page, page = _resolve_catalog_per_page()
    page_plants, total, total_pages, page = get_plants_paginated(
        page, per_page, categories=categories, co2=co2, light=light, stock=stock, prices=prices
    )
    _attach_catalog_images(page_plants, 'serve_plant_image')
    return render_template(
        'aqua_plants.html',
        plants=page_plants,
        co2_filter=co2,
        light_filter=light,
        stock_filter=stock,
        category_filter=categories,
        price_filter=prices,
        page=page,
        total=total,
        total_pages=total_pages,
        per_page=per_page,
        item_label='plant',
    )


@app.route('/aqua-plants/<int:id>')
def plant_detail(id):
    from models import get_plant_by_id
    plant = get_plant_by_id(id)
    if not plant:
        return redirect(url_for('aqua_plants'))
    _attach_catalog_detail_images(plant, 'serve_plant_image')
    return render_template('plant_detail.html', plant=plant)


@app.route('/api/plants')
def api_plants():
    from models import get_plants_paginated
    page = request.args.get('page', 1, type=int)
    co2 = request.args.getlist('co2')
    light = request.args.getlist('light')
    stock = request.args.getlist('stock')
    categories = request.args.getlist('category')
    prices = request.args.getlist('price')
    per_page = 12
    page_plants, total, total_pages, page = get_plants_paginated(
        page, per_page, categories=categories, co2=co2, light=light, stock=stock, prices=prices
    )
    _attach_catalog_images(page_plants, 'serve_plant_image')
    return jsonify(plants=page_plants, has_more=page < total_pages)


@app.route('/accessories')
def accessories():
    from models import get_tools_paginated
    stock = request.args.getlist('stock')
    categories = request.args.getlist('category')
    prices = request.args.getlist('price')
    per_page, page = _resolve_catalog_per_page()
    page_items, total, total_pages, page = get_tools_paginated(
        page, per_page, categories=categories, stock=stock, prices=prices
    )
    _attach_catalog_images(page_items, 'serve_tool_image')
    return render_template(
        'accessories.html',
        accessories=page_items,
        stock_filter=stock,
        category_filter=categories,
        price_filter=prices,
        page=page,
        total=total,
        total_pages=total_pages,
        per_page=per_page,
        item_label='accessory',
    )


@app.route('/accessories/<int:id>')
def accessory_detail(id):
    from models import get_tool_by_id
    item = get_tool_by_id(id)
    if not item:
        return redirect(url_for('accessories'))
    _attach_catalog_detail_images(item, 'serve_tool_image')
    return render_template('accessory_detail.html', item=item)


@app.route('/api/accessories')
def api_accessories():
    from models import get_tools_paginated
    page = request.args.get('page', 1, type=int)
    stock = request.args.getlist('stock')
    categories = request.args.getlist('category')
    prices = request.args.getlist('price')
    per_page = 12
    page_items, total, total_pages, page = get_tools_paginated(
        page, per_page, categories=categories, stock=stock, prices=prices
    )
    _attach_catalog_images(page_items, 'serve_tool_image')
    return jsonify(accessories=page_items, has_more=page < total_pages)


@app.route('/foods')
def foods():
    from models import get_foods_paginated
    stock = request.args.getlist('stock')
    categories = request.args.getlist('category')
    prices = request.args.getlist('price')
    per_page, page = _resolve_catalog_per_page()
    page_items, total, total_pages, page = get_foods_paginated(
        page, per_page, categories=categories, stock=stock, prices=prices
    )
    _attach_catalog_images(page_items, 'serve_food_image')
    return render_template(
        'foods.html',
        foods=page_items,
        stock_filter=stock,
        category_filter=categories,
        price_filter=prices,
        page=page,
        total=total,
        total_pages=total_pages,
        per_page=per_page,
        item_label='food',
    )


@app.route('/foods/<int:id>')
def food_detail(id):
    from models import get_food_by_id
    item = get_food_by_id(id)
    if not item:
        return redirect(url_for('foods'))
    _attach_catalog_detail_images(item, 'serve_food_image')
    return render_template('food_detail.html', item=item)


@app.route('/api/foods')
def api_foods():
    from models import get_foods_paginated
    page = request.args.get('page', 1, type=int)
    stock = request.args.getlist('stock')
    categories = request.args.getlist('category')
    prices = request.args.getlist('price')
    per_page = 12
    page_items, total, total_pages, page = get_foods_paginated(
        page, per_page, categories=categories, stock=stock, prices=prices
    )
    _attach_catalog_images(page_items, 'serve_food_image')
    return jsonify(foods=page_items, has_more=page < total_pages)


@app.route('/api/delivery-rule')
def api_delivery_rule():
    """Return delivery pricing rule for cart: base_price + (weight_kg * extra_per_kg)."""
    from models import get_delivery_base_per_kg
    rule = get_delivery_base_per_kg()
    if not rule:
        return jsonify(base_price=450, extra_per_kg=100)
    return jsonify(base_price=float(rule['base_price']), extra_per_kg=float(rule['extra_per_kg']))


def get_top_selling():
    """Return a mix of top products from plants, accessories, and foods."""
    from models import get_foods, get_plants, get_tools

    items = []
    plants = get_plants()[:2]
    tools = get_tools()[:2]
    foods = get_foods()[:2]
    _attach_catalog_images(plants, 'serve_plant_image')
    _attach_catalog_images(tools, 'serve_tool_image')
    _attach_catalog_images(foods, 'serve_food_image')
    for plant in plants:
        items.append({**plant, 'product_type': 'plant'})
    for tool in tools:
        items.append({**tool, 'product_type': 'accessory'})
    for food in foods:
        items.append({**food, 'product_type': 'food'})
    return items


def _first_item_image_url(items, endpoint):
    """Return image URL for the first catalog item that has an image."""
    for item in items:
        if item.get('has_image1'):
            return url_for(endpoint, id=item['id'], slot=1)
    return None


def get_category_preview_images():
    """Sample image per home-page category card (plants, tools, foods)."""
    from models import get_foods, get_plants, get_tools

    return {
        'plants': _first_item_image_url(get_plants(), 'serve_plant_image'),
        'tools': _first_item_image_url(get_tools(), 'serve_tool_image'),
        'foods': _first_item_image_url(get_foods(), 'serve_food_image'),
    }


@app.route('/tools')
def tools():
    return render_template('tools.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        from models import save_contact_message
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        if name and email and subject and message:
            new_id, _ = save_contact_message(name, email, subject, message)
            if new_id:
                flash('Thank you! Your message has been sent.', 'success')
                return redirect(url_for('contact'))
    return render_template('contact.html')


@app.route('/checkout')
def checkout():
    return render_template('checkout.html')


@app.route('/api/orders', methods=['POST'])
def api_create_order():
    from models import create_order

    data = request.get_json(silent=True) or {}
    customer_name = (data.get('customer_name') or '').strip()
    customer_email = (data.get('customer_email') or '').strip()
    customer_phone = (data.get('customer_phone') or '').strip()
    delivery_address = (data.get('delivery_address') or '').strip()
    notes = (data.get('notes') or '').strip()
    items = data.get('items') or []

    if not customer_name or not customer_email:
        return jsonify(success=False, error='Name and email are required.'), 400
    if not delivery_address:
        return jsonify(success=False, error='Delivery address is required.'), 400
    if not items:
        return jsonify(success=False, error='Your cart is empty.'), 400

    order_id, error = create_order(
        customer_name,
        customer_email,
        customer_phone,
        delivery_address,
        notes,
        items,
    )
    if not order_id:
        return jsonify(success=False, error=error or 'Could not place order.'), 400
    return jsonify(success=True, order_id=order_id)


@app.route('/signin')
def signin():
    if session.get('admin'):
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('index') + '?open=signin')


@app.route('/admin/login', methods=['POST'])
def admin_login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if username and password:
        from models import verify_admin
        if verify_admin(username, password):
            session['admin'] = True
            return jsonify(success=True, redirect=url_for('admin_dashboard'))
    return jsonify(success=False, error='Invalid username or password'), 401


def admin_required(f):
    """Decorator to require admin login."""
    @wraps(f)
    def inner(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return inner


@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')


PER_PAGE_OPTIONS = (5, 10, 20, 50)


def _resolve_admin_per_page(session_key, default, options):
    """Resolve admin list page/per_page from query or session."""
    per_page_arg = request.args.get('per_page', type=int)
    page = request.args.get('page', 1, type=int)
    prev_per_page = session.get(session_key, default)
    if per_page_arg is not None and per_page_arg in options:
        session[session_key] = per_page_arg
        if per_page_arg != prev_per_page:
            page = 1
    per_page = session.get(session_key, default)
    if per_page not in options:
        per_page = default
    return per_page, page


@app.route('/admin/messages')
@admin_required
def admin_messages():
    from models import get_contact_messages_paginated
    per_page, page = _resolve_admin_per_page('messages_per_page', 10, PER_PAGE_OPTIONS)
    messages, total, total_pages, current_page = get_contact_messages_paginated(page, per_page)
    notice, notice_type = _get_flashed_notice()
    return render_template(
        'admin_messages.html',
        messages=messages,
        total=total,
        total_pages=total_pages,
        page=current_page,
        per_page=per_page,
        per_page_options=PER_PAGE_OPTIONS,
        notice=notice,
        notice_type=notice_type,
    )


@app.route('/admin/messages/<int:message_id>/reply', methods=['POST'])
@admin_required
def admin_message_reply(message_id):
    from models import get_contact_message_by_id

    message = get_contact_message_by_id(message_id)
    if not message:
        flash('Message not found.', 'error')
        return redirect(url_for('admin_messages'))

    reply_subject = request.form.get('reply_subject', '').strip()
    reply_body = request.form.get('reply_body', '').strip()
    if not reply_subject or not reply_body:
        flash('Reply subject and message are required.', 'error')
        return redirect(url_for('admin_messages'))

    # TODO: send email to message['email'] with reply_subject and reply_body
    _ = (message, reply_subject, reply_body)

    flash('Reply saved. Email delivery will be enabled in a future update.', 'success')
    return redirect(url_for('admin_messages'))


@app.route('/admin/orders')
@admin_required
def admin_orders():
    from models import get_orders_paginated, get_order_status_counts

    per_page, page = _resolve_admin_per_page('orders_per_page', 10, PER_PAGE_OPTIONS)
    orders, total, total_pages, current_page = get_orders_paginated(page, per_page)
    status_counts = get_order_status_counts()
    notice, notice_type = _get_flashed_notice()
    return render_template(
        'admin_orders.html',
        orders=orders,
        total=total,
        total_pages=total_pages,
        page=current_page,
        per_page=per_page,
        per_page_options=PER_PAGE_OPTIONS,
        status_counts=status_counts,
        notice=notice,
        notice_type=notice_type,
    )


@app.route('/admin/orders/<int:order_id>', methods=['GET'])
@admin_required
def admin_order_detail(order_id):
    from models import get_order_by_id

    order = get_order_by_id(order_id)
    if not order:
        return redirect(url_for('admin_orders'))

    _attach_order_item_images(order['items'])

    message, message_type = _get_flashed_notice()

    return render_template(
        'admin_order_detail.html',
        order=order,
        message=message,
        message_type=message_type,
    )


@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def admin_order_status(order_id):
    from models import update_order_status

    status = request.form.get('status', '').strip()
    return_to = request.form.get('return_to', 'list')
    page = request.form.get('page', 1, type=int)
    per_page = request.form.get('per_page', type=int)

    if not update_order_status(order_id, status):
        flash('Could not update order status.', 'error')
        if return_to == 'detail':
            return redirect(url_for('admin_order_detail', order_id=order_id))
        params = {'page': page}
        if per_page:
            params['per_page'] = per_page
        return redirect(url_for('admin_orders', **params))

    flash('Order status updated.', 'success')
    if return_to == 'detail':
        return redirect(url_for('admin_order_detail', order_id=order_id))

    params = {'page': page}
    if per_page:
        params['per_page'] = per_page
    return redirect(url_for('admin_orders', **params))


def _filter_items_by_stock(items, stock):
    """Filter items by stock status. Returns filtered list."""
    if not stock:
        return items
    in_ok = 'in' in stock
    out_ok = 'out' in stock
    if in_ok and not out_ok:
        return [x for x in items if x.get('in_stock', True)]
    if out_ok and not in_ok:
        return [x for x in items if not x.get('in_stock', True)]
    return items


def _filter_plants_for_admin(plants, co2, light, stock, categories=None):
    """Apply co2, light, stock, and category filters to plants."""
    return _filter_plants(plants, co2, light, stock, categories or [])


def _ensure_plant_images(plants):
    """Add image URL to plants that have has_image1 but no image key."""
    _attach_catalog_images(plants, 'serve_plant_image')


def _blank_catalog_item():
    return {
        'id': None,
        'name': '',
        'price': 0,
        'category': '',
        'weight': '',
        'description': '',
        'in_stock': True,
        'care_level': '',
        'co2_condition': '',
        'light_condition': '',
        'has_image1': False,
        'has_image2': False,
        'has_image3': False,
    }


def _read_form_images():
    img1, img1_type = _read_uploaded_image('image1')
    img2, img2_type = _read_uploaded_image('image2')
    img3, img3_type = _read_uploaded_image('image3')
    return ((img1, img1_type), (img2, img2_type), (img3, img3_type))


def _parse_catalog_form_fields():
    try:
        price = float(request.form.get('price', 0) or 0)
    except ValueError:
        price = 0.0
    return {
        'name': request.form.get('name', '').strip(),
        'price': price,
        'category': request.form.get('category', '').strip(),
        'weight': request.form.get('weight', '').strip(),
        'description': request.form.get('description', '').strip(),
        'in_stock': request.form.get('in_stock') == '1',
        'care_level': request.form.get('care_level', '').strip() or None,
        'co2_condition': request.form.get('co2_condition', '').strip() or None,
        'light_condition': request.form.get('light_condition', '').strip() or None,
    }


def _is_allowed_catalog_document(filename, mime_type):
    ext = os.path.splitext((filename or '').lower())[1]
    if ext in ALLOWED_CATALOG_DOC_EXTENSIONS:
        return True
    if mime_type:
        if mime_type.startswith('text/'):
            return True
        if mime_type in ALLOWED_CATALOG_DOC_MIMES:
            return True
    return False


def _catalog_files_for(table, item_id=None):
    if not item_id:
        return []
    from models import get_product_files
    return get_product_files(CATALOG_TABLE_TYPES[table], item_id)


def _process_catalog_file_changes(table, item_id):
    """Apply document uploads and deletions for a catalog product."""
    from models import add_product_file, delete_product_files
    from werkzeug.utils import secure_filename

    product_type = CATALOG_TABLE_TYPES[table]
    delete_ids = []
    for raw_id in request.form.getlist('delete_file_ids'):
        try:
            delete_ids.append(int(raw_id))
        except (TypeError, ValueError):
            pass
    if delete_ids:
        delete_product_files(product_type, item_id, delete_ids)

    for upload in request.files.getlist('catalog_documents'):
        if not upload or not upload.filename:
            continue
        filename = secure_filename(upload.filename) or 'document.txt'
        data = upload.read()
        if not data:
            continue
        if not _is_allowed_catalog_document(filename, upload.content_type):
            continue
        mime = (upload.content_type or 'application/octet-stream')[:100]
        add_product_file(product_type, item_id, filename, data, mime, len(data))


def _get_flashed_notice(default_type='success'):
    """Return the first flashed message, consumed so it won't reappear on refresh."""
    messages = get_flashed_messages(with_categories=True)
    if messages:
        category, message = messages[0]
        return message, category
    return None, default_type


def _admin_list_flash_message(item_label):
    message, category = _get_flashed_notice()
    if message:
        return message, category
    return None, 'success'


def _admin_delete_product(table, item_id, get_by_id, list_route, item_label):
    """Delete a catalog product and redirect back to its admin list."""
    from models import delete_item

    if not get_by_id(item_id):
        return redirect(list_route)
    if delete_item(table, item_id):
        flash(f'{item_label} deleted successfully.', 'success')
        return redirect(list_route)
    flash(f'Failed to delete {item_label.lower()}.', 'error')
    return redirect(list_route)


@app.route('/admin/plants', methods=['GET'])
@admin_required
def admin_plants():
    from models import get_plants_paginated
    message, message_type = _admin_list_flash_message('Plant')
    co2 = request.args.getlist('co2')
    light = request.args.getlist('light')
    stock = request.args.getlist('stock')
    categories = request.args.getlist('category')
    prices = request.args.getlist('price')
    per_page, page = _resolve_catalog_per_page()
    page_plants, total, total_pages, page = get_plants_paginated(
        page, per_page, categories=categories, co2=co2, light=light, stock=stock, prices=prices
    )
    _ensure_plant_images(page_plants)
    return render_template(
        'admin_plants.html',
        plants=page_plants,
        message=message,
        message_type=message_type,
        co2_filter=co2,
        light_filter=light,
        stock_filter=stock,
        category_filter=categories,
        price_filter=prices,
        page=page,
        total=total,
        total_pages=total_pages,
        per_page=per_page,
        item_label='plant',
    )


@app.route('/admin/plants/<int:id>')
@admin_required
def admin_plant_detail(id):
    """Admin view of plant details (like public plant_detail)."""
    from models import get_plant_by_id
    plant = get_plant_by_id(id)
    if not plant:
        return redirect(url_for('admin_plants'))
    _attach_catalog_images([plant], 'serve_plant_image')
    return render_template('admin_plant_detail.html', plant=plant)


def _save_plant_form(item_id=None):
    """Process plant create/edit form. Returns redirect response or (item, message, message_type) for re-render."""
    from models import add_plant, update_plant, _update_item_images
    form_data = _parse_catalog_form_fields()
    if not form_data['name'] or not form_data['category']:
        item = dict(_blank_catalog_item(), **{k: form_data.get(k, '') for k in ('name', 'category', 'weight', 'description')})
        item['price'] = form_data['price']
        item['in_stock'] = form_data['in_stock']
        item['care_level'] = form_data.get('care_level') or ''
        item['co2_condition'] = form_data.get('co2_condition') or ''
        item['light_condition'] = form_data.get('light_condition') or ''
        return item, MSG_NAME_CATEGORY_REQUIRED, 'error'
    images = _read_form_images()
    if item_id:
        if not update_plant(item_id, **form_data):
            merged = dict(_blank_catalog_item(), **form_data)
            merged['id'] = item_id
            merged['care_level'] = form_data.get('care_level') or ''
            merged['co2_condition'] = form_data.get('co2_condition') or ''
            merged['light_condition'] = form_data.get('light_condition') or ''
            return merged, 'Failed to update plant.', 'error'
        _update_item_images('plants', item_id, images)
        _process_catalog_file_changes('plants', item_id)
        flash('Plant updated successfully.', 'success')
        return redirect(url_for('admin_plants'))
    new_id, err = add_plant(
        form_data['name'], form_data['price'], form_data['category'], form_data['description'],
        images=images, weight=form_data['weight'], in_stock=form_data['in_stock'],
        care_level=form_data['care_level'], co2_condition=form_data['co2_condition'],
        light_condition=form_data['light_condition'],
    )
    if new_id:
        _process_catalog_file_changes('plants', new_id)
        flash('Plant added successfully.', 'success')
        return redirect(url_for('admin_plants'))
    fail_msg = f'Failed to add plant: {err}' if err else 'Failed to add plant. Check database connection.'
    item = dict(_blank_catalog_item(), **form_data)
    item['care_level'] = form_data.get('care_level') or ''
    item['co2_condition'] = form_data.get('co2_condition') or ''
    item['light_condition'] = form_data.get('light_condition') or ''
    return item, fail_msg, 'error'


@app.route('/admin/plants/new', methods=['GET', 'POST'])
@admin_required
def admin_plants_new():
    if request.method == 'POST':
        result = _save_plant_form()
        if isinstance(result, tuple) and len(result) == 3:
            item, message, message_type = result
            return render_template(
                'admin_plant_edit.html',
                item=item,
                is_edit=False,
                form_action=url_for('admin_plants_new'),
                message=message,
                message_type=message_type,
                catalog_files=[],
            )
        return result
    return render_template(
        'admin_plant_edit.html',
        item=_blank_catalog_item(),
        is_edit=False,
        form_action=url_for('admin_plants_new'),
        catalog_files=[],
    )


@app.route('/admin/plants/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_plants_edit(id):
    from models import get_plant_by_id
    plant = get_plant_by_id(id)
    if not plant:
        return redirect(url_for('admin_plants'))
    if request.method == 'POST':
        result = _save_plant_form(id)
        if isinstance(result, tuple) and len(result) == 3:
            item, message, message_type = result
            return render_template(
                'admin_plant_edit.html',
                item=item or plant,
                is_edit=True,
                form_action=url_for('admin_plants_edit', id=id),
                message=message,
                message_type=message_type,
                catalog_files=_catalog_files_for('plants', id),
            )
        return result
    return render_template(
        'admin_plant_edit.html',
        item=plant,
        is_edit=True,
        form_action=url_for('admin_plants_edit', id=id),
        catalog_files=_catalog_files_for('plants', id),
    )


@app.route('/admin/plants/<int:id>/delete', methods=['POST'])
@admin_required
def admin_plants_delete(id):
    from models import get_plant_by_id
    return _admin_delete_product('plants', id, get_plant_by_id, url_for('admin_plants'), 'Plant')


def _save_tool_food_form(table, add_fn, update_fn, list_route, edit_template, item_label, item_id=None):
    """Process tool/food create/edit form."""
    from models import _update_item_images
    form_data = _parse_catalog_form_fields()
    plant_fields = {k: form_data[k] for k in ('name', 'price', 'category', 'weight', 'description', 'in_stock')}
    if not plant_fields['name'] or not plant_fields['category']:
        item = dict(_blank_catalog_item(), **plant_fields)
        return item, MSG_NAME_CATEGORY_REQUIRED, 'error'
    img1, t1 = _read_uploaded_image('image1')
    img2, t2 = _read_uploaded_image('image2')
    img3, t3 = _read_uploaded_image('image3')
    images = ((img1, t1), (img2, t2), (img3, t3))
    if item_id:
        if not update_fn(item_id, **plant_fields):
            merged = dict(_blank_catalog_item(), **plant_fields)
            merged['id'] = item_id
            return merged, f'Failed to update {table[:-1]}.', 'error'
        _update_item_images(table, item_id, images)
        _process_catalog_file_changes(table, item_id)
        flash(f'{item_label} updated successfully.', 'success')
        return redirect(list_route)
    new_id, err = add_fn(
        plant_fields['name'], plant_fields['price'], plant_fields['category'], plant_fields['description'],
        img1, t1, img2, t2, img3, t3, plant_fields['weight'], plant_fields['in_stock'],
    )
    if new_id:
        _process_catalog_file_changes(table, new_id)
        flash(f'{item_label} added successfully.', 'success')
        return redirect(list_route)
    fail_msg = f'Failed to add {table[:-1]}: {err}' if err else f'Failed to add {table[:-1]}. Check database connection.'
    return dict(_blank_catalog_item(), **plant_fields), fail_msg, 'error'


def _read_uploaded_image(field_name):
    """Read uploaded file and return (bytes, mime_type) or (None, None)."""
    f = request.files.get(field_name)
    if not f or f.filename == '':
        return (None, None)
    data = f.read()
    if not data:
        return (None, None)
    mime = f.content_type or MIME_JPEG
    if mime not in (MIME_JPEG, 'image/png', 'image/gif', 'image/webp'):
        mime = MIME_JPEG
    return (data, mime[:20])


@app.route('/admin/catalog-files/<int:id>')
@admin_required
def serve_catalog_file(id):
    """Download a catalog document attachment."""
    from models import get_product_file_by_id
    record = get_product_file_by_id(id)
    if not record:
        return '', 404
    return Response(
        record['file_data'],
        mimetype=record['file_type'] or 'application/octet-stream',
        headers={'Content-Disposition': f'attachment; filename="{record["file_name"]}"'},
    )


@app.route('/admin/plants/<int:id>/image/<int:slot>')
def serve_plant_image(id, slot):
    """Serve a plant image from the database."""
    from models import get_plant_image
    data, mime = get_plant_image(id, slot)
    if not data:
        return '', 404
    return Response(data, mimetype=mime or MIME_JPEG)


@app.route('/admin/tools', methods=['GET'])
@admin_required
def admin_tools():
    from models import get_tools_paginated
    message, message_type = _admin_list_flash_message('Tool')
    stock = request.args.getlist('stock')
    categories = request.args.getlist('category')
    prices = request.args.getlist('price')
    per_page, page = _resolve_catalog_per_page()
    page_items, total, total_pages, page = get_tools_paginated(
        page, per_page, categories=categories, stock=stock, prices=prices
    )
    _attach_catalog_images(page_items, 'serve_tool_image')
    return render_template(
        'admin_tools.html',
        items=page_items,
        message=message,
        message_type=message_type,
        stock_filter=stock,
        category_filter=categories,
        price_filter=prices,
        page=page,
        total=total,
        total_pages=total_pages,
        per_page=per_page,
        item_label='tool',
    )


@app.route('/admin/tools/new', methods=['GET', 'POST'])
@admin_required
def admin_tools_new():
    from models import add_tool, update_tool
    if request.method == 'POST':
        result = _save_tool_food_form('tools', add_tool, update_tool, url_for('admin_tools'), 'admin_tool_edit.html', 'Tool')
        if isinstance(result, tuple) and len(result) == 3:
            item, message, message_type = result
            return render_template(
                'admin_tool_edit.html',
                item=item,
                is_edit=False,
                form_action=url_for('admin_tools_new'),
                image_route='serve_tool_image',
                message=message,
                message_type=message_type,
                catalog_files=[],
            )
        return result
    return render_template(
        'admin_tool_edit.html',
        item=_blank_catalog_item(),
        is_edit=False,
        form_action=url_for('admin_tools_new'),
        image_route='serve_tool_image',
        catalog_files=[],
    )


@app.route('/admin/tools/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_tools_edit(id):
    from models import add_tool, get_tool_by_id, update_tool
    item = get_tool_by_id(id)
    if not item:
        return redirect(url_for('admin_tools'))
    if request.method == 'POST':
        result = _save_tool_food_form('tools', add_tool, update_tool, url_for('admin_tools'), 'admin_tool_edit.html', 'Tool', id)
        if isinstance(result, tuple) and len(result) == 3:
            err_item, message, message_type = result
            return render_template(
                'admin_tool_edit.html',
                item=err_item or item,
                is_edit=True,
                form_action=url_for('admin_tools_edit', id=id),
                image_route='serve_tool_image',
                message=message,
                message_type=message_type,
                catalog_files=_catalog_files_for('tools', id),
            )
        return result
    return render_template(
        'admin_tool_edit.html',
        item=item,
        is_edit=True,
        form_action=url_for('admin_tools_edit', id=id),
        image_route='serve_tool_image',
        catalog_files=_catalog_files_for('tools', id),
    )


@app.route('/admin/tools/<int:id>/delete', methods=['POST'])
@admin_required
def admin_tools_delete(id):
    from models import get_tool_by_id
    return _admin_delete_product('tools', id, get_tool_by_id, url_for('admin_tools'), 'Tool')


@app.route('/admin/tools/<int:id>/image/<int:slot>')
def serve_tool_image(id, slot):
    """Serve a tool image from the database."""
    from models import get_tool_image
    data, mime = get_tool_image(id, slot)
    if not data:
        return '', 404
    return Response(data, mimetype=mime or MIME_JPEG)


@app.route('/admin/foods', methods=['GET'])
@admin_required
def admin_foods():
    from models import get_foods_paginated
    message, message_type = _admin_list_flash_message('Food')
    stock = request.args.getlist('stock')
    categories = request.args.getlist('category')
    prices = request.args.getlist('price')
    per_page, page = _resolve_catalog_per_page()
    page_items, total, total_pages, page = get_foods_paginated(
        page, per_page, categories=categories, stock=stock, prices=prices
    )
    _attach_catalog_images(page_items, 'serve_food_image')
    return render_template(
        'admin_foods.html',
        items=page_items,
        message=message,
        message_type=message_type,
        stock_filter=stock,
        category_filter=categories,
        price_filter=prices,
        page=page,
        total=total,
        total_pages=total_pages,
        per_page=per_page,
        item_label='food',
    )


@app.route('/admin/foods/new', methods=['GET', 'POST'])
@admin_required
def admin_foods_new():
    from models import add_food, update_food
    if request.method == 'POST':
        result = _save_tool_food_form('foods', add_food, update_food, url_for('admin_foods'), 'admin_food_edit.html', 'Food')
        if isinstance(result, tuple) and len(result) == 3:
            item, message, message_type = result
            return render_template(
                'admin_food_edit.html',
                item=item,
                is_edit=False,
                form_action=url_for('admin_foods_new'),
                image_route='serve_food_image',
                message=message,
                message_type=message_type,
                catalog_files=[],
            )
        return result
    return render_template(
        'admin_food_edit.html',
        item=_blank_catalog_item(),
        is_edit=False,
        form_action=url_for('admin_foods_new'),
        image_route='serve_food_image',
        catalog_files=[],
    )


@app.route('/admin/foods/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_foods_edit(id):
    from models import add_food, get_food_by_id, update_food
    item = get_food_by_id(id)
    if not item:
        return redirect(url_for('admin_foods'))
    if request.method == 'POST':
        result = _save_tool_food_form('foods', add_food, update_food, url_for('admin_foods'), 'admin_food_edit.html', 'Food', id)
        if isinstance(result, tuple) and len(result) == 3:
            err_item, message, message_type = result
            return render_template(
                'admin_food_edit.html',
                item=err_item or item,
                is_edit=True,
                form_action=url_for('admin_foods_edit', id=id),
                image_route='serve_food_image',
                message=message,
                message_type=message_type,
                catalog_files=_catalog_files_for('foods', id),
            )
        return result
    return render_template(
        'admin_food_edit.html',
        item=item,
        is_edit=True,
        form_action=url_for('admin_foods_edit', id=id),
        image_route='serve_food_image',
        catalog_files=_catalog_files_for('foods', id),
    )


@app.route('/admin/foods/<int:id>/delete', methods=['POST'])
@admin_required
def admin_foods_delete(id):
    from models import get_food_by_id
    return _admin_delete_product('foods', id, get_food_by_id, url_for('admin_foods'), 'Food')


@app.route('/admin/foods/<int:id>/image/<int:slot>')
def serve_food_image(id, slot):
    """Serve a food image from the database."""
    from models import get_food_image
    data, mime = get_food_image(id, slot)
    if not data:
        return '', 404
    return Response(data, mimetype=mime or MIME_JPEG)


@app.route('/admin/delivery-prices', methods=['GET', 'POST'])
@admin_required
def admin_delivery_prices():
    from models import get_delivery_base_per_kg, update_delivery_base_per_kg
    base_rule = get_delivery_base_per_kg()
    if not base_rule:
        base_rule = {'max_weight_kg': 1.5, 'base_price': 450, 'extra_per_kg': 100}
    base_rule = {
        'max_weight_kg': float(base_rule['max_weight_kg']),
        'base_price': float(base_rule['base_price']),
        'extra_per_kg': float(base_rule['extra_per_kg']),
    }
    if request.method == 'POST':
        try:
            max_kg = float(request.form.get('max_weight_kg', 1.5) or 1.5)
            base_price = float(request.form.get('base_price', 450) or 450)
            extra = float(request.form.get('extra_per_kg', 100) or 100)
        except ValueError:
            flash('Invalid numbers for base rule.', 'error')
        else:
            if update_delivery_base_per_kg(max_kg, base_price, extra):
                flash('Delivery rule updated.', 'success')
            else:
                flash('Failed to update rule.', 'error')
        return redirect(url_for('admin_delivery_prices'))
    message, message_type = _get_flashed_notice()
    return render_template('admin_delivery_prices.html', base_rule=base_rule, message=message, message_type=message_type or 'success')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='localhost')
