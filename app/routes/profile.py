"""User profile + inventory + balance overview."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import InventoryItem, Order, BalanceTransaction, TransferRequest

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/")
@login_required
def index():
    """Профили асосӣ — overview, balance, inventory preview."""
    inventory = (
        InventoryItem.query.filter_by(user_id=current_user.id)
        .order_by(InventoryItem.acquired_at.desc())
        .limit(8)
        .all()
    )
    recent_orders = (
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "profile/index.html",
        inventory_items=inventory,
        recent_orders=recent_orders,
    )


@profile_bp.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "POST":
        current_user.name = (request.form.get("name") or "").strip()[:120] or None
        tg = (request.form.get("telegram_username") or "").strip().lstrip("@")[:64]
        current_user.telegram_username = tg or None
        lang = (request.form.get("preferred_language") or "tg").strip()
        if lang in ("tg", "ru"):
            current_user.preferred_language = lang
        cur = (request.form.get("preferred_currency") or "TJS").strip().upper()
        if cur in ("TJS", "TON", "USD"):
            current_user.preferred_currency = cur
        db.session.commit()
        flash("Профил нав карда шуд.", "success")
        return redirect(url_for("profile.index"))
    return render_template("profile/edit.html")


@profile_bp.route("/inventory")
@login_required
def inventory():
    """Тамоми gifts-и user."""
    page = request.args.get("page", 1, type=int)
    pagination = (
        InventoryItem.query.filter_by(user_id=current_user.id)
        .order_by(InventoryItem.acquired_at.desc())
        .paginate(page=page, per_page=24, error_out=False)
    )
    return render_template(
        "profile/inventory.html",
        pagination=pagination,
        items=pagination.items,
    )


@profile_bp.route("/transfers")
@login_required
def transfers():
    """Transfer requests-и user."""
    requests_list = (
        TransferRequest.query.filter_by(user_id=current_user.id)
        .order_by(TransferRequest.created_at.desc())
        .all()
    )
    return render_template("profile/transfers.html", requests=requests_list)
