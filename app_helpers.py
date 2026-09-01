"""Helper functions used by app.py routes."""
import os
from functools import wraps
from urllib.parse import urlencode

from flask import current_app, flash, get_flashed_messages, redirect, request, session, url_for

MSG_NAME_CATEGORY_REQUIRED = 'Name and category are required.'
MIME_JPEG = 'image/jpeg'
CATALOG_PER_PAGE_DEFAULT = 20
CATALOG_PER_PAGE_OPTIONS = (10, 20, 50)
PER_PAGE_OPTIONS = (5, 10, 20, 50)

CATALOG_TABLE_TYPES = {
    'plants': 'plant',
    'tools': 'tool',
    'foods': 'food',
}
CATALOG_TYPE_TO_TABLE = {value: key for key, value in CATALOG_TABLE_TYPES.items()}

ALLOWED_CATALOG_DOC_EXTENSIONS = {'.txt', '.csv', '.md'}
ALLOWED_CATALOG_DOC_MIMES = {
    'text/plain', 'text/csv', 'text/markdown',
}

HOME_TOP_SELLING_IMAGES = {
    'plant': 'images/home/top-plant.jpg',
    'accessory': 'images/home/top-accessory.jpg',
    'food': 'images/home/top-food.jpg',
}

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


def register_template_helpers(app):
    """Adds page links and filter lists to every HTML page."""
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


def _resolve_catalog_per_page():
    """Figures out how many items to show per page. Remembers what the user picked."""
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
    """Gets the saved page size for the current admin list."""
    if request.path.startswith('/admin/orders'):
        return session.get('orders_per_page', 10)
    if request.path.startswith('/admin/messages'):
        return session.get('messages_per_page', 10)
    return session.get('catalog_per_page', CATALOG_PER_PAGE_DEFAULT)


def _resolve_admin_per_page(session_key, default, options):
    """Same idea as catalog pages but for admin orders and messages lists."""
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


def _attach_catalog_images(items, endpoint):
    """Adds a photo link to each product in a list if it has one."""
    for item in items:
        if item.get('has_image1'):
            item['image'] = url_for(endpoint, id=item['id'], slot=1)
        else:
            item['image'] = ''


def _attach_order_item_images(items):
    """Adds photos to each item on an order page."""
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
    """Builds the photo gallery for a single product page."""
    images = []
    for slot in (1, 2, 3):
        if item.get(f'has_image{slot}'):
            images.append({
                'slot': slot,
                'url': url_for(endpoint, id=item['id'], slot=slot),
            })
    item['images'] = images
    item['image'] = images[0]['url'] if images else ''


def _home_top_static_image(product_type):
    """Gets the image file for a featured product on the home page if it exists."""
    rel = HOME_TOP_SELLING_IMAGES.get(product_type)
    if not rel:
        return None
    static_root = os.path.join(current_app.root_path, 'static')
    base, ext = os.path.splitext(rel)
    for candidate_ext in (ext, '.jpg', '.jpeg', '.png', '.webp'):
        candidate = base + candidate_ext if candidate_ext != ext else rel
        if os.path.isfile(os.path.join(static_root, candidate)):
            return url_for('static', filename=candidate.replace('\\', '/'))
    return None


def get_top_selling():
    """Picks one featured plant, accessory, and food to show on the home page."""
    from models import get_foods, get_plants, get_tools

    def pick_second(rows):
        if not rows:
            return None
        return rows[1] if len(rows) > 1 else rows[0]

    items = []
    for get_list, endpoint, product_type in (
        (get_plants, 'serve_plant_image', 'plant'),
        (get_tools, 'serve_tool_image', 'accessory'),
        (get_foods, 'serve_food_image', 'food'),
    ):
        item = pick_second(get_list())
        if not item:
            continue
        item['image'] = _home_top_static_image(product_type) or ''
        if not item['image']:
            _attach_catalog_images([item], endpoint)
        items.append({**item, 'product_type': product_type})
    return items


def _first_item_image_url(items, endpoint):
    """Finds the first product in a list that has a photo."""
    for item in items:
        if item.get('has_image1'):
            return url_for(endpoint, id=item['id'], slot=1)
    return None


def get_category_preview_images():
    """Gets one sample photo for each shop category on the home page."""
    from models import get_foods, get_plants, get_tools

    return {
        'plants': _first_item_image_url(get_plants(), 'serve_plant_image'),
        'tools': _first_item_image_url(get_tools(), 'serve_tool_image'),
        'foods': _first_item_image_url(get_foods(), 'serve_food_image'),
    }


