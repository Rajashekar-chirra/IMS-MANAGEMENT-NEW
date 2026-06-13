from flask import Blueprint, render_template, request
from flask_login import login_required
from datetime import date
from app import db
from models import Item, Category, SubCategory

warranty_bp = Blueprint('warranty', __name__)


@warranty_bp.route('/')
@login_required
def index():
    cat_id = request.args.get('category_id', '')
    subcat_id = request.args.get('subcategory_id', '')
    expiry_filter = request.args.get('expiry_filter', 'all')
    q = request.args.get('q', '')

    query = Item.query.filter(Item.warranty_expiry_date != None)

    if cat_id:
        query = query.filter(Item.category_id == int(cat_id))
    if subcat_id:
        query = query.filter(Item.subcategory_id == int(subcat_id))
    if q:
        query = query.filter(Item.item_name.ilike(f'%{q}%'))
    if expiry_filter == 'expired':
        query = query.filter(Item.warranty_expiry_date < date.today())
    elif expiry_filter == 'active':
        query = query.filter(Item.warranty_expiry_date >= date.today())

    items = query.order_by(Item.warranty_expiry_date).all()
    categories = Category.query.order_by(Category.category_name).all()
    subcategories = SubCategory.query.order_by(SubCategory.subcategory_name).all()

    return render_template('warranty/index.html', items=items, categories=categories,
                           subcategories=subcategories, cat_id=cat_id, subcat_id=subcat_id,
                           expiry_filter=expiry_filter, q=q, today=date.today(),
                           active_page='warranty')
