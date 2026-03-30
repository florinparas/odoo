from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, Product, StockMove

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/')
@login_required
def products():
    q = request.args.get('q', '')
    query = Product.query.filter_by(active=True)
    if q:
        query = query.filter(Product.name.ilike(f'%{q}%'))
    products = query.order_by(Product.name).all()
    return render_template('inventory/products.html', products=products, q=q)


@inventory_bp.route('/new', methods=['GET', 'POST'])
@login_required
def product_new():
    if request.method == 'POST':
        product = Product(
            name=request.form['name'],
            internal_ref=request.form.get('internal_ref', ''),
            description=request.form.get('description', ''),
            sale_price=float(request.form.get('sale_price') or 0),
            cost_price=float(request.form.get('cost_price') or 0),
            category=request.form.get('category', ''),
            product_type=request.form.get('product_type', 'storable'),
            barcode=request.form.get('barcode', ''),
            qty_on_hand=float(request.form.get('qty_on_hand') or 0),
        )
        db.session.add(product)
        db.session.commit()
        flash('Product created.', 'success')
        return redirect(url_for('inventory.product_detail', id=product.id))
    return render_template('inventory/product_form.html', product=None)


@inventory_bp.route('/<int:id>')
@login_required
def product_detail(id):
    product = db.get_or_404(Product, id)
    moves = StockMove.query.filter_by(product_id=id).order_by(StockMove.date.desc()).all()
    return render_template('inventory/product_detail.html', product=product, moves=moves)


@inventory_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def product_edit(id):
    product = db.get_or_404(Product, id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.internal_ref = request.form.get('internal_ref', '')
        product.description = request.form.get('description', '')
        product.sale_price = float(request.form.get('sale_price') or 0)
        product.cost_price = float(request.form.get('cost_price') or 0)
        product.category = request.form.get('category', '')
        product.product_type = request.form.get('product_type', 'storable')
        product.barcode = request.form.get('barcode', '')
        db.session.commit()
        flash('Product updated.', 'success')
        return redirect(url_for('inventory.product_detail', id=product.id))
    return render_template('inventory/product_form.html', product=product)


@inventory_bp.route('/<int:id>/adjust', methods=['POST'])
@login_required
def stock_adjust(id):
    product = db.get_or_404(Product, id)
    qty = float(request.form.get('quantity', 0))
    move_type = request.form.get('move_type', 'adjustment')
    if qty != 0:
        move = StockMove(
            product_id=product.id,
            quantity=abs(qty),
            move_type=move_type,
            reference=request.form.get('reference', ''),
            notes=request.form.get('notes', ''),
        )
        db.session.add(move)
        if move_type == 'in':
            product.qty_on_hand += abs(qty)
        elif move_type == 'out':
            product.qty_on_hand -= abs(qty)
        else:
            product.qty_on_hand = qty
        db.session.commit()
        flash('Stock updated.', 'success')
    return redirect(url_for('inventory.product_detail', id=product.id))


@inventory_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def product_delete(id):
    product = db.get_or_404(Product, id)
    product.active = False
    db.session.commit()
    flash('Product archived.', 'success')
    return redirect(url_for('inventory.products'))
