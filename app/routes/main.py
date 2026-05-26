"""Public routes — homepage, gift listing, gift details."""
from flask import (
    Blueprint, render_template, abort, request, redirect, url_for, flash,
)
from flask_login import login_required, current_user

from app import db
from app.models import Gift, Order, Settings, InventoryItem
from app.services.currency import get_rates, get_ton_rate_dict
from app.services.wallet import debit, WalletError

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
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
    return render_template(
        "index.html", featured=featured, latest=latest,
        ton_rate_dict=get_ton_rate_dict(),
    )


@main_bp.route("/gifts")
def gifts_list():
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
        query = query.order_by(Gift.base_ton_price.asc())
    elif sort == "price_desc":
        query = query.order_by(Gift.base_ton_price.desc())
    else:
        query = query.order_by(Gift.created_at.desc())

    pagination = query.paginate(page=page, per_page=24, error_out=False)
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
        ton_rate_dict=get_ton_rate_dict(),
        q=q,
        collection=collection,
        sort=sort,
        collections=[c[0] for c in collections if c[0]],
    )


@main_bp.route("/gift/<slug>")
def gift_detail(slug: str):
    gift = Gift.query.filter_by(slug=slug).first_or_404()
    similar = (
        Gift.query.filter(
            Gift.id != gift.id, Gift.is_available.is_(True)
        )
        .order_by(Gift.created_at.desc())
        .limit(4)
        .all()
    )
    return render_template(
        "gifts/detail.html",
        gift=gift,
        similar=similar,
        ton_rate_dict=get_ton_rate_dict(),
    )


@main_bp.route("/buy/<int:gift_id>", methods=["POST"])
@login_required
def buy(gift_id: int):
    """Харид аз баланси user."""
    gift = Gift.query.get_or_404(gift_id)
    if not gift.is_available or gift.quantity < 1:
        flash("Ин gift дастрас нест.", "error")
        return redirect(url_for("main.gift_detail", slug=gift.slug))

    currency = (request.form.get("currency") or "TJS").upper()
    if currency not in ("TJS", "TON", "USD"):
        flash("Валютаи нодуруст.", "error")
        return redirect(url_for("main.gift_detail", slug=gift.slug))

    rates = get_rates()
    ton_rate_dict = {"tjs": rates["ton_tjs"], "usd": rates["ton_usd"]}
    price = gift.get_price_in(currency, ton_rate_dict)
    if price <= 0:
        flash("Нархи нодуруст.", "error")
        return redirect(url_for("main.gift_detail", slug=gift.slug))

    try:
        # Order сохта мешавад
        order = Order(
            user_id=current_user.id,
            gift_id=gift.id,
            quantity=1,
            ton_price=gift.final_ton_price,
            tjs_price=gift.get_price_in("TJS", ton_rate_dict),
            usd_price=gift.get_price_in("USD", ton_rate_dict),
            ton_rate_at_purchase=rates["ton_tjs"],
            paid_currency=currency,
            paid_amount=price,
            status="paid",
        )
        db.session.add(order)
        db.session.flush()

        # Аз balance debit
        debit(
            current_user, currency, price,
            kind="purchase",
            description=f"Харид: {gift.title}",
            related_order_id=order.id,
        )

        # Inventory item месозем
        inv = InventoryItem(
            user_id=current_user.id,
            gift_id=gift.id,
            order_id=order.id,
            status="owned",
        )
        db.session.add(inv)

        # Gift quantity decrement
        gift.quantity = max(0, gift.quantity - 1)
        if gift.quantity == 0:
            gift.is_available = False

        db.session.commit()
        flash(f"✓ Харид муваффақ! {gift.title} ҳозир дар inventar-и шумост.", "success")
        return redirect(url_for("profile.inventory"))

    except WalletError as e:
        db.session.rollback()
        flash(str(e), "error")
        return redirect(url_for("wallet.index"))
    except Exception as e:
        db.session.rollback()
        flash(f"Хатои дохилӣ: {e}", "error")
        return redirect(url_for("main.gift_detail", slug=gift.slug))


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
