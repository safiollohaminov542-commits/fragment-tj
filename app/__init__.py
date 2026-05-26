"""Flask application factory."""
from flask import Flask, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

from config import config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from app.services.mail import mail
    mail.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Барои дидани ин саҳифа login кунед."
    login_manager.login_message_category = "info"

    # Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    from app.routes.wallet import wallet_bp
    from app.routes.profile import profile_bp
    from app.routes.transfer import transfer_bp
    from app.routes.language import language_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(wallet_bp, url_prefix="/wallet")
    app.register_blueprint(profile_bp, url_prefix="/profile")
    app.register_blueprint(transfer_bp, url_prefix="/transfer")
    app.register_blueprint(language_bp)

    # CSRF exemption барои JSON API
    csrf.exempt(api_bp)
    # Inline JSON endpoints
    from app.routes.admin import gift_import_preview
    csrf.exempt(gift_import_preview)
    from app.routes.wallet import preview as wallet_preview
    csrf.exempt(wallet_preview)

    # Ensure upload folder exists
    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)
    (app.config["UPLOAD_FOLDER"] / "lottie").mkdir(parents=True, exist_ok=True)

    # Auto-promote admins (тибқи ADMIN_EMAILS)
    from flask_login import user_logged_in
    from app.models import User

    @user_logged_in.connect_via(app)
    def _auto_promote_admin(sender, user):
        admin_emails = app.config.get("ADMIN_EMAILS", [])
        if user and user.email and user.email.lower() in admin_emails and not user.is_admin:
            user.is_admin = True
            db.session.commit()

    # i18n
    from app.services.i18n import install_i18n
    install_i18n(app)

    # Template context: rates, settings, currencies
    from app.services.currency import get_rates
    from app.models.settings import Settings

    @app.context_processor
    def inject_globals():
        try:
            rates = get_rates()
        except Exception:
            rates = {"ton_tjs": 52.0, "ton_usd": 5.5, "usd_tjs": 10.9}
        return {
            "rates": rates,
            "ton_rate": rates.get("ton_tjs", 52.0),  # backward compat
            "Settings": Settings,
            "site_name": app.config.get("SITE_NAME", "Fragment TJ"),
        }

    return app
