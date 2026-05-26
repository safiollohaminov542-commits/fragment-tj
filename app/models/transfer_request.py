"""TransferRequest — user-и заявка медиҳад gift-ро ба Telegram username гузаронад."""
from datetime import datetime
from app import db


class TransferRequest(db.Model):
    __tablename__ = "transfer_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    inventory_item_id = db.Column(
        db.Integer, db.ForeignKey("inventory_items.id"), nullable=False, unique=True
    )

    telegram_username = db.Column(db.String(64), nullable=False)  # @ali_user
    note = db.Column(db.Text, nullable=True)

    # pending | approved | sent | rejected
    status = db.Column(db.String(30), default="pending", nullable=False)
    admin_notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)

    inventory_item = db.relationship("InventoryItem")

    def __repr__(self) -> str:
        return f"<TransferRequest #{self.id} → {self.telegram_username} ({self.status})>"