def admin_required(f):
    """Blocks admin pages if the user is not logged in."""
    @wraps(f)
    def inner(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return inner


def _ensure_plant_images(plants):
    """Makes sure each plant in the list has an image field."""
    _attach_catalog_images(plants, 'serve_plant_image')


def _read_uploaded_image(field_name):
    """Reads one uploaded image from the form. Returns nothing if empty."""
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


def _blank_catalog_item():
    """Empty form values for adding or editing a product."""
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
    """Reads all three image upload slots from the form."""
    img1, img1_type = _read_uploaded_image('image1')
    img2, img2_type = _read_uploaded_image('image2')
    img3, img3_type = _read_uploaded_image('image3')
    return ((img1, img1_type), (img2, img2_type), (img3, img3_type))


def _parse_catalog_form_fields():
    """Reads name, price, category and other fields from the form."""
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
    """Checks if an uploaded file is a text document we allow."""
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
    """Gets the list of attached documents for a product edit page."""
    if not item_id:
        return []
    from models import get_product_files
    return get_product_files(CATALOG_TABLE_TYPES[table], item_id)


def _catalog_rag_meta(table, item_id=None):
    """Gets how many document pieces are saved and when they were last updated."""
    if not item_id:
        return {'chunk_count': 0, 'indexed_at': None}
    from models import get_rag_index_meta
    return get_rag_index_meta(CATALOG_TABLE_TYPES[table], item_id)


def _process_catalog_file_changes(table, item_id):
    """Handles uploading new documents or deleting old ones when a product is saved."""
    from models import add_product_file, delete_product_files
    from werkzeug.utils import secure_filename

    product_type = CATALOG_TABLE_TYPES[table]
    delete_ids = []
    for raw_id in request.form.getlist('delete_file_ids[]') or request.form.getlist('delete_file_ids'):
        try:
            delete_ids.append(int(raw_id))
        except (TypeError, ValueError):
            pass
    deleted_count = 0
    if delete_ids:
        deleted_count = delete_product_files(product_type, item_id, delete_ids)

    uploaded_count = 0
    uploads = request.files.getlist('catalog_documents[]') or request.files.getlist('catalog_documents')
    for upload in uploads:
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
        uploaded_count += 1
    return uploaded_count, deleted_count


def _auto_index_product_rag(table, item_id):
    """Rebuilds the chatbot search after documents change. Clears everything if all files were removed."""
    from models import delete_rag_chunks_for_product, get_product_files
    from rag_service import index_product

    product_type = CATALOG_TABLE_TYPES[table]
    if not get_product_files(product_type, item_id):
        delete_rag_chunks_for_product(product_type, item_id)
        return 0, None

    chunk_count, error = index_product(product_type, item_id)
    if error:
        return None, error
    return chunk_count, None


def _flash_catalog_save_message(item_label, action, table, item_id, uploaded_count, deleted_count):
    """Shows a success or error message after saving a product."""
    docs_changed = uploaded_count > 0 or deleted_count > 0
    if not docs_changed:
        flash(f'{item_label} {action} successfully.', 'success')
        return

    chunk_count, index_error = _auto_index_product_rag(table, item_id)
    if index_error:
        flash(
            f'{item_label} {action}. Documents saved but indexing failed: {index_error}',
            'error',
        )
    elif chunk_count == 0:
        flash(f'{item_label} {action}. Documents removed and search index cleared.', 'success')
    else:
        plural = 's' if chunk_count != 1 else ''
        flash(
            f'{item_label} {action}. Documents saved and indexed ({chunk_count} chunk{plural}).',
            'success',
        )


def _get_flashed_notice(default_type='success'):
    """Gets one message to show the user. It only shows once."""
    messages = get_flashed_messages(with_categories=True)
    if messages:
        category, message = messages[0]
        return message, category
    return None, default_type


def _admin_list_flash_message(item_label):
    """Gets the message to show on an admin list page after a redirect."""
    message, category = _get_flashed_notice()
    if message:
        return message, category
    return None, 'success'


def _admin_delete_product(table, item_id, get_by_id, list_route, item_label):
    """Deletes a product and shows if it worked or not."""
    from models import delete_item

    if not get_by_id(item_id):
        return redirect(list_route)
    if delete_item(table, item_id):
        flash(f'{item_label} deleted successfully.', 'success')
        return redirect(list_route)
    flash(f'Failed to delete {item_label.lower()}.', 'error')
    return redirect(list_route)


def _save_plant_form(item_id=None):
    """Saves a plant when the admin submits the add or edit form."""
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
        uploaded_count, deleted_count = _process_catalog_file_changes('plants', item_id)
        _flash_catalog_save_message('Plant', 'updated', 'plants', item_id, uploaded_count, deleted_count)
        return redirect(url_for('admin_plants_edit', id=item_id))
    new_id, err = add_plant(
        form_data['name'], form_data['price'], form_data['category'], form_data['description'],
        images=images, weight=form_data['weight'], in_stock=form_data['in_stock'],
        care_level=form_data['care_level'], co2_condition=form_data['co2_condition'],
        light_condition=form_data['light_condition'],
    )
    if new_id:
        uploaded_count, deleted_count = _process_catalog_file_changes('plants', new_id)
        _flash_catalog_save_message('Plant', 'added', 'plants', new_id, uploaded_count, deleted_count)
        return redirect(url_for('admin_plants_edit', id=new_id))
    fail_msg = f'Failed to add plant: {err}' if err else 'Failed to add plant. Check database connection.'
    item = dict(_blank_catalog_item(), **form_data)
    item['care_level'] = form_data.get('care_level') or ''
    item['co2_condition'] = form_data.get('co2_condition') or ''
    item['light_condition'] = form_data.get('light_condition') or ''
    return item, fail_msg, 'error'


def _save_tool_food_form(table, add_fn, update_fn, list_route, edit_route, edit_template, item_label, item_id=None):
    """Same as plant save but for tools and foods."""
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
        uploaded_count, deleted_count = _process_catalog_file_changes(table, item_id)
        _flash_catalog_save_message(item_label, 'updated', table, item_id, uploaded_count, deleted_count)
        return redirect(url_for(edit_route, id=item_id))
    new_id, err = add_fn(
        plant_fields['name'], plant_fields['price'], plant_fields['category'], plant_fields['description'],
        img1, t1, img2, t2, img3, t3, plant_fields['weight'], plant_fields['in_stock'],
    )
    if new_id:
        uploaded_count, deleted_count = _process_catalog_file_changes(table, new_id)
        _flash_catalog_save_message(item_label, 'added', table, new_id, uploaded_count, deleted_count)
        return redirect(url_for(edit_route, id=new_id))
    fail_msg = f'Failed to add {table[:-1]}: {err}' if err else f'Failed to add {table[:-1]}. Check database connection.'
    return dict(_blank_catalog_item(), **plant_fields), fail_msg, 'error'
