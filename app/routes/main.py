"""Public routes — homepage, gift listing, gift details."""
from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import Gift, Order, Settings
from app.services.ton_price import get_current_ton_rate

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Homepage."""
    if Settings.get_bool("maintenance_mode"):
        return render_template("maintenance.html")

    featured = (
        Gift.query.filter_by(is_featured=True, is_available=True).limit(8).all()
    )
    latest = (
        Gift.query.filter_by(is_available=True)
        .order_by(Gift.created_at.desc())
        .limit(12)
        .all()
    )
    rate = get_current_ton_rate()
    return render_template(
        "index.html", featured=featured, latest=latest, ton_rate=rate
    )


@main_bp.route("/gifts")
def gifts_list():
    """Тамоми gift-ҳо бо search/filter."""
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()
    collection = request.args.get("collection", "").strip()
    sort = request.args.get("sort", "newest")

    query = Gift.query.filter_by(is_available=True)
    if q:
        query = query.filter(Gift.title.ilike(f"%{q}%"))
    if collection:
        query = query.filter_by(collection=collection)

    if sort == "price_asc":
        query = query.order_by(Gift.ton_price.asc())
    elif sort == "price_desc":
        query = query.order_by(Gift.ton_price.desc())
    else:
        query = query.order_by(Gift.created_at.desc())

    pagination = query.paginate(page=page, per_page=24, error_out=False)
    rate = get_current_ton_rate()
    collections = (
        db.session.query(Gift.collection)
        .filter(Gift.collection.isnot(None))
        .distinct()
        .all()
    )

    return render_template(
        "gifts/list.html",
        pagination=pagination,
        gifts=pagination.items,
        ton_rate=rate,
        q=q,
        collection=collection,
        sort=sort,
        collections=[c[0] for c in collections if c[0]],
    )


@main_bp.route("/gift/<slug>")
def gift_detail(slug: str):
    gift = Gift.query.filter_by(slug=slug).first_or_404()
    rate = get_current_ton_rate()
    similar = (
        Gift.query.filter(
            Gift.id != gift.id, Gift.is_available.is_(True)
        )
        .order_by(Gift.created_at.desc())
        .limit(4)
        .all()
    )
    return render_template(
        "gifts/detail.html", gift=gift, ton_rate=rate, similar=similar
    )


@main_bp.route("/buy/<int:gift_id>", methods=["POST"])
@login_required
def buy(gift_id: int):
    """Сохтани order (pending). Pay-флоуи воқеӣ дар ин MVP нест."""
    gift = Gift.query.get_or_404(gift_id)
    if not gift.is_available or gift.quantity < 1:
        flash("Ин gift дастрас нест.", "error")
        return redirect(url_for("main.gift_detail", slug=gift.slug))

    rate = get_current_ton_rate()
    contact = request.form.get("contact", "").strip()

    order = Order(
        user_id=current_user.id,
        gift_id=gift.id,
        quantity=1,
        ton_price=gift.ton_price,
        tjs_price=gift.get_tjs_price(rate),
        ton_rate_at_purchase=rate,
        contact_info=contact or None,
        status="pending",
    )
    db.session.add(order)
    db.session.commit()
    flash(
        f"Order #{order.id} сохта шуд! Барои пардохт бо мо тамос гиред.", "success"
    )
    return redirect(url_for("main.my_orders"))


@main_bp.route("/orders")
@login_required
def my_orders():
    orders = (
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("orders/list.html", orders=orders)


@main_bp.route("/about")
def about():
    return render_template("about.html")
