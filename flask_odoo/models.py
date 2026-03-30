from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ─── Authentication & Users ───────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, manager, user
    avatar_color = db.Column(db.String(7), default='#714B67')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def initials(self):
        parts = self.full_name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return self.full_name[:2].upper()


# ─── CRM ──────────────────────────────────────────────────────────────

class Contact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    company = db.Column(db.String(150))
    job_title = db.Column(db.String(100))
    address = db.Column(db.Text)
    city = db.Column(db.String(80))
    country = db.Column(db.String(80))
    notes = db.Column(db.Text)
    contact_type = db.Column(db.String(20), default='company')  # company, individual
    is_customer = db.Column(db.Boolean, default=False)
    is_vendor = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    leads = db.relationship('Lead', backref='contact', lazy=True)
    sale_orders = db.relationship('SaleOrder', backref='customer', lazy=True)
    invoices = db.relationship('Invoice', backref='partner', lazy=True)


class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    expected_revenue = db.Column(db.Float, default=0)
    probability = db.Column(db.Integer, default=10)
    stage = db.Column(db.String(30), default='new')  # new, qualified, proposition, won, lost
    priority = db.Column(db.Integer, default=0)  # 0=normal, 1=high, 2=very high
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    description = db.Column(db.Text)
    source = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    date_deadline = db.Column(db.Date)

    assignee = db.relationship('User', backref='leads')


# ─── Sales ────────────────────────────────────────────────────────────

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    internal_ref = db.Column(db.String(50))
    description = db.Column(db.Text)
    sale_price = db.Column(db.Float, default=0)
    cost_price = db.Column(db.Float, default=0)
    category = db.Column(db.String(100))
    product_type = db.Column(db.String(20), default='storable')  # storable, consumable, service
    barcode = db.Column(db.String(50))
    qty_on_hand = db.Column(db.Float, default=0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SaleOrder(db.Model):
    __tablename__ = 'sale_orders'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
    date_order = db.Column(db.Date, default=date.today)
    date_due = db.Column(db.Date)
    state = db.Column(db.String(20), default='draft')  # draft, sent, sale, done, cancel
    amount_untaxed = db.Column(db.Float, default=0)
    amount_tax = db.Column(db.Float, default=0)
    amount_total = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    salesperson_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lines = db.relationship('SaleOrderLine', backref='order', lazy=True, cascade='all, delete-orphan')
    salesperson = db.relationship('User', backref='sale_orders')


class SaleOrderLine(db.Model):
    __tablename__ = 'sale_order_lines'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('sale_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    description = db.Column(db.String(300))
    quantity = db.Column(db.Float, default=1)
    unit_price = db.Column(db.Float, default=0)
    tax_percent = db.Column(db.Float, default=0)
    subtotal = db.Column(db.Float, default=0)

    product = db.relationship('Product')


# ─── Invoicing ────────────────────────────────────────────────────────

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    partner_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
    invoice_type = db.Column(db.String(20), default='out_invoice')  # out_invoice, in_invoice, out_refund, in_refund
    date_invoice = db.Column(db.Date, default=date.today)
    date_due = db.Column(db.Date)
    state = db.Column(db.String(20), default='draft')  # draft, posted, paid, cancelled
    amount_untaxed = db.Column(db.Float, default=0)
    amount_tax = db.Column(db.Float, default=0)
    amount_total = db.Column(db.Float, default=0)
    amount_paid = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lines = db.relationship('InvoiceLine', backref='invoice', lazy=True, cascade='all, delete-orphan')


class InvoiceLine(db.Model):
    __tablename__ = 'invoice_lines'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    description = db.Column(db.String(300), nullable=False)
    quantity = db.Column(db.Float, default=1)
    unit_price = db.Column(db.Float, default=0)
    tax_percent = db.Column(db.Float, default=0)
    subtotal = db.Column(db.Float, default=0)

    product = db.relationship('Product')


# ─── Inventory ────────────────────────────────────────────────────────

class StockMove(db.Model):
    __tablename__ = 'stock_moves'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    move_type = db.Column(db.String(20), nullable=False)  # in, out, adjustment
    reference = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    product = db.relationship('Product', backref='stock_moves')


# ─── Projects ─────────────────────────────────────────────────────────

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='active')  # active, on_hold, done
    color = db.Column(db.String(7), default='#714B67')
    date_start = db.Column(db.Date, default=date.today)
    date_end = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')
    manager = db.relationship('User', backref='managed_projects')


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    description = db.Column(db.Text)
    stage = db.Column(db.String(30), default='todo')  # todo, in_progress, review, done
    priority = db.Column(db.Integer, default=0)
    date_deadline = db.Column(db.Date)
    hours_planned = db.Column(db.Float, default=0)
    hours_spent = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assignee = db.relationship('User', backref='tasks')


# ─── HR ───────────────────────────────────────────────────────────────

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    color = db.Column(db.String(7), default='#714B67')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    manager = db.relationship('User', backref='managed_departments')
    employees = db.relationship('Employee', backref='department', lazy=True)


class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    job_title = db.Column(db.String(100))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    hire_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(20), default='active')  # active, archived
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='employee_profile')
