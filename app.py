import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64 MB for image uploads

MSG_NAME_CATEGORY_REQUIRED = 'Name and category are required.'
QUERY_UPDATED = '?updated=1'
MIME_JPEG = 'image/jpeg'


@app.route('/')
def index():
    return render_template('public.html', top_products=get_top_selling())


@app.route('/public')
def public():
    return redirect(url_for('index'))


PLANT_CATEGORIES = [
    'Anubias & Fern', 'Background Plant', 'Bucephalandra', 'Carpeting plant',
    'Cryptocoryne', 'Epiphyte plants', 'Floating plants', 'Ludwigia Varieties',
    'Midground Plant', 'Moss', 'Rare plants', 'Rotala Varieties', 'Other'
]
CO2_OPTIONS = ['High CO2', 'Medium CO2', 'Low CO2']
LIGHT_OPTIONS = ['High Light', 'Medium Light', 'Low Light']
SAMPLE_PLANTS = [
    {'id': i, 'name': f'Aqua Plant {i}', 'price': 4.99 + (i % 5) * 2, 'category': PLANT_CATEGORIES[i % len(PLANT_CATEGORIES)], 'co2_condition': CO2_OPTIONS[i % 3], 'light_condition': LIGHT_OPTIONS[i % 3], 'weight': '', 'image': f'https://picsum.photos/seed/plant{i}/400/400', 'description': 'Beautiful aquatic plant perfect for your aquarium. Easy to care for and thrives in most water conditions.', 'in_stock': i % 10 != 7}
    for i in range(1, 51)
]


@app.route('/aqua-plants')
def aqua_plants():
    from models import get_plants
    co2 = request.args.getlist('co2')
    stock = request.args.getlist('stock')
    plants = get_plants()
    if not plants:
        plants = SAMPLE_PLANTS
    if co2:
        plants = [p for p in plants if (p.get('co2_condition') or '') in co2]
    if stock:
        in_ok = 'in' in stock
        out_ok = 'out' in stock
        if in_ok and not out_ok:
            plants = [p for p in plants if p.get('in_stock', True)]
        elif out_ok and not in_ok:
            plants = [p for p in plants if not p.get('in_stock', True)]
    for p in plants[:12]:
        if 'image' not in p and p.get('has_image1'):
            p['image'] = url_for('serve_plant_image', id=p['id'], slot=1)
        elif 'image' not in p:
            p['image'] = ''
    return render_template('aqua_plants.html', plants=plants[:12], co2_filter=co2, stock_filter=stock)


def get_plant(id):
    for p in SAMPLE_PLANTS:
        if p['id'] == id:
            return p
    return None


@app.route('/aqua-plants/<int:id>')
def plant_detail(id):
    plant = get_plant(id)
    if not plant:
        return redirect(url_for('aqua_plants'))
    return render_template('plant_detail.html', plant=plant)


@app.route('/api/plants')
def api_plants():
    from models import get_plants
    page = request.args.get('page', 1, type=int)
    co2 = request.args.getlist('co2')
    stock = request.args.getlist('stock')
    per_page = 12
    plants = get_plants()
    if not plants:
        plants = SAMPLE_PLANTS
    if co2:
        plants = [p for p in plants if (p.get('co2_condition') or '') in co2]
    if stock:
        in_ok = 'in' in stock
        out_ok = 'out' in stock
        if in_ok and not out_ok:
            plants = [p for p in plants if p.get('in_stock', True)]
        elif out_ok and not in_ok:
            plants = [p for p in plants if not p.get('in_stock', True)]
    start = (page - 1) * per_page
    end = start + per_page
    page_plants = plants[start:end]
    for p in page_plants:
        if 'image' not in p and p.get('has_image1'):
            p['image'] = url_for('serve_plant_image', id=p['id'], slot=1)
        elif 'image' not in p:
            p['image'] = ''
    return jsonify(plants=page_plants, has_more=end < len(plants))


