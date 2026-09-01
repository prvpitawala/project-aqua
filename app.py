"""
Main app file for AquaStore.
Connects the shop pages, checkout, admin area, and product chatbot.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response, flash

from app_helpers import (
    CATALOG_TYPE_TO_TABLE,
    MIME_JPEG,
    PER_PAGE_OPTIONS,
    admin_required,
    get_category_preview_images,
    get_top_selling,
    register_template_helpers,
    _admin_delete_product,
    _admin_list_flash_message,
    _attach_catalog_detail_images,
    _attach_catalog_images,
    _attach_order_item_images,
    _auto_index_product_rag,
    _blank_catalog_item,
    _catalog_files_for,
    _catalog_rag_meta,
    _ensure_plant_images,
    _get_flashed_notice,
    _resolve_admin_per_page,
    _resolve_catalog_per_page,
    _save_plant_form,
    _save_tool_food_form,
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024  # 64 MB — enough for multi-image product uploads

register_template_helpers(app)

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
)

# --- Public pages ---

@app.route('/')
def index():
    """Home page with featured products and customer reviews."""
    return render_template(
        'public.html',
        top_products=get_top_selling(),
        category_images=get_category_preview_images(),
        testimonials=HOME_TESTIMONIALS,
    )


@app.route('/public')
def public():
    """Old link that sends people to the main home page."""
    return redirect(url_for('index'))


# --- Public catalog pages (HTML) ---

@app.route('/aqua-plants')
def aqua_plants():
    """Shop page for browsing plants with filters."""
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
    """One plant page with photos, info, and chatbot."""
    from models import get_plant_by_id
    plant = get_plant_by_id(id)
    if not plant:
        return redirect(url_for('aqua_plants'))
    _attach_catalog_detail_images(plant, 'serve_plant_image')
    return render_template('plant_detail.html', plant=plant)


# --- Public API ---

@app.route('/api/plants')
def api_plants():
    """Sends plant list as JSON for loading more on the page."""
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
    """Shop page for browsing accessories."""
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
    """One accessory page with photos and chatbot."""
    from models import get_tool_by_id
    item = get_tool_by_id(id)
    if not item:
        return redirect(url_for('accessories'))
    _attach_catalog_detail_images(item, 'serve_tool_image')
    return render_template('accessory_detail.html', item=item)


@app.route('/api/accessories')
def api_accessories():
    """Sends accessory list as JSON for loading more on the page."""
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
    """Shop page for browsing fish food."""
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
    """One food page with photos and chatbot."""
    from models import get_food_by_id
    item = get_food_by_id(id)
    if not item:
        return redirect(url_for('foods'))
    _attach_catalog_detail_images(item, 'serve_food_image')
    return render_template('food_detail.html', item=item)


@app.route('/api/foods')
def api_foods():
    """Sends food list as JSON for loading more on the page."""
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
    """Returns delivery price info for the checkout cart."""
    from models import get_delivery_base_per_kg
    rule = get_delivery_base_per_kg()
    if not rule:
        return jsonify(base_price=450, extra_per_kg=100)
    return jsonify(base_price=float(rule['base_price']), extra_per_kg=float(rule['extra_per_kg']))


@app.route('/tools')
def tools():
    """Extra tools page. The main shop uses the accessories page instead."""
    return render_template('tools.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact form page. Saves messages for admin to read."""
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
    """Checkout page where customers place their order."""
    return render_template('checkout.html')


@app.route('/api/orders', methods=['POST'])
def api_create_order():
    """Saves a new order from the checkout page."""
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


# --- Auth ---

@app.route('/signin')
def signin():
    """Opens admin login or goes to dashboard if already logged in."""
    if session.get('admin'):
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('index') + '?open=signin')


@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Checks admin username and password and logs them in."""
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if username and password:
        from models import verify_admin
        if verify_admin(username, password):
            session['admin'] = True
            return jsonify(success=True, redirect=url_for('admin_dashboard'))
    return jsonify(success=False, error='Invalid username or password'), 401


# --- Admin area ---

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Main admin page with links to manage the store."""
    return render_template('admin_dashboard.html')


@app.route('/admin/messages')
@admin_required
def admin_messages():
    """Shows messages customers sent through the contact form."""
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
    """Saves an admin reply to a customer message."""
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
    """Shows all customer orders."""
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
    """Shows one order with all details."""
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
    """Updates if an order is pending, shipped, etc."""
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


