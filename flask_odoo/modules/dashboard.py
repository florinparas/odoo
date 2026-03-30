from flask import Blueprint, render_template
from flask_login import login_required
from models import db, Contact, Lead, SaleOrder, Invoice, Project, Task, Employee, Product

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    stats = {
        'contacts': Contact.query.count(),
        'leads': Lead.query.filter(Lead.stage.notin_(['won', 'lost'])).count(),
        'orders': SaleOrder.query.filter_by(state='sale').count(),
        'revenue': db.session.query(db.func.coalesce(db.func.sum(SaleOrder.amount_total), 0)).filter_by(state='sale').scalar(),
        'invoices_open': Invoice.query.filter_by(state='posted').count(),
        'invoices_amount': db.session.query(db.func.coalesce(db.func.sum(Invoice.amount_total - Invoice.amount_paid), 0)).filter_by(state='posted').scalar(),
        'products': Product.query.count(),
        'projects': Project.query.filter_by(status='active').count(),
        'tasks_todo': Task.query.filter(Task.stage.in_(['todo', 'in_progress'])).count(),
        'employees': Employee.query.filter_by(status='active').count(),
    }
    recent_leads = Lead.query.order_by(Lead.created_at.desc()).limit(5).all()
    recent_orders = SaleOrder.query.order_by(SaleOrder.created_at.desc()).limit(5).all()
    return render_template('dashboard/index.html', stats=stats,
                           recent_leads=recent_leads, recent_orders=recent_orders)
