from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/')
@login_required
def index():
    return render_template('settings/index.html')


@settings_bp.route('/users')
@login_required
def users():
    all_users = User.query.order_by(User.full_name).all()
    return render_template('settings/users.html', users=all_users)


@settings_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
def user_new():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('settings.users'))
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            full_name=request.form['full_name'],
            role=request.form.get('role', 'user'),
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('User created.', 'success')
        return redirect(url_for('settings.users'))
    return render_template('settings/user_form.html', user=None)


@settings_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(id):
    user = db.get_or_404(User, id)
    if current_user.role != 'admin' and current_user.id != user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('settings.users'))
    if request.method == 'POST':
        user.full_name = request.form['full_name']
        user.email = request.form['email']
        if current_user.role == 'admin':
            user.role = request.form.get('role', user.role)
        if request.form.get('password'):
            user.set_password(request.form['password'])
        db.session.commit()
        flash('User updated.', 'success')
        return redirect(url_for('settings.users'))
    return render_template('settings/user_form.html', user=user)


@settings_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form['full_name']
        current_user.email = request.form['email']
        if request.form.get('password'):
            current_user.set_password(request.form['password'])
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('settings.profile'))
    return render_template('settings/profile.html')