# --- Admin catalog (plants, tools, foods) ---

@app.route('/admin/plants', methods=['GET'])
@admin_required
def admin_plants():
    """Admin page to view and manage plants."""
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
    """Admin preview of one plant page."""
    from models import get_plant_by_id
    plant = get_plant_by_id(id)
    if not plant:
        return redirect(url_for('admin_plants'))
    _attach_catalog_images([plant], 'serve_plant_image')
    return render_template('admin_plant_detail.html', plant=plant)


@app.route('/admin/plants/new', methods=['GET', 'POST'])
@admin_required
def admin_plants_new():
    """Form to add a new plant."""
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
    """Form to edit a plant, its photos, and documents."""
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
                rag_index_meta=_catalog_rag_meta('plants', id),
                rag_product_type='plant',
            )
        return result
    return render_template(
        'admin_plant_edit.html',
        item=plant,
        is_edit=True,
        form_action=url_for('admin_plants_edit', id=id),
        catalog_files=_catalog_files_for('plants', id),
        rag_index_meta=_catalog_rag_meta('plants', id),
        rag_product_type='plant',
    )


@app.route('/admin/plants/<int:id>/delete', methods=['POST'])
@admin_required
def admin_plants_delete(id):
    """Deletes a plant."""
    from models import get_plant_by_id
    return _admin_delete_product('plants', id, get_plant_by_id, url_for('admin_plants'), 'Plant')


# --- Catalog documents & RAG ---

@app.route('/admin/catalog-files/<int:id>')
@admin_required
def serve_catalog_file(id):
    """Lets admin download an attached document."""
    from models import get_product_file_by_id
    record = get_product_file_by_id(id)
    if not record:
        return '', 404
    return Response(
        record['file_data'],
        mimetype=record['file_type'] or 'application/octet-stream',
        headers={'Content-Disposition': f'attachment; filename="{record["file_name"]}"'},
    )


@app.route('/admin/api/catalog/files/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_catalog_file(id):
    """Deletes one document and updates the chatbot search."""
    from models import delete_product_files, get_product_file_by_id

    record = get_product_file_by_id(id)
    if not record:
        return jsonify(success=False, error='File not found.'), 404

    product_type = record['product_type']
    product_id = record['product_id']
    table = CATALOG_TYPE_TO_TABLE.get(product_type)
    if not table:
        return jsonify(success=False, error='Invalid file record.'), 400

    if not delete_product_files(product_type, product_id, [id]):
        return jsonify(success=False, error='Could not delete file.'), 400

    chunk_count, index_error = _auto_index_product_rag(table, product_id)
    if index_error:
        return jsonify(
            success=True,
            warning=f'File deleted but re-index failed: {index_error}',
            chunk_count=0,
        )

    return jsonify(success=True, chunk_count=chunk_count or 0)


@app.route('/admin/api/rag/index', methods=['POST'])
@admin_required
def admin_rag_index():
    """Manually refreshes the chatbot documents for one product."""
    from rag_service import index_product, normalize_product_type

    data = request.get_json(silent=True) or {}
    product_type = normalize_product_type(data.get('product_type') or request.form.get('product_type'))
    product_id = data.get('product_id') or request.form.get('product_id')

    chunk_count, error = index_product(product_type, product_id)
    if error:
        return jsonify(success=False, error=error), 400

    from models import get_rag_index_meta
    meta = get_rag_index_meta(product_type, int(product_id))
    indexed_at = meta['indexed_at'].isoformat() if meta.get('indexed_at') else None
    return jsonify(
        success=True,
        chunk_count=chunk_count,
        indexed_at=indexed_at,
    )


@app.route('/api/rag/chat', methods=['POST'])
def api_rag_chat():
    """Chatbot that answers questions about one product using its documents."""
    from rag_service import answer_question, normalize_product_type

    data = request.get_json(silent=True) or {}
    product_type = normalize_product_type(data.get('product_type'))
    product_id = data.get('product_id')
    product_name = (data.get('product_name') or '').strip()
    message = (data.get('message') or '').strip()

    if not product_type or product_id is None:
        return jsonify(success=False, error='Product context is required.'), 400

    answer, error = answer_question(product_type, product_id, product_name, message)
    if error:
        return jsonify(success=False, error=error), 400
    return jsonify(success=True, answer=answer)


@app.route('/admin/plants/<int:id>/image/<int:slot>')
def serve_plant_image(id, slot):
    """Shows a plant photo from the database."""
    from models import get_plant_image
    data, mime = get_plant_image(id, slot)
    if not data:
        return '', 404
    return Response(data, mimetype=mime or MIME_JPEG)


@app.route('/admin/tools', methods=['GET'])
@admin_required
def admin_tools():
    """Admin page to view and manage tools and accessories."""
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
    """Form to add a new tool or accessory."""
    from models import add_tool, update_tool
    if request.method == 'POST':
        result = _save_tool_food_form('tools', add_tool, update_tool, url_for('admin_tools'), 'admin_tools_edit', 'admin_tool_edit.html', 'Tool')
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
    """Form to edit a tool, its photos, and documents."""
    from models import add_tool, get_tool_by_id, update_tool
    item = get_tool_by_id(id)
    if not item:
        return redirect(url_for('admin_tools'))
    if request.method == 'POST':
        result = _save_tool_food_form('tools', add_tool, update_tool, url_for('admin_tools'), 'admin_tools_edit', 'admin_tool_edit.html', 'Tool', id)
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
                rag_index_meta=_catalog_rag_meta('tools', id),
                rag_product_type='tool',
            )
        return result
    return render_template(
        'admin_tool_edit.html',
        item=item,
        is_edit=True,
        form_action=url_for('admin_tools_edit', id=id),
        image_route='serve_tool_image',
        catalog_files=_catalog_files_for('tools', id),
        rag_index_meta=_catalog_rag_meta('tools', id),
        rag_product_type='tool',
    )


