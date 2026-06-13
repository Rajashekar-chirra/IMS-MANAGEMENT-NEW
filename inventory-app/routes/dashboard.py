from flask import Blueprint, render_template
from flask_login import login_required
from datetime import date
from app import db
from models import Item, PurchaseMaster, PurchaseItem, DistributionMaster, DistributionItem, Vendor, Category

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    total_items = Item.query.count()
    total_vendors = Vendor.query.count()
    total_categories = Category.query.count()

    available_stock = db.session.query(
        db.func.coalesce(db.func.sum(Item.current_stock), 0)
    ).scalar()

    total_purchase_txns = PurchaseMaster.query.count()
    total_dist_txns = DistributionMaster.query.count()

    total_received = db.session.query(
        db.func.coalesce(db.func.sum(PurchaseItem.quantity), 0)
    ).scalar()

    total_distributed = db.session.query(
        db.func.coalesce(db.func.sum(DistributionItem.quantity_issued), 0)
    ).scalar()

    low_stock_items = Item.query.filter(
        Item.current_stock <= Item.minimum_stock_level,
        Item.minimum_stock_level > 0
    ).all()
    out_of_stock = sum(1 for it in low_stock_items if it.current_stock == 0)
    low_stock_count = len(low_stock_items)

    warranty_expired = Item.query.filter(
        Item.warranty_expiry_date.isnot(None),
        Item.warranty_expiry_date < date.today()
    ).count()
    under_warranty = Item.query.filter(
        Item.warranty_expiry_date.isnot(None),
        Item.warranty_expiry_date >= date.today()
    ).count()

    total_distributors = db.session.query(
        db.func.count(db.func.distinct(DistributionMaster.issued_to))
    ).scalar()

    recent_purchases = PurchaseMaster.query.order_by(PurchaseMaster.created_at.desc()).limit(5).all()
    recent_distributions = DistributionMaster.query.order_by(DistributionMaster.created_at.desc()).limit(5).all()

    return render_template('dashboard/index.html',
                           total_items=total_items,
                           total_vendors=total_vendors,
                           total_categories=total_categories,
                           available_stock=available_stock,
                           total_purchase_txns=total_purchase_txns,
                           total_dist_txns=total_dist_txns,
                           total_received=total_received,
                           total_distributed=total_distributed,
                           low_stock_count=low_stock_count,
                           low_stock_items=low_stock_items[:5],
                           out_of_stock=out_of_stock,
                           warranty_expired=warranty_expired,
                           under_warranty=under_warranty,
                           total_distributors=total_distributors,
                           recent_purchases=recent_purchases,
                           recent_distributions=recent_distributions,
                           active_page='dashboard')
