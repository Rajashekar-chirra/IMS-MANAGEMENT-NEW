from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from app import db
from models import Category, SubCategory, Brand, Vendor, Item

masters_bp = Blueprint('masters', __name__)


# ─── CATEGORIES ───────────────────────────────────────────────────────────────

@masters_bp.route('/categories')
@login_required
def categories():
    q = request.args.get('q', '')
    query = Category.query
    if q:
        query = query.filter(Category.category_name.ilike(f'%{q}%'))
    cats = query.order_by(Category.category_name).all()
    return render_template('masters/categories.html', categories=cats, q=q, active_page='masters')


@masters_bp.route('/categories/add', methods=['POST'])
@login_required
def add_category():
    name = request.form.get('category_name', '').strip()
    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('masters.categories'))
    if Category.query.filter_by(category_name=name).first():
        flash('Category already exists.', 'warning')
        return redirect(url_for('masters.categories'))
    db.session.add(Category(category_name=name))
    db.session.commit()
    flash('Category added successfully.', 'success')
    return redirect(url_for('masters.categories'))


@masters_bp.route('/categories/edit/<int:id>', methods=['POST'])
@login_required
def edit_category(id):
    cat = Category.query.get_or_404(id)
    name = request.form.get('category_name', '').strip()
    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('masters.categories'))
    cat.category_name = name
    db.session.commit()
    flash('Category updated.', 'success')
    return redirect(url_for('masters.categories'))


@masters_bp.route('/categories/delete/<int:id>', methods=['POST'])
@login_required
def delete_category(id):
    cat = Category.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    flash('Category deleted.', 'success')
    return redirect(url_for('masters.categories'))


# ─── SUBCATEGORIES ────────────────────────────────────────────────────────────

@masters_bp.route('/subcategories')
@login_required
def subcategories():
    q = request.args.get('q', '')
    query = SubCategory.query
    if q:
        query = query.filter(SubCategory.subcategory_name.ilike(f'%{q}%'))
    subcats = query.order_by(SubCategory.subcategory_name).all()
    categories = Category.query.order_by(Category.category_name).all()
    return render_template('masters/subcategories.html', subcategories=subcats, categories=categories, q=q, active_page='masters')


@masters_bp.route('/subcategories/add', methods=['POST'])
@login_required
def add_subcategory():
    name = request.form.get('subcategory_name', '').strip()
    cat_id = request.form.get('category_id')
    if not name or not cat_id:
        flash('All fields are required.', 'danger')
        return redirect(url_for('masters.subcategories'))
    db.session.add(SubCategory(subcategory_name=name, category_id=int(cat_id)))
    db.session.commit()
    flash('Sub-Category added.', 'success')
    return redirect(url_for('masters.subcategories'))


@masters_bp.route('/subcategories/edit/<int:id>', methods=['POST'])
@login_required
def edit_subcategory(id):
    sc = SubCategory.query.get_or_404(id)
    sc.subcategory_name = request.form.get('subcategory_name', sc.subcategory_name).strip()
    sc.category_id = int(request.form.get('category_id', sc.category_id))
    db.session.commit()
    flash('Sub-Category updated.', 'success')
    return redirect(url_for('masters.subcategories'))


@masters_bp.route('/subcategories/delete/<int:id>', methods=['POST'])
@login_required
def delete_subcategory(id):
    sc = SubCategory.query.get_or_404(id)
    db.session.delete(sc)
    db.session.commit()
    flash('Sub-Category deleted.', 'success')
    return redirect(url_for('masters.subcategories'))


# ─── BRANDS ───────────────────────────────────────────────────────────────────

@masters_bp.route('/brands')
@login_required
def brands():
    q = request.args.get('q', '')
    query = Brand.query
    if q:
        query = query.filter(Brand.brand_name.ilike(f'%{q}%'))
    brands_list = query.order_by(Brand.brand_name).all()
    return render_template('masters/brands.html', brands=brands_list, q=q, active_page='masters')


@masters_bp.route('/brands/add', methods=['POST'])
@login_required
def add_brand():
    name = request.form.get('brand_name', '').strip()
    if not name:
        flash('Brand name is required.', 'danger')
        return redirect(url_for('masters.brands'))
    if Brand.query.filter_by(brand_name=name).first():
        flash('Brand already exists.', 'warning')
        return redirect(url_for('masters.brands'))
    db.session.add(Brand(brand_name=name))
    db.session.commit()
    flash('Brand added.', 'success')
    return redirect(url_for('masters.brands'))


@masters_bp.route('/brands/edit/<int:id>', methods=['POST'])
@login_required
def edit_brand(id):
    brand = Brand.query.get_or_404(id)
    brand.brand_name = request.form.get('brand_name', brand.brand_name).strip()
    db.session.commit()
    flash('Brand updated.', 'success')
    return redirect(url_for('masters.brands'))


