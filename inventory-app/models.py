from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subcategories = db.relationship('SubCategory', backref='category', lazy=True, cascade='all, delete-orphan')
    items = db.relationship('Item', backref='category', lazy=True)


class SubCategory(db.Model):
    __tablename__ = 'subcategories'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    subcategory_name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('Item', backref='subcategory', lazy=True)


class Brand(db.Model):
    __tablename__ = 'brands'
    id = db.Column(db.Integer, primary_key=True)
    brand_name = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('Item', backref='brand', lazy=True)


class Vendor(db.Model):
    __tablename__ = 'vendors'
    id = db.Column(db.Integer, primary_key=True)
    vendor_name = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    purchase_masters = db.relationship('PurchaseMaster', backref='vendor', lazy=True)


class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(150), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategories.id'))
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'))
    model_name = db.Column(db.String(120))
    serial_no = db.Column(db.String(120))
    minimum_stock_level = db.Column(db.Integer, default=0)
    current_stock = db.Column(db.Integer, default=0)
    warranty_expiry_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_warranty_expired(self):
        if self.warranty_expiry_date:
            return self.warranty_expiry_date < date.today()
        return False

    @property
    def is_low_stock(self):
        return self.current_stock <= self.minimum_stock_level and self.minimum_stock_level > 0


# ─── NEW ERP-STYLE PURCHASE TABLES ───────────────────────────────────────────

class PurchaseMaster(db.Model):
    __tablename__ = 'purchase_master'
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(20), unique=True, nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=True)
    purchase_date = db.Column(db.Date, default=date.today)
    rv_no = db.Column(db.String(80))
    rv_date = db.Column(db.Date)
    grand_total = db.Column(db.Numeric(14, 2), default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    purchase_items = db.relationship('PurchaseItem', backref='master', cascade='all, delete-orphan', lazy=True)

    @property
    def total_quantity(self):
        return sum(pi.quantity for pi in self.purchase_items)


class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'
    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.Integer, db.ForeignKey('purchase_master.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    unit_price = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(14, 2), default=0)
    item = db.relationship('Item', backref='purchase_items', lazy=True)
    vendor = db.relationship('Vendor', backref='purchase_items', lazy=True)


# ─── NEW ERP-STYLE DISTRIBUTION TABLES ───────────────────────────────────────

class DistributionMaster(db.Model):
    __tablename__ = 'distribution_master'
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(20), unique=True, nullable=False)
    issued_to = db.Column(db.String(200), nullable=False)
    employee_id = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    voucher_no = db.Column(db.String(80))
    voucher_date = db.Column(db.Date, default=date.today)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    dist_items = db.relationship('DistributionItem', backref='master', cascade='all, delete-orphan', lazy=True)

    @property
    def total_quantity(self):
        return sum(di.quantity_issued for di in self.dist_items)


class DistributionItem(db.Model):
    __tablename__ = 'distribution_items'
    id = db.Column(db.Integer, primary_key=True)
    master_id = db.Column(db.Integer, db.ForeignKey('distribution_master.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity_issued = db.Column(db.Integer, nullable=False, default=0)
    item = db.relationship('Item', backref='distribution_items', lazy=True)
