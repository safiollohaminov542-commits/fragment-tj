"""Admin panel — gift management, settings, orders."""
import os
import re
import uuid
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    current_app,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models import Gift, Order, Settings, User
from app.services.ton_price import get_current_ton_rate, invalidate_cache

admin_bp = Blueprint("admin", __name__)


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return wrapper


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\u0400-\u04FF\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:200] or uuid.uuid4().hex[:12]


def _allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


def _save_image(file_storage) -> str | None:
    if not file_storage or not file_storage.filename:
        return None
    if not _allowed_file(file_storage.filename):
        return None
    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    path = current_app.config["UPLOAD_FOLDER"] / name
    file_storage.save(path)
    return f"/static/uploads/{name}"


@admin_bp.route("/")
@admin_required
def dashboard():
    stats = {
        "total_gifts": Gift.query.count(),
        "available_gifts": Gift.query.filter_by(is_available=True).count(),
        "total_users": User.query.count(),
        "total_orders": Order.query.count(),
        "pending_orders": Order.query.filter_by(status="pending").count(),
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_orders=recent_orders,
        ton_rate=get_current_ton_rate(),
    )


# === Gifts ===
@admin_bp.route("/gifts")
@admin_required
def gifts():
    page = request.args.get("page", 1, type=int)
    pagination = Gift.query.order_by(Gift.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template(
        "admin/gifts.html", pagination=pagination, gifts=pagination.items
    )


@admin_bp.route("/gifts/new", methods=["GET", "POST"])
@admin_required
def gift_new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Title лозим аст.", "error")
            return redirect(url_for("admin.gift_new"))

        slug = _slugify(title)
        # ensure unique
        if Gift.query.filter_by(slug=slug).first():
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"

        image_url = _save_image(request.files.get("image")) or request.form.get(
            "image_url"
        ) or None

        gift = Gift(
            title=title,
            slug=slug,
            description=request.form.get("description"),
            image_url=image_url,
            ton_price=float(request.form.get("ton_price", 0) or 0),
            manual_tjs_price=float(request.form["manual_tjs_price"])
            if request.form.get("manual_tjs_price")
            else None,
            use_manual_price=bool(request.form.get("use_manual_price")),
            fragment_url=request.form.get("fragment_url") or None,
            collection=request.form.get("collection") or None,
            rarity=request.form.get("rarity") or None,
            is_available=bool(request.form.get("is_available")),
            is_featured=bool(request.form.get("is_featured")),
            quantity=int(request.form.get("quantity", 1) or 1),
        )
        db.session.add(gift)
        db.session.commit()
        flash(f"Gift '{gift.title}' илова шуд.", "success")
        return redirect(url_for("admin.gifts"))

    return render_template("admin/gift_form.html", gift=None)


@admin_bp.route("/gifts/<int:gift_id>/edit", methods=["GET", "POST"])
@admin_required
def gift_edit(gift_id):
    gift = Gift.query.get_or_404(gift_id)
    if request.method == "POST":
        gift.title = request.form.get("title", gift.title).strip()
        gift.description = request.form.get("description")
        new_image = _save_image(request.files.get("image"))
        if new_image:
            gift.image_url = new_image
        elif request.form.get("image_url"):
            gift.image_url = request.form.get("image_url")

        gift.ton_price = float(request.form.get("ton_price", 0) or 0)
        gift.manual_tjs_price = (
            float(request.form["manual_tjs_price"])
            if request.form.get("manual_tjs_price")
            else None
        )
        gift.use_manual_price = bool(request.form.get("use_manual_price"))
        gift.fragment_url = request.form.get("fragment_url") or None
        gift.collection = request.form.get("collection") or None
        gift.rarity = request.form.get("rarity") or None
        gift.is_available = bool(request.form.get("is_available"))
        gift.is_featured = bool(request.form.get("is_featured"))
        gift.quantity = int(request.form.get("quantity", 1) or 1)

        db.session.commit()
        flash("Gift нав карда шуд.", "success")
        return redirect(url_for("admin.gifts"))

    return render_template("admin/gift_form.html", gift=gift)


@admin_bp.route("/gifts/<int:gift_id>/delete", methods=["POST"])
@admin_required
def gift_delete(gift_id):
    gift = Gift.query.get_or_404(gift_id)
    db.session.delete(gift)
    db.session.commit()
    flash("Gift нест карда шуд.", "info")
    return redirect(url_for("admin.gifts"))


# === Settings ===
@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    if request.method == "POST":
        for key in Settings.DEFAULTS:
            if key in ("use_manual_rate", "maintenance_mode"):
                Settings.set(key, "true" if request.form.get(key) else "false")
            else:
                value = request.form.get(key, "")
                Settings.set(key, value)
        invalidate_cache()
        flash("Settings нав карда шуданд.", "success")
        return redirect(url_for("admin.settings"))

    items = Settings.query.all()
    settings_dict = {s.key: s for s in items}
    return render_template(
        "admin/settings.html",
        settings=settings_dict,
        defaults=Settings.DEFAULTS,
        live_rate=get_current_ton_rate(),
    )


# === Orders ===
@admin_bp.route("/orders")
@admin_required
def orders():
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "").strip()
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    pagination = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=30, error_out=False
    )
    return render_template(
        "admin/orders.html",
        pagination=pagination,
        orders=pagination.items,
        status=status,
    )


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status")
    if new_status in ("pending", "paid", "completed", "cancelled"):
        order.status = new_status
        db.session.commit()
        flash(f"Order #{order.id} → {new_status}", "success")
    return redirect(url_for("admin.orders"))


# === Users ===
@admin_bp.route("/users")
@admin_required
def users():
    page = request.args.get("page", 1, type=int)
    pagination = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=30, error_out=False
    )
    return render_template(
        "admin/users.html", pagination=pagination, users=pagination.items
    )