ACCESSORY_CATEGORIES = [
    'Aquarium Soil', 'water Pump', 'Filter Media', 'CO2 accessaries',
    'Fertilizers & Treatment', 'Temperature accessories', 'Air pumps', 'Other product'
]
SAMPLE_ACCESSORIES = [
    {'id': i, 'name': f'Aquarium Accessory {i}', 'price': 5.99 + (i % 6) * 3, 'category': ACCESSORY_CATEGORIES[i % len(ACCESSORY_CATEGORIES)], 'weight': '', 'image': f'https://picsum.photos/seed/acc{i}/400/400', 'description': 'Quality aquarium accessory for your tank. Reliable and durable.', 'in_stock': i % 10 != 3}
    for i in range(1, 51)
]


@app.route('/accessories')
def accessories():
    stock = request.args.getlist('stock')
    items = SAMPLE_ACCESSORIES
    if stock:
        in_ok = 'in' in stock
        out_ok = 'out' in stock
        if in_ok and not out_ok:
            items = [a for a in items if a.get('in_stock', True)]
        elif out_ok and not in_ok:
            items = [a for a in items if not a.get('in_stock', True)]
    return render_template('accessories.html', accessories=items[:12], stock_filter=stock)


def get_accessory(id):
    for a in SAMPLE_ACCESSORIES:
        if a['id'] == id:
            return a
    return None


@app.route('/accessories/<int:id>')
def accessory_detail(id):
    item = get_accessory(id)
    if not item:
        return redirect(url_for('accessories'))
    return render_template('accessory_detail.html', item=item)


@app.route('/api/accessories')
def api_accessories():
    page = request.args.get('page', 1, type=int)
    stock = request.args.getlist('stock')
    per_page = 12
    items = SAMPLE_ACCESSORIES
    if stock:
        in_ok = 'in' in stock
        out_ok = 'out' in stock
        if in_ok and not out_ok:
            items = [a for a in items if a.get('in_stock', True)]
        elif out_ok and not in_ok:
            items = [a for a in items if not a.get('in_stock', True)]
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]
    return jsonify(accessories=page_items, has_more=end < len(items))


SAMPLE_FOODS = [
    {'id': i, 'name': f'Aquarium Food {i}', 'price': 3.99 + (i % 4) * 1.5, 'category': ['Flakes', 'Pellets', 'Freeze-dried', 'Treats'][i % 4], 'weight': '', 'image': f'https://picsum.photos/seed/food{i}/400/400', 'description': f'Nutritional fish food for healthy aquariums. Category: {["flakes", "pellets", "freeze-dried", "treats"][i % 4]}.', 'in_stock': i % 10 != 5}
    for i in range(1, 51)
]


@app.route('/foods')
def foods():
    stock = request.args.getlist('stock')
    items = SAMPLE_FOODS
    if stock:
        in_ok = 'in' in stock
        out_ok = 'out' in stock
        if in_ok and not out_ok:
            items = [f for f in items if f.get('in_stock', True)]
        elif out_ok and not in_ok:
            items = [f for f in items if not f.get('in_stock', True)]
    return render_template('foods.html', foods=items[:12], stock_filter=stock)


def get_food(id):
    for f in SAMPLE_FOODS:
        if f['id'] == id:
            return f
    return None


@app.route('/foods/<int:id>')
def food_detail(id):
    item = get_food(id)
    if not item:
        return redirect(url_for('foods'))
    return render_template('food_detail.html', item=item)


@app.route('/api/foods')
def api_foods():
    page = request.args.get('page', 1, type=int)
    stock = request.args.getlist('stock')
    per_page = 12
    items = SAMPLE_FOODS
    if stock:
        in_ok = 'in' in stock
        out_ok = 'out' in stock
        if in_ok and not out_ok:
            items = [f for f in items if f.get('in_stock', True)]
        elif out_ok and not in_ok:
            items = [f for f in items if not f.get('in_stock', True)]
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]
    return jsonify(foods=page_items, has_more=end < len(items))


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
    items = []
    for p in [SAMPLE_PLANTS[0], SAMPLE_PLANTS[1]]:
        items.append({**p, 'product_type': 'plant'})
    for a in [SAMPLE_ACCESSORIES[0], SAMPLE_ACCESSORIES[1]]:
        items.append({**a, 'product_type': 'accessory'})
    for f in [SAMPLE_FOODS[0], SAMPLE_FOODS[1]]:
        items.append({**f, 'product_type': 'food'})
    return items


