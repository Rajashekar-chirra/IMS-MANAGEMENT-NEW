from flask import Blueprint, render_template, request
from flask_login import login_required
from app import db
from models import Item, Category, SubCategory

stocks_bp = Blueprint('stocks', __name__)


@stocks_bp.route('/')
@login_required
def index():
    cat_id = request.args.get('category_id', '')
    subcat_id = request.args.get('subcategory_id', '')
    stock_filter = request.args.get('stock_filter', 'all')
    q = request.args.get('q', '')

    query = Item.query
    if cat_id:
        query = query.filter(Item.category_id == int(cat_id))
    if subcat_id:
        query = query.filter(Item.subcategory_id == int(subcat_id))
    if q:
        query = query.filter(Item.item_name.ilike(f'%{q}%'))
    if stock_filter == 'low':
        query = query.filter(Item.current_stock <= Item.minimum_stock_level)
    elif stock_filter == 'out':
        query = query.filter(Item.current_stock == 0)

    items = query.order_by(Item.item_name).all()
    categories = Category.query.order_by(Category.category_name).all()
    subcategories = SubCategory.query.order_by(SubCategory.subcategory_name).all()

    return render_template('stocks/index.html', items=items, categories=categories,
                           subcategories=subcategories, cat_id=cat_id, subcat_id=subcat_id,
                           stock_filter=stock_filter, q=q, active_page='stocks')
