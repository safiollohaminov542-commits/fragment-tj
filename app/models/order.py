"""Order model."""
from datetime import datetime
from app import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    gift_id = db.Column(db.Integer, db.ForeignKey("gifts.id"), nullable=False)

    quantity = db.Column(db.Integer, default=1, nullable=False)

    # Snapshot of pricing at purchase time
    ton_price = db.Column(db.Float, nullable=False)
    tjs_price = db.Column(db.Float, nullable=False)
    usd_price = db.Column(db.Float, nullable=True)
    ton_rate_at_purchase = db.Column(db.Float, nullable=False)

    # Payment info
    paid_currency = db.Column(db.String(5), nullable=True)  # TJS / TON / USD
    paid_amount = db.Column(db.Float, nullable=True)

    status = db.Column(
        db.String(30), default="pending", nullable=False
    )  # pending, paid, completed, cancelled, refunded

    contact_info = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    gift = db.relationship("Gift", backref="orders")
    inventory_item = db.relationship(
        "InventoryItem",
        uselist=False,
        backref="order",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Order #{self.id} — {self.status}>"
