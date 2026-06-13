from flask import Blueprint, render_template, request
from flask_login import login_required
from datetime import date
from app import db
from models import DistributionMaster, DistributionItem, PurchaseMaster, PurchaseItem, Vendor, Item, Category

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/distributor-history')
@login_required
def distributor_history():
    q = request.args.get('q', '').strip()
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')

    query = DistributionMaster.query
    if q:
        query = query.filter(
            DistributionMaster.issued_to.ilike(f'%{q}%') |
            DistributionMaster.employee_id.ilike(f'%{q}%') |
            DistributionMaster.phone.ilike(f'%{q}%') |
            DistributionMaster.department.ilike(f'%{q}%')
        )
    if from_date:
        try:
            query = query.filter(DistributionMaster.voucher_date >= date.fromisoformat(from_date))
        except ValueError:
            pass
    if to_date:
        try:
            query = query.filter(DistributionMaster.voucher_date <= date.fromisoformat(to_date))
        except ValueError:
            pass

    all_masters = query.order_by(DistributionMaster.issued_to, DistributionMaster.created_at.desc()).all()

    distributors = {}
    for m in all_masters:
        key = m.issued_to.strip().lower()
        if key not in distributors:
            distributors[key] = {
                'name': m.issued_to,
                'employee_id': m.employee_id,
                'phone': m.phone,
                'department': m.department,
                'total_txns': 0,
                'total_qty': 0,
                'last_date': None
            }
        distributors[key]['total_txns'] += 1
        for di in m.dist_items:
            distributors[key]['total_qty'] += di.quantity_issued
        if m.voucher_date:
            if distributors[key]['last_date'] is None or m.voucher_date > distributors[key]['last_date']:
                distributors[key]['last_date'] = m.voucher_date

    return render_template('reports/distributor_history.html',
                           distributors=sorted(distributors.values(), key=lambda x: x['name']),
                           q=q, from_date=from_date, to_date=to_date,
                           active_page='reports')


@reports_bp.route('/distributor-history/detail')
@login_required
def distributor_detail():
    name = request.args.get('name', '').strip()
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    category_id = request.args.get('category_id', '')

    if not name:
        return __import__('flask').redirect(__import__('flask').url_for('reports.distributor_history'))

    query = DistributionMaster.query.filter(DistributionMaster.issued_to.ilike(name))
    if from_date:
        try:
            query = query.filter(DistributionMaster.voucher_date >= date.fromisoformat(from_date))
        except ValueError:
            pass
    if to_date:
        try:
            query = query.filter(DistributionMaster.voucher_date <= date.fromisoformat(to_date))
        except ValueError:
            pass

    masters = query.order_by(DistributionMaster.created_at.desc()).all()

    total_qty = sum(di.quantity_issued for m in masters for di in m.dist_items)
    total_txns = len(masters)
    last_date = max((m.voucher_date for m in masters if m.voucher_date), default=None)
    info = masters[0] if masters else None

    item_summary = {}
    for m in masters:
        for di in m.dist_items:
            if category_id and di.item and str(di.item.category_id) != str(category_id):
                continue
            k = di.item_id
            if k not in item_summary:
                item_summary[k] = {'item': di.item, 'total_qty': 0, 'txns': 0}
            item_summary[k]['total_qty'] += di.quantity_issued
            item_summary[k]['txns'] += 1

    categories = Category.query.order_by(Category.category_name).all()
    return render_template('reports/distributor_detail.html',
                           name=name, info=info, masters=masters,
                           total_qty=total_qty, total_txns=total_txns, last_date=last_date,
                           item_summary=sorted(item_summary.values(), key=lambda x: -x['total_qty']),
                           from_date=from_date, to_date=to_date,
                           category_id=category_id, categories=categories,
                           active_page='reports')


@reports_bp.route('/vendor-history')
@login_required
def vendor_history():
    q = request.args.get('q', '').strip()
    query = Vendor.query
    if q:
        query = query.filter(
            Vendor.vendor_name.ilike(f'%{q}%') |
            Vendor.mobile.ilike(f'%{q}%')
        )
    vendors = query.order_by(Vendor.vendor_name).all()

    vendor_data = []
    for v in vendors:
        # Query by per-item vendor (new style)
        pit_items = PurchaseItem.query.filter_by(vendor_id=v.id).all()
        total_qty = sum(pi.quantity for pi in pit_items)
        total_amount = sum(float(pi.total_amount or 0) for pi in pit_items)
        master_ids = set(pi.master_id for pi in pit_items)
        dates = [pi.master.purchase_date for pi in pit_items if pi.master and pi.master.purchase_date]
        last_date = max(dates) if dates else None
        vendor_data.append({
            'vendor': v,
            'total_txns': len(master_ids),
            'total_qty': total_qty,
            'total_amount': total_amount,
            'last_date': last_date
        })

    return render_template('reports/vendor_history.html',
                           vendor_data=vendor_data, q=q, active_page='reports')


@reports_bp.route('/vendor-history/<int:vendor_id>')
@login_required
def vendor_detail(vendor_id):
    vendor = Vendor.query.get_or_404(vendor_id)
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    category_id = request.args.get('category_id', '')

    # Get all purchase items belonging to this vendor (per-item vendor model)
    pit_query = PurchaseItem.query.filter_by(vendor_id=vendor_id)
    all_pit = pit_query.all()

    # Apply date filters via master
    filtered_pit = []
    for pi in all_pit:
        m = pi.master
        if not m:
            continue
        if from_date:
            try:
                if m.purchase_date and m.purchase_date < date.fromisoformat(from_date):
                    continue
            except ValueError:
                pass
        if to_date:
            try:
                if m.purchase_date and m.purchase_date > date.fromisoformat(to_date):
                    continue
            except ValueError:
                pass
        filtered_pit.append(pi)

    # Build master view grouped by master_id
    master_map = {}
    for pi in filtered_pit:
        mid = pi.master_id
        if mid not in master_map:
            master_map[mid] = {'master': pi.master, 'items': []}
        master_map[mid]['items'].append(pi)
    masters = sorted(master_map.values(), key=lambda x: x['master'].created_at, reverse=True)

    total_qty = sum(pi.quantity for pi in filtered_pit)
    total_amount = sum(float(pi.total_amount or 0) for pi in filtered_pit)
    dates = [pi.master.purchase_date for pi in filtered_pit if pi.master and pi.master.purchase_date]
    last_date = max(dates) if dates else None

    item_summary = {}
    for pi in filtered_pit:
        if category_id and pi.item and str(pi.item.category_id) != str(category_id):
            continue
        k = pi.item_id
        if k not in item_summary:
            item_summary[k] = {'item': pi.item, 'total_qty': 0, 'total_amount': 0}
        item_summary[k]['total_qty'] += pi.quantity
        item_summary[k]['total_amount'] += float(pi.total_amount or 0)

    categories = Category.query.order_by(Category.category_name).all()
    return render_template('reports/vendor_detail.html',
                           vendor=vendor, masters=masters,
                           total_qty=total_qty, total_amount=total_amount, last_date=last_date,
                           item_summary=sorted(item_summary.values(), key=lambda x: -x['total_qty']),
                           from_date=from_date, to_date=to_date,
                           category_id=category_id, categories=categories,
                           active_page='reports')
