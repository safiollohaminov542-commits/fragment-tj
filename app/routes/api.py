"""JSON API endpoints."""
from flask import Blueprint, jsonify, request

from app.models import Gift
from app.services.currency import get_rates, get_ton_rate_dict, convert

api_bp = Blueprint("api", __name__)


@api_bp.route("/rates")
def rates():
    """Курсҳои феълӣ — TON/USD/TJS."""
    return jsonify(get_rates())


@api_bp.route("/ton-rate")
def ton_rate():
    """Курси феълии TON → TJS (backward compat)."""
    r = get_rates()
    return jsonify({"rate": r["ton_tjs"], "currency": "TJS"})


@api_bp.route("/convert")
def convert_endpoint():
    """Convert: ?amount=10&from=TON&to=TJS."""
    try:
        amount = float(request.args.get("amount", "0"))
    except ValueError:
        return jsonify({"error": "amount нодуруст"}), 400
    from_c = (request.args.get("from") or "").upper()
    to_c = (request.args.get("to") or "").upper()
    if from_c not in ("TJS", "TON", "USD") or to_c not in ("TJS", "TON", "USD"):
        return jsonify({"error": "currency нодуруст"}), 400
    return jsonify({
        "amount": amount,
        "from": from_c,
        "to": to_c,
        "result": convert(amount, from_c, to_c),
    })


@api_bp.route("/gifts")
def gifts():
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()
    query = Gift.query.filter_by(is_available=True)
    if q:
        query = query.filter(Gift.title.ilike(f"%{q}%"))
    pagination = query.order_by(Gift.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    rate_dict = get_ton_rate_dict()
    return jsonify({
        "items": [g.to_dict(rate_dict) for g in pagination.items],
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total,
    })


@api_bp.route("/gift/<slug>")
def gift_detail(slug: str):
    gift = Gift.query.filter_by(slug=slug).first()
    if not gift:
        return jsonify({"error": "not_found"}), 404
    return jsonify(gift.to_dict(get_ton_rate_dict()))