@app.route('/tools')
def tools():
    return render_template('tools.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    success = False
    if request.method == 'POST':
        from models import save_contact_message
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        if name and email and subject and message:
            new_id, _ = save_contact_message(name, email, subject, message)
            success = new_id is not None
    return render_template('contact.html', success=success)


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


PER_PAGE_OPTIONS = (10, 15, 20, 25, 50)


@app.route('/admin/messages')
@admin_required
def admin_messages():
    from models import get_contact_messages_paginated
    page = request.args.get('page', 1, type=int)
    per_page_arg = request.args.get('per_page', type=int)
    if per_page_arg is not None and per_page_arg in PER_PAGE_OPTIONS:
        session['messages_per_page'] = per_page_arg
        per_page = per_page_arg
        page = 1
    else:
        per_page = session.get('messages_per_page', 15)
        if per_page not in PER_PAGE_OPTIONS:
            per_page = 15
    messages, total, total_pages, current_page = get_contact_messages_paginated(page, per_page)
    return render_template('admin_messages.html', messages=messages, total=total, total_pages=total_pages, page=current_page, per_page=per_page, per_page_options=PER_PAGE_OPTIONS)


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


def _filter_plants_for_admin(plants, co2, light, stock):
    """Apply co2, light, stock filters to plants. Returns filtered list."""
    if co2:
        plants = [p for p in plants if (p.get('co2_condition') or '') in co2]
    if light:
        plants = [p for p in plants if (p.get('light_condition') or '') in light]
    return _filter_items_by_stock(plants, stock)


def _ensure_plant_images(plants):
    """Add image URL to plants that have has_image1 but no image key."""
    for p in plants:
        if 'image' not in p and p.get('has_image1'):
            p['image'] = url_for('serve_plant_image', id=p['id'], slot=1)
        elif 'image' not in p:
            p['image'] = ''


@app.route('/admin/plants', methods=['GET', 'POST'])
@admin_required
def admin_plants():
    from models import add_plant, get_plants
    message = 'Plant updated successfully.' if request.args.get('updated') else None
    message_type = 'success'
    if request.method == 'POST' and message is None:
        message, message_type = _process_admin_add_form(add_plant, 'Plant')
    co2 = request.args.getlist('co2')
    light = request.args.getlist('light')
    stock = request.args.getlist('stock')
    plants = get_plants() or SAMPLE_PLANTS
    plants = _filter_plants_for_admin(plants, co2, light, stock)
    _ensure_plant_images(plants)
    return render_template('admin_plants.html', plants=plants, message=message, message_type=message_type, co2_filter=co2, light_filter=light, stock_filter=stock)


@app.route('/admin/plants/<int:id>')
@admin_required
def admin_plant_detail(id):
    """Admin view of plant details (like public plant_detail)."""
    from models import get_plant_by_id
    db_plant = get_plant_by_id(id)
    plant = db_plant if db_plant else next((p for p in SAMPLE_PLANTS if p['id'] == id), None)
    if not plant:
        return redirect(url_for('admin_plants'))
    if 'image' not in plant and plant.get('has_image1'):
        plant = dict(plant)
        plant['image'] = url_for('serve_plant_image', id=plant['id'], slot=1)
    elif 'image' not in plant:
        plant = dict(plant)
        plant['image'] = ''
    return render_template('admin_plant_detail.html', plant=plant)


@app.route('/admin/plants/<int:id>/json')
@admin_required
def admin_plant_json(id):
    """Return plant data as JSON for the edit modal."""
    from models import get_plant_by_id
    db_plant = get_plant_by_id(id)
    if not db_plant:
        plant = next((p for p in SAMPLE_PLANTS if p['id'] == id), None)
    else:
        plant = db_plant
    if not plant:
        return jsonify({'error': 'Plant not found'}), 404
    out = {
        'id': plant['id'],
        'name': plant.get('name', ''),
        'price': float(plant.get('price', 0)),
        'category': plant.get('category', ''),
        'weight': plant.get('weight') or '',
        'description': plant.get('description') or '',
        'care_level': plant.get('care_level') or '',
        'co2_condition': plant.get('co2_condition') or '',
        'light_condition': plant.get('light_condition') or '',
        'in_stock': bool(plant.get('in_stock', True)),
        'has_image1': bool(plant.get('has_image1')),
        'has_image2': bool(plant.get('has_image2')),
        'has_image3': bool(plant.get('has_image3')),
    }
    return jsonify(out)


def _parse_plant_edit_form():
    """Parse plant edit form. Returns (form_data_dict, redirect_url, is_ajax)."""
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
    }, url_for('admin_plants') + QUERY_UPDATED, request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _apply_plant_edit_response(plant_id, plant, db_plant, form_data, redirect_url, is_ajax):
    """Apply plant edit and return response. Returns response or None."""
    from models import update_plant
    if db_plant:
        if not update_plant(plant_id, **form_data):
            return None
    else:
        plant.update(form_data)
    return jsonify({'success': True, 'redirect': redirect_url}) if is_ajax else redirect(redirect_url)


