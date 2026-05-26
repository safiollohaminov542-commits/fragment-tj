"""InventoryItem — gift-и user-и харидорӣ карда (in his profile)."""
from datetime import datetime
from app import db


class InventoryItem(db.Model):
    """User-и харидорӣ кардаи gift."""

    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    gift_id = db.Column(db.Integer, db.ForeignKey("gifts.id"), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True, unique=True)

    # Status: 'owned' | 'transfer_pending' | 'transferred'
    status = db.Column(db.String(30), default="owned", nullable=False)

    acquired_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    transferred_at = db.Column(db.DateTime, nullable=True)

    gift = db.relationship("Gift")

    def __repr__(self) -> str:
        return f"<InventoryItem #{self.id} user={self.user_id} gift={self.gift_id}>"
