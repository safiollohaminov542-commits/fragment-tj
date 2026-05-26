"""Gift model — Fragment-style NFT gift."""
from datetime import datetime
from app import db


class Gift(db.Model):
    __tablename__ = "gifts"

    id = db.Column(db.Integer, primary_key=True)

    # Basics
    title = db.Column(db.String(200), nullable=False)  # "Vice Cream #150025"
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    # Media
    image_url = db.Column(db.String(500), nullable=True)  # static preview
    animation_url = db.Column(db.String(500), nullable=True)  # Lottie JSON file
    background_color = db.Column(db.String(20), nullable=True)  # hex from backdrop

    # Source
    fragment_url = db.Column(db.String(500), nullable=True)
    collection = db.Column(db.String(120), nullable=True)  # "Vice Cream"
    gift_number = db.Column(db.Integer, nullable=True)  # 150025

    # Pricing — base price аз Fragment, markup-и Admin
    base_ton_price = db.Column(db.Float, nullable=False, default=0.0)  # Fragment original price
    markup_percent = db.Column(db.Float, default=0.0, nullable=False)  # +50% etc.
    manual_tjs_price = db.Column(db.Float, nullable=True)  # final override
    use_manual_price = db.Column(db.Boolean, default=False, nullable=False)

    # Attributes (parsed аз Fragment)
    model_name = db.Column(db.String(100), nullable=True)  # "Ube Cream"
    model_rarity = db.Column(db.Float, nullable=True)  # 2.0 (= 2%)
    backdrop_name = db.Column(db.String(100), nullable=True)  # "Mustard"
    backdrop_rarity = db.Column(db.Float, nullable=True)
    symbol_name = db.Column(db.String(100), nullable=True)  # "Greek Sun"
    symbol_rarity = db.Column(db.Float, nullable=True)

    # Issued
    issued_number = db.Column(db.Integer, nullable=True)  # 402506
    issued_total = db.Column(db.Integer, nullable=True)  # 490553

    # Owner info (snapshot аз Fragment, ҳамчун info)
    fragment_owner = db.Column(db.String(120), nullable=True)
    fragment_status = db.Column(db.String(30), nullable=True)  # "for_sale" | "auction"

    # Marketplace
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    # Meta
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @property
    def final_ton_price(self) -> float:
        """Нархи ниҳоӣ бо markup."""
        return round(self.base_ton_price * (1 + self.markup_percent / 100), 4)

    @property
    def has_animation(self) -> bool:
        return bool(self.animation_url)

    def get_price_in(self, currency: str, ton_rate: dict) -> float:
        """
        Нархро дар валютаи додашуда мегардонад.
        ton_rate: dict {'tjs': 52.0, 'usd': 5.5} = курси 1 TON
        """
        if self.use_manual_price and self.manual_tjs_price is not None:
            tjs = self.manual_tjs_price
            ton_in_tjs = ton_rate.get("tjs", 52.0)
            usd_in_tjs = ton_rate.get("tjs", 52.0) / max(ton_rate.get("usd", 5.5), 0.01)
            if currency == "TJS":
                return round(tjs, 2)
            if currency == "TON":
                return round(tjs / max(ton_in_tjs, 0.01), 4)
            if currency == "USD":
                return round(tjs / max(usd_in_tjs, 0.01), 2)

        ton = self.final_ton_price
        if currency == "TON":
            return round(ton, 4)
        if currency == "TJS":
            return round(ton * ton_rate.get("tjs", 52.0), 2)
        if currency == "USD":
            return round(ton * ton_rate.get("usd", 5.5), 2)
        return 0.0

    def to_dict(self, ton_rate: dict) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "description": self.description,
            "image_url": self.image_url,
            "animation_url": self.animation_url,
            "background_color": self.background_color,
            "collection": self.collection,
            "gift_number": self.gift_number,
            "base_ton_price": self.base_ton_price,
            "markup_percent": self.markup_percent,
            "final_ton_price": self.final_ton_price,
            "price_tjs": self.get_price_in("TJS", ton_rate),
            "price_usd": self.get_price_in("USD", ton_rate),
            "is_manual_price": self.use_manual_price,
            "model": {"name": self.model_name, "rarity": self.model_rarity},
            "backdrop": {"name": self.backdrop_name, "rarity": self.backdrop_rarity},
            "symbol": {"name": self.symbol_name, "rarity": self.symbol_rarity},
            "issued": {"number": self.issued_number, "total": self.issued_total},
            "fragment": {
                "owner": self.fragment_owner,
                "status": self.fragment_status,
                "url": self.fragment_url,
            },
            "is_available": self.is_available,
            "is_featured": self.is_featured,
            "quantity": self.quantity,
        }

    def __repr__(self) -> str:
        return f"<Gift {self.title} — {self.final_ton_price} TON>"