@masters_bp.route('/brands/delete/<int:id>', methods=['POST'])
@login_required
def delete_brand(id):
    brand = Brand.query.get_or_404(id)
    db.session.delete(brand)
    db.session.commit()
    flash('Brand deleted.', 'success')
    return redirect(url_for('masters.brands'))


# ─── VENDORS ──────────────────────────────────────────────────────────────────

@masters_bp.route('/vendors')
@login_required
def vendors():
    q = request.args.get('q', '')
    query = Vendor.query
    if q:
        query = query.filter(Vendor.vendor_name.ilike(f'%{q}%'))
    vendors_list = query.order_by(Vendor.vendor_name).all()
    return render_template('masters/vendors.html', vendors=vendors_list, q=q, active_page='masters')


@masters_bp.route('/vendors/add', methods=['POST'])
@login_required
def add_vendor():
    name = request.form.get('vendor_name', '').strip()
    mobile = request.form.get('mobile', '').strip()
    address = request.form.get('address', '').strip()
    if not name:
        flash('Vendor name is required.', 'danger')
        return redirect(url_for('masters.vendors'))
    db.session.add(Vendor(vendor_name=name, mobile=mobile, address=address))
    db.session.commit()
    flash('Vendor added.', 'success')
    return redirect(url_for('masters.vendors'))


@masters_bp.route('/vendors/edit/<int:id>', methods=['POST'])
@login_required
def edit_vendor(id):
    v = Vendor.query.get_or_404(id)
    v.vendor_name = request.form.get('vendor_name', v.vendor_name).strip()
    v.mobile = request.form.get('mobile', v.mobile)
    v.address = request.form.get('address', v.address)
    db.session.commit()
    flash('Vendor updated.', 'success')
    return redirect(url_for('masters.vendors'))


@masters_bp.route('/vendors/delete/<int:id>', methods=['POST'])
@login_required
def delete_vendor(id):
    v = Vendor.query.get_or_404(id)
    db.session.delete(v)
    db.session.commit()
    flash('Vendor deleted.', 'success')
    return redirect(url_for('masters.vendors'))


# ─── ITEMS ────────────────────────────────────────────────────────────────────

@masters_bp.route('/items')
@login_required
def items():
    q = request.args.get('q', '')
    query = Item.query
    if q:
        query = query.filter(Item.item_name.ilike(f'%{q}%'))
    items_list = query.order_by(Item.item_name).all()
    categories = Category.query.order_by(Category.category_name).all()
    subcategories = SubCategory.query.order_by(SubCategory.subcategory_name).all()
    brands = Brand.query.order_by(Brand.brand_name).all()
    return render_template('masters/items.html', items=items_list, categories=categories,
                           subcategories=subcategories, brands=brands, q=q, active_page='masters')


@masters_bp.route('/items/add', methods=['POST'])
@login_required
def add_item():
    serial = request.form.get('serial_no', '').strip()
    if serial and Item.query.filter_by(serial_no=serial).first():
        flash('Serial number already exists.', 'danger')
        return redirect(url_for('masters.items'))
    from datetime import date as d
    warranty_str = request.form.get('warranty_expiry_date', '')
    warranty = d.fromisoformat(warranty_str) if warranty_str else None
    min_stock = int(request.form.get('minimum_stock_level', 0) or 0)
    item = Item(
        item_name=request.form.get('item_name', '').strip(),
        category_id=int(request.form.get('category_id')),
        subcategory_id=request.form.get('subcategory_id') or None,
        brand_id=request.form.get('brand_id') or None,
        model_name=request.form.get('model_name', '').strip(),
        serial_no=serial or None,
        minimum_stock_level=min_stock,
        warranty_expiry_date=warranty,
    )
    db.session.add(item)
    db.session.commit()
    flash('Item added.', 'success')
    return redirect(url_for('masters.items'))


@masters_bp.route('/items/edit/<int:id>', methods=['POST'])
@login_required
def edit_item(id):
    item = Item.query.get_or_404(id)
    serial = request.form.get('serial_no', '').strip()
    existing = Item.query.filter_by(serial_no=serial).first()
    if serial and existing and existing.id != id:
        flash('Serial number already in use.', 'danger')
        return redirect(url_for('masters.items'))
    from datetime import date as d
    warranty_str = request.form.get('warranty_expiry_date', '')
    item.item_name = request.form.get('item_name', item.item_name).strip()
    item.category_id = int(request.form.get('category_id', item.category_id))
    item.subcategory_id = request.form.get('subcategory_id') or None
    item.brand_id = request.form.get('brand_id') or None
    item.model_name = request.form.get('model_name', item.model_name)
    item.serial_no = serial or None
    item.minimum_stock_level = int(request.form.get('minimum_stock_level', item.minimum_stock_level) or 0)
    item.warranty_expiry_date = d.fromisoformat(warranty_str) if warranty_str else None
    db.session.commit()
    flash('Item updated.', 'success')
    return redirect(url_for('masters.items'))


@masters_bp.route('/items/delete/<int:id>', methods=['POST'])
@login_required
def delete_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted.', 'success')
    return redirect(url_for('masters.items'))