@app.route('/admin/tools/<int:id>/delete', methods=['POST'])
@admin_required
def admin_tools_delete(id):
    """Deletes a tool."""
    from models import get_tool_by_id
    return _admin_delete_product('tools', id, get_tool_by_id, url_for('admin_tools'), 'Tool')


@app.route('/admin/tools/<int:id>/image/<int:slot>')
def serve_tool_image(id, slot):
    """Shows a tool or accessory photo from the database."""
    from models import get_tool_image
    data, mime = get_tool_image(id, slot)
    if not data:
        return '', 404
    return Response(data, mimetype=mime or MIME_JPEG)


@app.route('/admin/foods', methods=['GET'])
@admin_required
def admin_foods():
    """Admin page to view and manage fish food."""
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
    """Form to add new fish food."""
    from models import add_food, update_food
    if request.method == 'POST':
        result = _save_tool_food_form('foods', add_food, update_food, url_for('admin_foods'), 'admin_foods_edit', 'admin_food_edit.html', 'Food')
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
    """Form to edit food, its photos, and documents."""
    from models import add_food, get_food_by_id, update_food
    item = get_food_by_id(id)
    if not item:
        return redirect(url_for('admin_foods'))
    if request.method == 'POST':
        result = _save_tool_food_form('foods', add_food, update_food, url_for('admin_foods'), 'admin_foods_edit', 'admin_food_edit.html', 'Food', id)
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
                rag_index_meta=_catalog_rag_meta('foods', id),
                rag_product_type='food',
            )
        return result
    return render_template(
        'admin_food_edit.html',
        item=item,
        is_edit=True,
        form_action=url_for('admin_foods_edit', id=id),
        image_route='serve_food_image',
        catalog_files=_catalog_files_for('foods', id),
        rag_index_meta=_catalog_rag_meta('foods', id),
        rag_product_type='food',
    )


@app.route('/admin/foods/<int:id>/delete', methods=['POST'])
@admin_required
def admin_foods_delete(id):
    """Deletes a food product."""
    from models import get_food_by_id
    return _admin_delete_product('foods', id, get_food_by_id, url_for('admin_foods'), 'Food')


@app.route('/admin/foods/<int:id>/image/<int:slot>')
def serve_food_image(id, slot):
    """Shows a food product photo from the database."""
    from models import get_food_image
    data, mime = get_food_image(id, slot)
    if not data:
        return '', 404
    return Response(data, mimetype=mime or MIME_JPEG)


@app.route('/admin/delivery-prices', methods=['GET', 'POST'])
@admin_required
def admin_delivery_prices():
    """Admin page to set delivery fees."""
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
    """Logs the admin out."""
    session.pop('admin', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='localhost')