@app.route('/admin/plants/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_plants_edit(id):
    from models import get_plant_by_id
    db_plant = get_plant_by_id(id)
    plant = db_plant if db_plant else next((p for p in SAMPLE_PLANTS if p['id'] == id), None)
    if not plant:
        return redirect(url_for('admin_plants'))
    if request.method == 'POST':
        form_data, redirect_url, is_ajax = _parse_plant_edit_form()
        response = _apply_plant_edit_response(id, plant, db_plant, form_data, redirect_url, is_ajax)
        if response is not None:
            return response
    return render_template('admin_plant_edit.html', item=plant)


def _process_admin_add_form(add_fn, item_name):
    """Process add-item form POST. Returns (message, message_type) tuple."""
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    if not name or not category:
        return (MSG_NAME_CATEGORY_REQUIRED, 'error')
    try:
        price_f = float(request.form.get('price', 0) or 0)
    except ValueError:
        price_f = 0.0
    description = request.form.get('description', '').strip()
    weight = request.form.get('weight', '').strip()
    in_stock = request.form.get('in_stock') == '1'
    care_level = request.form.get('care_level', '').strip() or None
    co2_condition = request.form.get('co2_condition', '').strip() or None
    light_condition = request.form.get('light_condition', '').strip() or None
    img1, img1_type = _read_uploaded_image('image1')
    img2, img2_type = _read_uploaded_image('image2')
    img3, img3_type = _read_uploaded_image('image3')
    images = ((img1, img1_type), (img2, img2_type), (img3, img3_type))
    if add_fn.__name__ == 'add_plant':
        new_id, err = add_fn(name, price_f, category, description, images=images, weight=weight, in_stock=in_stock, care_level=care_level, co2_condition=co2_condition, light_condition=light_condition)
    else:
        new_id, err = add_fn(name, price_f, category, description, img1, img1_type, img2, img2_type, img3, img3_type, weight, in_stock)
    if new_id:
        return (f'{item_name} "{name}" added successfully.', 'success')
    fail_msg = f'Failed to add {item_name.lower()}: {err}' if err else f'Failed to add {item_name.lower()}. Check database connection.'
    return (fail_msg, 'error')


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


@app.route('/admin/plants/<int:id>/image/<int:slot>')
def serve_plant_image(id, slot):
    """Serve a plant image from the database."""
    from models import get_plant_image
    data, mime = get_plant_image(id, slot)
    if not data:
        return '', 404
    return Response(data, mimetype=mime or MIME_JPEG)


@app.route('/admin/tools', methods=['GET', 'POST'])
@admin_required
def admin_tools():
    from models import add_tool
    message = 'Tool updated successfully.' if request.args.get('updated') else None
    message_type = 'success'
    if request.method == 'POST' and message is None:
        message, message_type = _process_admin_add_form(add_tool, 'Tool')
    stock = request.args.getlist('stock')
    items = SAMPLE_ACCESSORIES
    if stock:
        in_ok = 'in' in stock
        out_ok = 'out' in stock
        if in_ok and not out_ok:
            items = [a for a in items if a.get('in_stock', True)]
        elif out_ok and not in_ok:
            items = [a for a in items if not a.get('in_stock', True)]
    return render_template('admin_tools.html', items=items, message=message, message_type=message_type, stock_filter=stock)


@app.route('/admin/tools/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_tools_edit(id):
    item = next((a for a in SAMPLE_ACCESSORIES if a['id'] == id), None)
    if not item:
        return redirect(url_for('admin_tools'))
    if request.method == 'POST':
        item['name'] = request.form.get('name', '').strip()
        item['price'] = float(request.form.get('price', 0) or 0)
        item['category'] = request.form.get('category', '').strip()
        item['weight'] = request.form.get('weight', '').strip()
        item['description'] = request.form.get('description', '').strip()
        item['in_stock'] = request.form.get('in_stock') == '1'
        return redirect(url_for('admin_tools') + QUERY_UPDATED)
    return render_template('admin_tool_edit.html', item=item)


@app.route('/admin/tools/<int:id>/image/<int:slot>')
def serve_tool_image(id, slot):
    """Serve a tool image from the database."""
    from models import get_tool_image
    data, mime = get_tool_image(id, slot)
    if not data:
        return '', 404
    return Response(data, mimetype=mime or MIME_JPEG)


@app.route('/admin/foods', methods=['GET', 'POST'])
@admin_required
def admin_foods():
    from models import add_food
    message = 'Food updated successfully.' if request.args.get('updated') else None
    message_type = 'success'
    if request.method == 'POST' and message is None:
        message, message_type = _process_admin_add_form(add_food, 'Food')
    stock = request.args.getlist('stock')
    items = SAMPLE_FOODS
    if stock:
        in_ok = 'in' in stock
        out_ok = 'out' in stock
        if in_ok and not out_ok:
            items = [f for f in items if f.get('in_stock', True)]
        elif out_ok and not in_ok:
            items = [f for f in items if not f.get('in_stock', True)]
    return render_template('admin_foods.html', items=items, message=message, message_type=message_type, stock_filter=stock)


@app.route('/admin/foods/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_foods_edit(id):
    item = next((f for f in SAMPLE_FOODS if f['id'] == id), None)
    if not item:
        return redirect(url_for('admin_foods'))
    if request.method == 'POST':
        item['name'] = request.form.get('name', '').strip()
        item['price'] = float(request.form.get('price', 0) or 0)
        item['category'] = request.form.get('category', '').strip()
        item['weight'] = request.form.get('weight', '').strip()
        item['description'] = request.form.get('description', '').strip()
        item['in_stock'] = request.form.get('in_stock') == '1'
        return redirect(url_for('admin_foods') + QUERY_UPDATED)
    return render_template('admin_food_edit.html', item=item)


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
    message = None
    message_type = 'success'
    base_rule = get_delivery_base_per_kg()
    if not base_rule:
        base_rule = {'max_weight_kg': 1.5, 'base_price': 450, 'extra_per_kg': 100}
    if request.method == 'POST':
        try:
            max_kg = float(request.form.get('max_weight_kg', 1.5) or 1.5)
            base_price = float(request.form.get('base_price', 450) or 450)
            extra = float(request.form.get('extra_per_kg', 100) or 100)
        except ValueError:
            message = 'Invalid numbers for base rule.'
            message_type = 'error'
        else:
            if update_delivery_base_per_kg(max_kg, base_price, extra):
                message = 'Delivery rule updated.'
                base_rule = get_delivery_base_per_kg() or base_rule
            else:
                message = 'Failed to update rule.'
                message_type = 'error'
    return render_template('admin_delivery_prices.html', base_rule=base_rule, message=message, message_type=message_type or 'success')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
