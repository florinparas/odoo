from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User


login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from modules.auth import auth_bp
    from modules.dashboard import dashboard_bp
    from modules.crm import crm_bp
    from modules.sales import sales_bp
    from modules.inventory import inventory_bp
    from modules.invoicing import invoicing_bp
    from modules.projects import projects_bp
    from modules.hr import hr_bp
    from modules.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(crm_bp, url_prefix='/crm')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(invoicing_bp, url_prefix='/invoicing')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(hr_bp, url_prefix='/hr')
    app.register_blueprint(settings_bp, url_prefix='/settings')

    with app.app_context():
        db.create_all()
        _seed_admin(app)

    return app


def _seed_admin(app):
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@odoo-flask.local',
            full_name='Administrator',
            role='admin',
            avatar_color='#714B67',
        )
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
