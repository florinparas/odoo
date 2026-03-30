from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, SaleOrder, SaleOrderLine, Contact, Product, User

sales_bp = Blueprint('sales', __name__)


def _next_so_name():
    last = SaleOrder.query.order_by(SaleOrder.id.desc()).first()
    num = (last.id + 1) if last else 1
    return f'S{num:05d}'


@sales_bp.route('/')
@login_required
def orders():
    state = request.args.get('state', '')
    query = SaleOrder.query
    if state:
        query = query.filter_by(state=state)
    orders = query.order_by(SaleOrder.created_at.desc()).all()
    return render_template('sales/orders.html', orders=orders, current_state=state)


@sales_bp.route('/new', methods=['GET', 'POST'])
@login_required
def order_new():
    if request.method == 'POST':
        order = SaleOrder(
            name=_next_so_name(),
            customer_id=int(request.form['customer_id']),
            salesperson_id=current_user.id,
            notes=request.form.get('notes', ''),
        )
        db.session.add(order)
        db.session.flush()
        _save_lines(order, request.form)
        _recalc_totals(order)
        db.session.commit()
        flash('Quotation created.', 'success')
        return redirect(url_for('sales.order_detail', id=order.id))
    customers = Contact.query.filter_by(is_customer=True).order_by(Contact.name).all()
    products = Product.query.filter_by(active=True).order_by(Product.name).all()
    return render_template('sales/order_form.html', order=None, customers=customers, products=products)


@sales_bp.route('/<int:id>')
@login_required
def order_detail(id):
    order = db.get_or_404(SaleOrder, id)
    return render_template('sales/order_detail.html', order=order)


@sales_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def order_edit(id):
    order = db.get_or_404(SaleOrder, id)
    if request.method == 'POST':
        order.customer_id = int(request.form['customer_id'])
        order.notes = request.form.get('notes', '')
        SaleOrderLine.query.filter_by(order_id=order.id).delete()
        _save_lines(order, request.form)
        _recalc_totals(order)
        db.session.commit()
        flash('Order updated.', 'success')
        return redirect(url_for('sales.order_detail', id=order.id))
    customers = Contact.query.filter_by(is_customer=True).order_by(Contact.name).all()
    products = Product.query.filter_by(active=True).order_by(Product.name).all()
    return render_template('sales/order_form.html', order=order, customers=customers, products=products)


@sales_bp.route('/<int:id>/confirm', methods=['POST'])
@login_required
def order_confirm(id):
    order = db.get_or_404(SaleOrder, id)
    order.state = 'sale'
    db.session.commit()
    flash('Order confirmed.', 'success')
    return redirect(url_for('sales.order_detail', id=order.id))


@sales_bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def order_cancel(id):
    order = db.get_or_404(SaleOrder, id)
    order.state = 'cancel'
    db.session.commit()
    flash('Order cancelled.', 'warning')
    return redirect(url_for('sales.order_detail', id=order.id))


@sales_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def order_delete(id):
    order = db.get_or_404(SaleOrder, id)
    db.session.delete(order)
    db.session.commit()
    flash('Order deleted.', 'success')
    return redirect(url_for('sales.orders'))


def _save_lines(order, form):
    idx = 0
    while f'line_product_{idx}' in form:
        product_id = form.get(f'line_product_{idx}')
        qty = float(form.get(f'line_qty_{idx}', 1))
        price = float(form.get(f'line_price_{idx}', 0))
        tax = float(form.get(f'line_tax_{idx}', 0))
        if product_id:
            line = SaleOrderLine(
                order_id=order.id,
                product_id=int(product_id),
                quantity=qty,
                unit_price=price,
                tax_percent=tax,
                subtotal=qty * price,
            )
            db.session.add(line)
        idx += 1


def _recalc_totals(order):
    db.session.flush()
    lines = SaleOrderLine.query.filter_by(order_id=order.id).all()
    untaxed = sum(l.subtotal for l in lines)
    tax = sum(l.subtotal * l.tax_percent / 100 for l in lines)
    order.amount_untaxed = untaxed
    order.amount_tax = tax
    order.amount_total = untaxed + tax
