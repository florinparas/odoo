from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Project, Task, User

projects_bp = Blueprint('projects', __name__)

TASK_STAGES = [
    ('todo', 'To Do'),
    ('in_progress', 'In Progress'),
    ('review', 'Review'),
    ('done', 'Done'),
]


@projects_bp.route('/')
@login_required
def project_list():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('projects/project_list.html', projects=projects)


@projects_bp.route('/new', methods=['GET', 'POST'])
@login_required
def project_new():
    if request.method == 'POST':
        project = Project(
            name=request.form['name'],
            description=request.form.get('description', ''),
            manager_id=request.form.get('manager_id') or current_user.id,
            color=request.form.get('color', '#714B67'),
        )
        db.session.add(project)
        db.session.commit()
        flash('Project created.', 'success')
        return redirect(url_for('projects.project_board', id=project.id))
    users = User.query.order_by(User.full_name).all()
    return render_template('projects/project_form.html', project=None, users=users)


@projects_bp.route('/<int:id>')
@login_required
def project_board(id):
    project = db.get_or_404(Project, id)
    tasks_by_stage = {}
    for code, label in TASK_STAGES:
        tasks_by_stage[code] = {
            'label': label,
            'tasks': Task.query.filter_by(project_id=id, stage=code).order_by(Task.priority.desc()).all()
        }
    return render_template('projects/project_board.html', project=project,
                           tasks_by_stage=tasks_by_stage, stages=TASK_STAGES)


@projects_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def project_edit(id):
    project = db.get_or_404(Project, id)
    if request.method == 'POST':
        project.name = request.form['name']
        project.description = request.form.get('description', '')
        project.manager_id = request.form.get('manager_id') or current_user.id
        project.status = request.form.get('status', 'active')
        project.color = request.form.get('color', '#714B67')
        db.session.commit()
        flash('Project updated.', 'success')
        return redirect(url_for('projects.project_board', id=project.id))
    users = User.query.order_by(User.full_name).all()
    return render_template('projects/project_form.html', project=project, users=users)


@projects_bp.route('/<int:pid>/tasks/new', methods=['GET', 'POST'])
@login_required
def task_new(pid):
    project = db.get_or_404(Project, pid)
    if request.method == 'POST':
        task = Task(
            name=request.form['name'],
            project_id=pid,
            assigned_to=request.form.get('assigned_to') or None,
            description=request.form.get('description', ''),
            stage=request.form.get('stage', 'todo'),
            priority=int(request.form.get('priority') or 0),
            hours_planned=float(request.form.get('hours_planned') or 0),
        )
        db.session.add(task)
        db.session.commit()
        flash('Task created.', 'success')
        return redirect(url_for('projects.project_board', id=pid))
    users = User.query.order_by(User.full_name).all()
    return render_template('projects/task_form.html', project=project, task=None,
                           users=users, stages=TASK_STAGES)


@projects_bp.route('/<int:pid>/tasks/<int:tid>/edit', methods=['GET', 'POST'])
@login_required
def task_edit(pid, tid):
    task = db.get_or_404(Task, tid)
    project = db.get_or_404(Project, pid)
    if request.method == 'POST':
        task.name = request.form['name']
        task.assigned_to = request.form.get('assigned_to') or None
        task.description = request.form.get('description', '')
        task.stage = request.form.get('stage', 'todo')
        task.priority = int(request.form.get('priority') or 0)
        task.hours_planned = float(request.form.get('hours_planned') or 0)
        task.hours_spent = float(request.form.get('hours_spent') or 0)
        db.session.commit()
        flash('Task updated.', 'success')
        return redirect(url_for('projects.project_board', id=pid))
    users = User.query.order_by(User.full_name).all()
    return render_template('projects/task_form.html', project=project, task=task,
                           users=users, stages=TASK_STAGES)


@projects_bp.route('/<int:pid>/tasks/<int:tid>/stage', methods=['POST'])
@login_required
def task_stage(pid, tid):
    task = db.get_or_404(Task, tid)
    task.stage = request.form.get('stage', task.stage)
    db.session.commit()
    return redirect(url_for('projects.project_board', id=pid))


@projects_bp.route('/<int:pid>/tasks/<int:tid>/delete', methods=['POST'])
@login_required
def task_delete(pid, tid):
    task = db.get_or_404(Task, tid)
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted.', 'success')
    return redirect(url_for('projects.project_board', id=pid))
