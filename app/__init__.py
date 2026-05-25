"""Flask application factory."""
from flask import Flask
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
    """Create ва конфигуратсия кардани Flask app."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Барои дидани ин саҳифа login кунед."

    # Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    # CSRF exemption барои webhook/API endpoints
    csrf.exempt(api_bp)

    # Ensure upload folder exists
    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)

    # Template context processors
    from app.services.ton_price import get_current_ton_rate

    @app.context_processor
    def inject_globals():
        return {
            "ton_rate": get_current_ton_rate(),
            "bot_username": app.config["TELEGRAM_BOT_USERNAME"],
        }

    return app
