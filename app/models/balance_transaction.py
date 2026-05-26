"""BalanceTransaction — log-и ҳамаи тағйирёбии balance-и users."""
from datetime import datetime
from app import db


class BalanceTransaction(db.Model):
    __tablename__ = "balance_transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    # 'topup' | 'purchase' | 'refund' | 'convert_in' | 'convert_out' | 'adjust'
    kind = db.Column(db.String(30), nullable=False)

    currency = db.Column(db.String(5), nullable=False)  # TJS | TON | USD
    amount = db.Column(db.Float, nullable=False)  # +/-
    balance_after = db.Column(db.Float, nullable=False)

    description = db.Column(db.String(255), nullable=True)
    related_order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)

    # Admin кӣ инро кард (агар admin action бошад)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    related_order = db.relationship("Order", foreign_keys=[related_order_id])
    admin = db.relationship("User", foreign_keys=[admin_id])

    def __repr__(self) -> str:
        sign = "+" if self.amount >= 0 else ""
        return f"<BalanceTx user={self.user_id} {sign}{self.amount} {self.currency} ({self.kind})>"
