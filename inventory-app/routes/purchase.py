from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from datetime import date
from decimal import Decimal, InvalidOperation
from app import db
from models import PurchaseMaster, PurchaseItem, Item, Vendor, Category

purchase_bp = Blueprint('purchase', __name__)


def _gen_transaction_id():
    last = PurchaseMaster.query.order_by(PurchaseMaster.id.desc()).first()
    num = (last.id if last else 0) + 1
    return f'PUR-{1000 + num}'


@purchase_bp.route('/')
@login_required
def index():
    q = request.args.get('q', '')
    query = PurchaseMaster.query
    if q:
        query = query.filter(
            PurchaseMaster.transaction_id.ilike(f'%{q}%') |
            PurchaseMaster.rv_no.ilike(f'%{q}%')
        )
    purchases = query.order_by(PurchaseMaster.created_at.desc()).all()
    items_raw = Item.query.order_by(Item.item_name).all()
    vendors = Vendor.query.order_by(Vendor.vendor_name).all()
    categories = Category.query.order_by(Category.category_name).all()
    next_txn = _gen_transaction_id()
    items_json = [
        {
            'id': it.id,
            'item_name': it.item_name,
            'current_stock': it.current_stock,
            'category_name': it.category.category_name if it.category else ''
        }
        for it in items_raw
    ]
    vendors_json = [
        {'id': v.id, 'vendor_name': v.vendor_name}
        for v in vendors
    ]
    return render_template('purchase/index.html',
                           purchases=purchases, items=items_raw,
                           items_json=items_json, vendors_json=vendors_json,
                           vendors=vendors, categories=categories,
                           q=q, next_txn=next_txn,
                           today=date.today(), active_page='purchase')


@purchase_bp.route('/add', methods=['POST'])
@login_required
def add():
    item_ids = request.form.getlist('item_id[]')
    quantities = request.form.getlist('quantity[]')
    unit_prices = request.form.getlist('unit_price[]')
    vendor_ids = request.form.getlist('vendor_id[]')

    if not item_ids or not any(item_ids):
        flash('Please add at least one item.', 'danger')
        return redirect(url_for('purchase.index'))

    rv_no = request.form.get('rv_no', '').strip()
    purchase_date_str = request.form.get('purchase_date', '')
    rv_date_str = request.form.get('rv_date', '')
    notes = request.form.get('notes', '').strip()
    purchase_date = date.fromisoformat(purchase_date_str) if purchase_date_str else date.today()
    rv_date = date.fromisoformat(rv_date_str) if rv_date_str else None

    grand_total = Decimal('0')
    rows = []
    for i, item_id in enumerate(item_ids):
        if not item_id:
            continue
        try:
            qty = int(quantities[i]) if i < len(quantities) and quantities[i] else 0
            price = Decimal(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else Decimal('0')
        except (ValueError, InvalidOperation):
            flash(f'Row {i+1}: Invalid quantity or price.', 'danger')
            return redirect(url_for('purchase.index'))
        if qty <= 0:
            flash(f'Row {i+1}: Quantity must be greater than zero.', 'danger')
            return redirect(url_for('purchase.index'))
        total = qty * price
        grand_total += total
        vid = vendor_ids[i] if i < len(vendor_ids) and vendor_ids[i] else None
        rows.append({
            'item_id': int(item_id),
            'vendor_id': int(vid) if vid else None,
            'qty': qty,
            'price': price,
            'total': total
        })

    if not rows:
        flash('Please add at least one item.', 'danger')
        return redirect(url_for('purchase.index'))

    # Pre-load all item objects BEFORE touching the session to avoid autoflush FK errors
    item_objects = {}
    for row in rows:
        iid = row['item_id']
        if iid not in item_objects:
            obj = db.session.get(Item, iid)
            if not obj:
                flash(f'Item not found (ID {iid}). Please try again.', 'danger')
                return redirect(url_for('purchase.index'))
            item_objects[iid] = obj

    txn_id = _gen_transaction_id()
    master = PurchaseMaster(
        transaction_id=txn_id,
        vendor_id=None,
        purchase_date=purchase_date,
        rv_no=rv_no or None,
        rv_date=rv_date,
        grand_total=grand_total,
        notes=notes or None
    )
    db.session.add(master)
    db.session.flush()

    for row in rows:
        pi = PurchaseItem(
            master_id=master.id,
            item_id=row['item_id'],
            vendor_id=row['vendor_id'],
            quantity=row['qty'],
            unit_price=row['price'],
            total_amount=row['total']
        )
        db.session.add(pi)
        item_objects[row['item_id']].current_stock += row['qty']

    db.session.commit()
    flash(f'Purchase <strong>{txn_id}</strong> recorded — {len(rows)} item(s) added to stock.', 'success')
    return redirect(url_for('purchase.index'))


@purchase_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    master = PurchaseMaster.query.get_or_404(id)
    for pi in master.purchase_items:
        item = Item.query.get(pi.item_id)
        if item and item.current_stock < pi.quantity:
            flash(f'Cannot delete: "{item.item_name}" would go to negative stock.', 'danger')
            return redirect(url_for('purchase.index'))
    for pi in master.purchase_items:
        item = Item.query.get(pi.item_id)
        if item:
            item.current_stock -= pi.quantity
    txn_id = master.transaction_id
    db.session.delete(master)
    db.session.commit()
    flash(f'Purchase <strong>{txn_id}</strong> deleted. Stock restored.', 'success')
    return redirect(url_for('purchase.index'))
