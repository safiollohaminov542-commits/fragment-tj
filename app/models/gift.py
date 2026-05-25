"""Gift model — маҳсулоти асосии marketplace."""
from datetime import datetime
from app import db


class Gift(db.Model):
    __tablename__ = "gifts"

    id = db.Column(db.Integer, primary_key=True)

    # Basics
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)

    # Pricing
    ton_price = db.Column(db.Float, nullable=False, default=0.0)
    manual_tjs_price = db.Column(db.Float, nullable=True)  # override
    use_manual_price = db.Column(db.Boolean, default=False, nullable=False)

    # Source
    fragment_url = db.Column(db.String(500), nullable=True)
    collection = db.Column(db.String(120), nullable=True)
    rarity = db.Column(db.String(80), nullable=True)

    # Status
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    # Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def get_tjs_price(self, ton_rate: float) -> float:
        """Нархи TJS-ро ҳисоб мекунад. Manual override-ро ҳам месанҷад."""
        if self.use_manual_price and self.manual_tjs_price is not None:
            return round(self.manual_tjs_price, 2)
        return round(self.ton_price * ton_rate, 2)

    def to_dict(self, ton_rate: float = 52.0) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "image_url": self.image_url,
            "ton_price": self.ton_price,
            "tjs_price": self.get_tjs_price(ton_rate),
            "is_manual_price": self.use_manual_price,
            "collection": self.collection,
            "rarity": self.rarity,
            "is_available": self.is_available,
            "is_featured": self.is_featured,
            "quantity": self.quantity,
            "fragment_url": self.fragment_url,
        }

    def __repr__(self) -> str:
        return f"<Gift {self.title} — {self.ton_price} TON>"
