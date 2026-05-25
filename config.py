"""Configuration файл барои Flask app."""
import os
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent
load_dotenv(basedir / ".env")


class Config:
    """Базавӣ конфигуратсия."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{basedir / 'fragment_tj.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "")

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # Admin
    ADMIN_TELEGRAM_IDS = [
        int(x.strip())
        for x in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",")
        if x.strip().isdigit()
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


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
