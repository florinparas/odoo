from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Contact, Lead, User

crm_bp = Blueprint('crm', __name__)

LEAD_STAGES = [
    ('new', 'New'),
    ('qualified', 'Qualified'),
    ('proposition', 'Proposition'),
    ('won', 'Won'),
    ('lost', 'Lost'),
]


# ─── Contacts ─────────────────────────────────────────────────────────

@crm_bp.route('/contacts')
@login_required
def contacts():
    q = request.args.get('q', '')
    query = Contact.query
    if q:
        query = query.filter(Contact.name.ilike(f'%{q}%'))
    contacts = query.order_by(Contact.name).all()
    return render_template('crm/contacts.html', contacts=contacts, q=q)


@crm_bp.route('/contacts/new', methods=['GET', 'POST'])
@login_required
def contact_new():
    if request.method == 'POST':
        contact = Contact(
            name=request.form['name'],
            email=request.form.get('email', ''),
            phone=request.form.get('phone', ''),
            company=request.form.get('company', ''),
            job_title=request.form.get('job_title', ''),
            city=request.form.get('city', ''),
            country=request.form.get('country', ''),
            contact_type=request.form.get('contact_type', 'company'),
            is_customer='is_customer' in request.form,
            is_vendor='is_vendor' in request.form,
            notes=request.form.get('notes', ''),
        )
        db.session.add(contact)
        db.session.commit()
        flash('Contact created.', 'success')
        return redirect(url_for('crm.contact_detail', id=contact.id))
    return render_template('crm/contact_form.html', contact=None)


@crm_bp.route('/contacts/<int:id>')
@login_required
def contact_detail(id):
    contact = db.get_or_404(Contact, id)
    return render_template('crm/contact_detail.html', contact=contact)


@crm_bp.route('/contacts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def contact_edit(id):
    contact = db.get_or_404(Contact, id)
    if request.method == 'POST':
        contact.name = request.form['name']
        contact.email = request.form.get('email', '')
        contact.phone = request.form.get('phone', '')
        contact.company = request.form.get('company', '')
        contact.job_title = request.form.get('job_title', '')
        contact.city = request.form.get('city', '')
        contact.country = request.form.get('country', '')
        contact.contact_type = request.form.get('contact_type', 'company')
        contact.is_customer = 'is_customer' in request.form
        contact.is_vendor = 'is_vendor' in request.form
        contact.notes = request.form.get('notes', '')
        db.session.commit()
        flash('Contact updated.', 'success')
        return redirect(url_for('crm.contact_detail', id=contact.id))
    return render_template('crm/contact_form.html', contact=contact)


@crm_bp.route('/contacts/<int:id>/delete', methods=['POST'])
@login_required
def contact_delete(id):
    contact = db.get_or_404(Contact, id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact deleted.', 'success')
    return redirect(url_for('crm.contacts'))


# ─── Leads / Pipeline ─────────────────────────────────────────────────

@crm_bp.route('/pipeline')
@login_required
def pipeline():
    leads_by_stage = {}
    for code, label in LEAD_STAGES:
        leads_by_stage[code] = {
            'label': label,
            'leads': Lead.query.filter_by(stage=code).order_by(Lead.created_at.desc()).all()
        }
    return render_template('crm/pipeline.html', leads_by_stage=leads_by_stage, stages=LEAD_STAGES)


@crm_bp.route('/leads')
@login_required
def leads():
    leads = Lead.query.order_by(Lead.created_at.desc()).all()
    return render_template('crm/leads.html', leads=leads, stages=LEAD_STAGES)


@crm_bp.route('/leads/new', methods=['GET', 'POST'])
@login_required
def lead_new():
    if request.method == 'POST':
        lead = Lead(
            name=request.form['name'],
            contact_id=request.form.get('contact_id') or None,
            email=request.form.get('email', ''),
            phone=request.form.get('phone', ''),
            expected_revenue=float(request.form.get('expected_revenue') or 0),
            probability=int(request.form.get('probability') or 10),
            stage=request.form.get('stage', 'new'),
            priority=int(request.form.get('priority') or 0),
            assigned_to=request.form.get('assigned_to') or None,
            description=request.form.get('description', ''),
            source=request.form.get('source', ''),
        )
        db.session.add(lead)
        db.session.commit()
        flash('Lead created.', 'success')
        return redirect(url_for('crm.pipeline'))
    contacts = Contact.query.order_by(Contact.name).all()
    users = User.query.order_by(User.full_name).all()
    return render_template('crm/lead_form.html', lead=None, contacts=contacts,
                           users=users, stages=LEAD_STAGES)


@crm_bp.route('/leads/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def lead_edit(id):
    lead = db.get_or_404(Lead, id)
    if request.method == 'POST':
        lead.name = request.form['name']
        lead.contact_id = request.form.get('contact_id') or None
        lead.email = request.form.get('email', '')
        lead.phone = request.form.get('phone', '')
        lead.expected_revenue = float(request.form.get('expected_revenue') or 0)
        lead.probability = int(request.form.get('probability') or 10)
        lead.stage = request.form.get('stage', 'new')
        lead.priority = int(request.form.get('priority') or 0)
        lead.assigned_to = request.form.get('assigned_to') or None
        lead.description = request.form.get('description', '')
        lead.source = request.form.get('source', '')
        db.session.commit()
        flash('Lead updated.', 'success')
        return redirect(url_for('crm.pipeline'))
    contacts = Contact.query.order_by(Contact.name).all()
    users = User.query.order_by(User.full_name).all()
    return render_template('crm/lead_form.html', lead=lead, contacts=contacts,
                           users=users, stages=LEAD_STAGES)


@crm_bp.route('/leads/<int:id>/stage', methods=['POST'])
@login_required
def lead_stage(id):
    lead = db.get_or_404(Lead, id)
    lead.stage = request.form.get('stage', lead.stage)
    db.session.commit()
    return redirect(url_for('crm.pipeline'))


@crm_bp.route('/leads/<int:id>/delete', methods=['POST'])
@login_required
def lead_delete(id):
    lead = db.get_or_404(Lead, id)
    db.session.delete(lead)
    db.session.commit()
    flash('Lead deleted.', 'success')
    return redirect(url_for('crm.leads'))
