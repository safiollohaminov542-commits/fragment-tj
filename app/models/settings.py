"""Settings model — конфигуратсияи қобили тағйир аз admin panel."""
from datetime import datetime
from app import db


class Settings(db.Model):
    """Key-value store барои site settings."""

    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    DEFAULTS = {
        # Курсҳо: агар use_manual_*=true бошад, manual rate истифода мешавад,
        # вагарна аз CoinGecko гирифта мешавад.
        "use_manual_ton_tjs": ("false", "Истифодаи manual rate барои TON→TJS"),
        "manual_ton_tjs": ("52.0", "Manual rate: 1 TON = ? TJS"),

        "use_manual_ton_usd": ("false", "Истифодаи manual rate барои TON→USD"),
        "manual_ton_usd": ("5.5", "Manual rate: 1 TON = ? USD"),

        "use_manual_usd_tjs": ("false", "Истифодаи manual rate барои USD→TJS"),
        "manual_usd_tjs": ("10.9", "Manual rate: 1 USD = ? TJS"),

        # Default markup за нав gift-и нав дар Quick Import
        "default_markup_percent": ("30.0", "Дефолт markup % барои gift-ҳои import"),

        # Site
        "site_name": ("Fragment TJ", "Номи сайт"),
        "site_tagline": ("Маркетплейси Telegram Gifts дар Тоҷикистон", "Tagline"),
        "contact_telegram": ("@your_username", "Telegram барои тамос"),
        "maintenance_mode": ("false", "Маинтенанс — сайт пӯшида"),
    }

    @classmethod
    def get(cls, key: str, default: str = "") -> str:
        item = cls.query.filter_by(key=key).first()
        return item.value if item else default

    @classmethod
    def set(cls, key: str, value: str, description: str = None) -> None:
        item = cls.query.filter_by(key=key).first()
        if item:
            item.value = value
            if description:
                item.description = description
        else:
            item = cls(key=key, value=value, description=description)
            db.session.add(item)
        db.session.commit()

    @classmethod
    def get_float(cls, key: str, default: float = 0.0) -> float:
        try:
            return float(cls.get(key, str(default)))
        except (TypeError, ValueError):
            return default

    @classmethod
    def get_bool(cls, key: str, default: bool = False) -> bool:
        return cls.get(key, str(default).lower()).strip().lower() in (
            "true", "1", "yes", "on",
        )

    @classmethod
    def ensure_defaults(cls) -> None:
        for key, (value, description) in cls.DEFAULTS.items():
            if not cls.query.filter_by(key=key).first():
                db.session.add(cls(key=key, value=value, description=description))
        db.session.commit()

    def __repr__(self) -> str:
        return f"<Settings {self.key}={self.value}>"
