from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, Invoice, InvoiceLine, Contact, Product

invoicing_bp = Blueprint('invoicing', __name__)


def _next_inv_name(inv_type='out_invoice'):
    prefix = 'INV' if inv_type == 'out_invoice' else 'BILL'
    last = Invoice.query.filter_by(invoice_type=inv_type).order_by(Invoice.id.desc()).first()
    num = (last.id + 1) if last else 1
    return f'{prefix}/{num:05d}'


@invoicing_bp.route('/')
@login_required
def invoices():
    inv_type = request.args.get('type', 'out_invoice')
    state = request.args.get('state', '')
    query = Invoice.query.filter_by(invoice_type=inv_type)
    if state:
        query = query.filter_by(state=state)
    invoices = query.order_by(Invoice.created_at.desc()).all()
    return render_template('invoicing/invoices.html', invoices=invoices,
                           inv_type=inv_type, current_state=state)


@invoicing_bp.route('/new', methods=['GET', 'POST'])
@login_required
def invoice_new():
    inv_type = request.args.get('type', 'out_invoice')
    if request.method == 'POST':
        inv_type = request.form.get('invoice_type', 'out_invoice')
        invoice = Invoice(
            name=_next_inv_name(inv_type),
            partner_id=int(request.form['partner_id']),
            invoice_type=inv_type,
            notes=request.form.get('notes', ''),
        )
        db.session.add(invoice)
        db.session.flush()
        _save_lines(invoice, request.form)
        _recalc(invoice)
        db.session.commit()
        flash('Invoice created.', 'success')
        return redirect(url_for('invoicing.invoice_detail', id=invoice.id))
    partners = Contact.query.order_by(Contact.name).all()
    products = Product.query.filter_by(active=True).order_by(Product.name).all()
    return render_template('invoicing/invoice_form.html', invoice=None,
                           partners=partners, products=products, inv_type=inv_type)


@invoicing_bp.route('/<int:id>')
@login_required
def invoice_detail(id):
    invoice = db.get_or_404(Invoice, id)
    return render_template('invoicing/invoice_detail.html', invoice=invoice)


@invoicing_bp.route('/<int:id>/post', methods=['POST'])
@login_required
def invoice_post(id):
    invoice = db.get_or_404(Invoice, id)
    invoice.state = 'posted'
    db.session.commit()
    flash('Invoice posted.', 'success')
    return redirect(url_for('invoicing.invoice_detail', id=invoice.id))


@invoicing_bp.route('/<int:id>/pay', methods=['POST'])
@login_required
def invoice_pay(id):
    invoice = db.get_or_404(Invoice, id)
    amount = float(request.form.get('amount', 0))
    invoice.amount_paid += amount
    if invoice.amount_paid >= invoice.amount_total:
        invoice.state = 'paid'
    db.session.commit()
    flash('Payment registered.', 'success')
    return redirect(url_for('invoicing.invoice_detail', id=invoice.id))


@invoicing_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def invoice_delete(id):
    invoice = db.get_or_404(Invoice, id)
    db.session.delete(invoice)
    db.session.commit()
    flash('Invoice deleted.', 'success')
    return redirect(url_for('invoicing.invoices'))


def _save_lines(invoice, form):
    idx = 0
    while f'line_description_{idx}' in form:
        desc = form.get(f'line_description_{idx}', '')
        qty = float(form.get(f'line_qty_{idx}', 1))
        price = float(form.get(f'line_price_{idx}', 0))
        tax = float(form.get(f'line_tax_{idx}', 0))
        if desc:
            line = InvoiceLine(
                invoice_id=invoice.id,
                product_id=form.get(f'line_product_{idx}') or None,
                description=desc,
                quantity=qty,
                unit_price=price,
                tax_percent=tax,
                subtotal=qty * price,
            )
            db.session.add(line)
        idx += 1


def _recalc(invoice):
    db.session.flush()
    lines = InvoiceLine.query.filter_by(invoice_id=invoice.id).all()
    untaxed = sum(l.subtotal for l in lines)
    tax = sum(l.subtotal * l.tax_percent / 100 for l in lines)
    invoice.amount_untaxed = untaxed
    invoice.amount_tax = tax
    invoice.amount_total = untaxed + tax
