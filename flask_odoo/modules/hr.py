from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, Employee, Department, User

hr_bp = Blueprint('hr', __name__)


# ─── Departments ──────────────────────────────────────────────────────

@hr_bp.route('/departments')
@login_required
def departments():
    depts = Department.query.order_by(Department.name).all()
    return render_template('hr/departments.html', departments=depts)


@hr_bp.route('/departments/new', methods=['GET', 'POST'])
@login_required
def department_new():
    if request.method == 'POST':
        dept = Department(
            name=request.form['name'],
            manager_id=request.form.get('manager_id') or None,
            color=request.form.get('color', '#714B67'),
        )
        db.session.add(dept)
        db.session.commit()
        flash('Department created.', 'success')
        return redirect(url_for('hr.departments'))
    users = User.query.order_by(User.full_name).all()
    return render_template('hr/department_form.html', department=None, users=users)


@hr_bp.route('/departments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def department_edit(id):
    dept = db.get_or_404(Department, id)
    if request.method == 'POST':
        dept.name = request.form['name']
        dept.manager_id = request.form.get('manager_id') or None
        dept.color = request.form.get('color', '#714B67')
        db.session.commit()
        flash('Department updated.', 'success')
        return redirect(url_for('hr.departments'))
    users = User.query.order_by(User.full_name).all()
    return render_template('hr/department_form.html', department=dept, users=users)


# ─── Employees ────────────────────────────────────────────────────────

@hr_bp.route('/')
@login_required
def employees():
    q = request.args.get('q', '')
    query = Employee.query.filter_by(status='active')
    if q:
        query = query.filter(Employee.name.ilike(f'%{q}%'))
    emps = query.order_by(Employee.name).all()
    return render_template('hr/employees.html', employees=emps, q=q)


@hr_bp.route('/new', methods=['GET', 'POST'])
@login_required
def employee_new():
    if request.method == 'POST':
        emp = Employee(
            name=request.form['name'],
            email=request.form.get('email', ''),
            phone=request.form.get('phone', ''),
            job_title=request.form.get('job_title', ''),
            department_id=request.form.get('department_id') or None,
        )
        db.session.add(emp)
        db.session.commit()
        flash('Employee created.', 'success')
        return redirect(url_for('hr.employee_detail', id=emp.id))
    departments = Department.query.order_by(Department.name).all()
    return render_template('hr/employee_form.html', employee=None, departments=departments)


@hr_bp.route('/<int:id>')
@login_required
def employee_detail(id):
    emp = db.get_or_404(Employee, id)
    return render_template('hr/employee_detail.html', employee=emp)


@hr_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def employee_edit(id):
    emp = db.get_or_404(Employee, id)
    if request.method == 'POST':
        emp.name = request.form['name']
        emp.email = request.form.get('email', '')
        emp.phone = request.form.get('phone', '')
        emp.job_title = request.form.get('job_title', '')
        emp.department_id = request.form.get('department_id') or None
        db.session.commit()
        flash('Employee updated.', 'success')
        return redirect(url_for('hr.employee_detail', id=emp.id))
    departments = Department.query.order_by(Department.name).all()
    return render_template('hr/employee_form.html', employee=emp, departments=departments)


@hr_bp.route('/<int:id>/archive', methods=['POST'])
@login_required
def employee_archive(id):
    emp = db.get_or_404(Employee, id)
    emp.status = 'archived'
    db.session.commit()
    flash('Employee archived.', 'success')
    return redirect(url_for('hr.employees'))
