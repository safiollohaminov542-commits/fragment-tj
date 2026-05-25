"""User model."""
from datetime import datetime
from flask import current_app
from flask_login import UserMixin

from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    # Auth identifiers (яктоаш бояд бошад)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=True, index=True)
    google_id = db.Column(db.String(120), unique=True, nullable=True, index=True)
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)

    # Profile
    username = db.Column(db.String(80), nullable=True)
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    photo_url = db.Column(db.String(500), nullable=True)

    # Meta
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    orders = db.relationship("Order", backref="user", lazy="dynamic")

    @property
    def display_name(self) -> str:
        """Ном барои нишон додан дар UI."""
        if self.first_name:
            full = self.first_name
            if self.last_name:
                full += f" {self.last_name}"
            return full
        if self.username:
            return f"@{self.username}"
        if self.email:
            return self.email
        return f"User #{self.id}"

    @property
    def is_admin(self) -> bool:
        """Оё admin аст? (тибқи ADMIN_TELEGRAM_IDS дар .env)."""
        admin_ids = current_app.config.get("ADMIN_TELEGRAM_IDS", [])
        return self.telegram_id is not None and self.telegram_id in admin_ids

    def __repr__(self) -> str:
        return f"<User {self.display_name}>"


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))
