"""Configuration файл барои Flask app."""
import os
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent
load_dotenv(basedir / ".env")


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


class Config:
    """Базавӣ конфигуратсия."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{basedir / 'fragment_tj.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Site
    SITE_NAME = os.getenv("SITE_NAME", "Fragment TJ")

    # === Email (Flask-Mail / Gmail SMTP) ===
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "465"))
    MAIL_USE_TLS = _bool("MAIL_USE_TLS", False)
    MAIL_USE_SSL = _bool("MAIL_USE_SSL", True)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER_NAME = os.getenv("MAIL_DEFAULT_SENDER_NAME", "Fragment TJ")
    MAIL_DEFAULT_SENDER_EMAIL = os.getenv("MAIL_DEFAULT_SENDER_EMAIL", MAIL_USERNAME)
    MAIL_DEFAULT_SENDER = (MAIL_DEFAULT_SENDER_NAME, MAIL_DEFAULT_SENDER_EMAIL)
    MAIL_MAX_EMAILS = int(os.getenv("MAIL_MAX_EMAILS", "10"))
    MAIL_SUPPRESS_SEND = _bool("MAIL_SUPPRESS_SEND", False)

    # Admin
    # Email-ҳои admin (бо вергул ҷудо). Ин email-ҳо автомат admin мешаванд.
    ADMIN_EMAILS = [
        e.strip().lower()
        for e in os.getenv("ADMIN_EMAILS", "").split(",")
        if e.strip()
    ]

    # TON Price
    COINGECKO_API_URL = os.getenv(
        "COINGECKO_API_URL", "https://api.coingecko.com/api/v3/simple/price"
    )
    DEFAULT_TON_TJS_RATE = float(os.getenv("DEFAULT_TON_TJS_RATE", "52.0"))

    # Uploads
    UPLOAD_FOLDER = basedir / "app" / "static" / "uploads"
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # Session
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7  # 1 ҳафта


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
