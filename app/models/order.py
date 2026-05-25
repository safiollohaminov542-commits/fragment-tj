"""Order model."""
from datetime import datetime
from app import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    gift_id = db.Column(db.Integer, db.ForeignKey("gifts.id"), nullable=False)

    quantity = db.Column(db.Integer, default=1, nullable=False)
    ton_price = db.Column(db.Float, nullable=False)  # snapshot
    tjs_price = db.Column(db.Float, nullable=False)  # snapshot
    ton_rate_at_purchase = db.Column(db.Float, nullable=False)

    status = db.Column(
        db.String(30), default="pending", nullable=False
    )  # pending, paid, completed, cancelled

    contact_info = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    gift = db.relationship("Gift", backref="orders")

    def __repr__(self) -> str:
        return f"<Order #{self.id} — {self.status}>"
