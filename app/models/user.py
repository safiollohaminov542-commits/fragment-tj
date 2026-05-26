"""User model — email-based authentication."""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    # Email-based auth
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)

    # Profile
    name = db.Column(db.String(120), nullable=True)
    photo_url = db.Column(db.String(500), nullable=True)

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    orders = db.relationship("Order", backref="user", lazy="dynamic")
    verification_codes = db.relationship(
        "VerificationCode", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        """Hash password бо werkzeug."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Санҷиши password."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def display_name(self) -> str:
        """Ном барои UI."""
        if self.name:
            return self.name
        # Email-и пеш аз @
        return self.email.split("@")[0]

    @property
    def initial(self) -> str:
        """Ҳарфи якуми барои avatar fallback."""
        return (self.display_name[:1] or "?").upper()

    def __repr__(self) -> str:
        return f"<User {self.email}>"


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))
