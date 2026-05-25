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
        "ton_tjs_rate": ("52.0", "Курси як TON ба сомонӣ (manual override)"),
        "use_manual_rate": ("false", "Истифодаи manual rate ба ҷои API"),
        "site_name": ("Fragment TJ", "Номи сайт"),
        "site_tagline": ("Маркетплейси Telegram Gifts дар Тоҷикистон", "Tagline"),
        "contact_telegram": ("@your_username", "Telegram барои тамос"),
        "maintenance_mode": ("false", "Маинтенанс — сайт пӯшида"),
        "merchant_ton_wallet": (
            "",
            "TON wallet барои қабули payment (UQ... ё EQ...)",
        ),
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
            "true",
            "1",
            "yes",
            "on",
        )

    @classmethod
    def ensure_defaults(cls) -> None:
        """Дар startup default settings-ро месозад."""
        for key, (value, description) in cls.DEFAULTS.items():
            if not cls.query.filter_by(key=key).first():
                db.session.add(cls(key=key, value=value, description=description))
        db.session.commit()

    def __repr__(self) -> str:
        return f"<Settings {self.key}={self.value}>"
