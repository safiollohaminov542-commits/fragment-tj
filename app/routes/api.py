"""JSON API endpoints."""
from flask import Blueprint, jsonify, request

from app.models import Gift
from app.services.ton_price import get_current_ton_rate

api_bp = Blueprint("api", __name__)


@api_bp.route("/ton-rate")
def ton_rate():
    """Курси феълии TON → TJS."""
    return jsonify({"rate": get_current_ton_rate(), "currency": "TJS"})


@api_bp.route("/gifts")
def gifts():
    """Рӯйхати gift-ҳо барои AJAX/SPA."""
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()

    query = Gift.query.filter_by(is_available=True)
    if q:
        query = query.filter(Gift.title.ilike(f"%{q}%"))

    pagination = query.order_by(Gift.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    rate = get_current_ton_rate()
    return jsonify(
        {
            "items": [g.to_dict(rate) for g in pagination.items],
            "page": pagination.page,
            "pages": pagination.pages,
            "total": pagination.total,
            "ton_rate": rate,
        }
    )


@api_bp.route("/gift/<slug>")
def gift_detail(slug):
    gift = Gift.query.filter_by(slug=slug).first()
    if not gift:
        return jsonify({"error": "not_found"}), 404
    return jsonify(gift.to_dict(get_current_ton_rate()))
