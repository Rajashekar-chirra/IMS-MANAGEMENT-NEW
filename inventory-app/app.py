from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.masters import masters_bp
    from routes.purchase import purchase_bp
    from routes.distributions import distributions_bp
    from routes.warranty import warranty_bp
    from routes.stocks import stocks_bp
    from routes.exports import exports_bp
    from routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(masters_bp, url_prefix='/masters')
    app.register_blueprint(purchase_bp, url_prefix='/purchase')
    app.register_blueprint(distributions_bp, url_prefix='/distributions')
    app.register_blueprint(warranty_bp, url_prefix='/warranty')
    app.register_blueprint(stocks_bp, url_prefix='/stocks')
    app.register_blueprint(exports_bp, url_prefix='/exports')
    app.register_blueprint(reports_bp, url_prefix='/reports')

    with app.app_context():
        db.create_all()
        # Schema migrations: add new columns that db.create_all() cannot handle
        with db.engine.connect() as _conn:
            _conn.execute(db.text(
                "ALTER TABLE purchase_items ADD COLUMN IF NOT EXISTS vendor_id INTEGER REFERENCES vendors(id);"
            ))
            _conn.commit()
        _seed_data()

    return app


def _seed_data():
    from models import User

    if User.query.first():
        return

    admin = User(username='admin', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
