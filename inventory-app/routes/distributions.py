from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from datetime import date
from app import db
from models import DistributionMaster, DistributionItem, Item, Category

distributions_bp = Blueprint('distributions', __name__)


def _gen_transaction_id():
    last = DistributionMaster.query.order_by(DistributionMaster.id.desc()).first()
    num = (last.id if last else 0) + 1
    return f'DIST-{1000 + num}'


def _gen_voucher():
    last = DistributionMaster.query.order_by(DistributionMaster.id.desc()).first()
    num = (last.id if last else 0) + 1
    return f'VCH-{date.today().year}-{num:04d}'


@distributions_bp.route('/')
@login_required
def index():
    q = request.args.get('q', '')
    query = DistributionMaster.query
    if q:
        query = query.filter(
            DistributionMaster.issued_to.ilike(f'%{q}%') |
            DistributionMaster.transaction_id.ilike(f'%{q}%') |
            DistributionMaster.employee_id.ilike(f'%{q}%') |
            DistributionMaster.voucher_no.ilike(f'%{q}%')
        )
    distributions = query.order_by(DistributionMaster.created_at.desc()).all()
    items_raw = Item.query.order_by(Item.item_name).all()
    categories = Category.query.order_by(Category.category_name).all()
    next_txn = _gen_transaction_id()
    next_voucher = _gen_voucher()
    items_json = [
        {
            'id': it.id,
            'item_name': it.item_name,
            'current_stock': it.current_stock,
            'category_name': it.category.category_name if it.category else ''
        }
        for it in items_raw
    ]
    return render_template('distributions/index.html',
                           distributions=distributions, items=items_raw,
                           items_json=items_json,
                           categories=categories, q=q,
                           next_txn=next_txn, next_voucher=next_voucher,
                           today=date.today(), active_page='distributions')


@distributions_bp.route('/add', methods=['POST'])
@login_required
def add():
    item_ids = request.form.getlist('item_id[]')
    quantities = request.form.getlist('quantity_issued[]')

    if not item_ids or not any(item_ids):
        flash('Please add at least one item.', 'danger')
        return redirect(url_for('distributions.index'))

    issued_to = request.form.get('issued_to', '').strip()
    employee_id = request.form.get('employee_id', '').strip()
    phone = request.form.get('phone', '').strip()
    department = request.form.get('department', '').strip()
    voucher_no = request.form.get('voucher_no', '').strip() or _gen_voucher()
    voucher_date_str = request.form.get('voucher_date', '')
    notes = request.form.get('notes', '').strip()
    voucher_date = date.fromisoformat(voucher_date_str) if voucher_date_str else date.today()

    if not issued_to:
        flash('Issued To is required.', 'danger')
        return redirect(url_for('distributions.index'))

    rows = []
    for i, item_id in enumerate(item_ids):
        if not item_id:
            continue
        try:
            qty = int(quantities[i]) if i < len(quantities) and quantities[i] else 0
        except ValueError:
            flash(f'Row {i+1}: Invalid quantity.', 'danger')
            return redirect(url_for('distributions.index'))
        if qty <= 0:
            flash(f'Row {i+1}: Quantity must be greater than zero.', 'danger')
            return redirect(url_for('distributions.index'))
        item = Item.query.get(int(item_id))
        if not item:
            flash(f'Row {i+1}: Item not found.', 'danger')
            return redirect(url_for('distributions.index'))
        if item.current_stock < qty:
            flash(f'Insufficient stock for <strong>{item.item_name}</strong>. '
                  f'Available: {item.current_stock}, Requested: {qty}.', 'danger')
            return redirect(url_for('distributions.index'))
        rows.append({'item_id': int(item_id), 'qty': qty, 'item': item})

    if not rows:
        flash('Please add at least one item.', 'danger')
        return redirect(url_for('distributions.index'))

    txn_id = _gen_transaction_id()
    master = DistributionMaster(
        transaction_id=txn_id,
        issued_to=issued_to,
        employee_id=employee_id or None,
        phone=phone or None,
        department=department or None,
        voucher_no=voucher_no,
        voucher_date=voucher_date,
        notes=notes or None
    )
    db.session.add(master)
    db.session.flush()

    for row in rows:
        di = DistributionItem(
            master_id=master.id,
            item_id=row['item_id'],
            quantity_issued=row['qty']
        )
        db.session.add(di)
        row['item'].current_stock -= row['qty']

    db.session.commit()
    flash(f'Distribution <strong>{txn_id}</strong> recorded — {len(rows)} item(s) issued to <strong>{issued_to}</strong>.', 'success')
    return redirect(url_for('distributions.index'))


@distributions_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    master = DistributionMaster.query.get_or_404(id)
    for di in master.dist_items:
        item = Item.query.get(di.item_id)
        if item:
            item.current_stock += di.quantity_issued
    txn_id = master.transaction_id
    db.session.delete(master)
    db.session.commit()
    flash(f'Distribution <strong>{txn_id}</strong> deleted. Stock restored.', 'success')
    return redirect(url_for('distributions.index'))
