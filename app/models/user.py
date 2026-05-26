"""User model — email-based authentication + wallet."""
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
    telegram_username = db.Column(db.String(64), nullable=True)
    preferred_language = db.Column(db.String(5), default="tg", nullable=False)
    preferred_currency = db.Column(db.String(5), default="TJS", nullable=False)

    # Wallet (балансҳо дар се валюта — нигоҳдорӣ дар ҳамин валюта)
    balance_tjs = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    balance_ton = db.Column(db.Numeric(12, 6), default=0, nullable=False)
    balance_usd = db.Column(db.Numeric(12, 2), default=0, nullable=False)

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    orders = db.relationship("Order", backref="user", lazy="dynamic")
    inventory_items = db.relationship("InventoryItem", backref="user", lazy="dynamic")
    transfer_requests = db.relationship("TransferRequest", backref="user", lazy="dynamic")
    balance_transactions = db.relationship(
        "BalanceTransaction", backref="user", lazy="dynamic"
    )
    verification_codes = db.relationship(
        "VerificationCode", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def display_name(self) -> str:
        if self.name:
            return self.name
        return self.email.split("@")[0]

    @property
    def initial(self) -> str:
        return (self.display_name[:1] or "?").upper()

    def get_balance(self, currency: str) -> float:
        """Balance дар валютаи додашуда."""
        c = currency.upper()
        if c == "TJS":
            return float(self.balance_tjs or 0)
        if c == "TON":
            return float(self.balance_ton or 0)
        if c == "USD":
            return float(self.balance_usd or 0)
        return 0.0

    def set_balance(self, currency: str, amount: float) -> None:
        c = currency.upper()
        if c == "TJS":
            self.balance_tjs = amount
        elif c == "TON":
            self.balance_ton = amount
        elif c == "USD":
            self.balance_usd = amount

    def __repr__(self) -> str:
        return f"<User {self.email}>"


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))
