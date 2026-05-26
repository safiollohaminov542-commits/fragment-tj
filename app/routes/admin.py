"""Admin panel — gifts, settings, orders, users, wallet, transfers."""
import re
import uuid
from datetime import datetime
from functools import wraps

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort,
    current_app, jsonify,
)
from flask_login import login_required, current_user

from app import db
from app.models import (
    Gift, Order, Settings, User, InventoryItem, TransferRequest,
    BalanceTransaction,
)
from app.services.currency import get_rates, get_ton_rate_dict, invalidate_cache
from app.services.wallet import credit, debit, adjust, WalletError, VALID_CURRENCIES
from app.services.fragment_parser import parse_fragment_url, FragmentParseError
from app.services.lottie import download_animation

admin_bp = Blueprint("admin", __name__)


# ============================================================================
# Decorators / Helpers
# ============================================================================

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
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9\u0400-\u04FF\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:200] or uuid.uuid4().hex[:12]


def _allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


def _save_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    if not _allowed_file(file_storage.filename):
        return None
    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    path = current_app.config["UPLOAD_FOLDER"] / name
    file_storage.save(path)
    return f"/static/uploads/{name}"


def _ensure_unique_slug(slug: str) -> str:
    if Gift.query.filter_by(slug=slug).first():
        return f"{slug}-{uuid.uuid4().hex[:6]}"
    return slug


# ============================================================================
# Dashboard
# ============================================================================

@admin_bp.route("/")
@admin_required
def dashboard():
    stats = {
        "total_gifts": Gift.query.count(),
        "available_gifts": Gift.query.filter_by(is_available=True).count(),
        "total_users": User.query.count(),
        "total_orders": Order.query.count(),
        "pending_transfers": TransferRequest.query.filter_by(status="pending").count(),
        "total_inventory": InventoryItem.query.count(),
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(8).all()
    pending_transfers = (
        TransferRequest.query.filter_by(status="pending")
        .order_by(TransferRequest.created_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_orders=recent_orders,
        pending_transfers=pending_transfers,
        rates=get_rates(),
    )


# ============================================================================
# Gifts
# ============================================================================

@admin_bp.route("/gifts")
@admin_required
def gifts():
    page = request.args.get("page", 1, type=int)
    pagination = Gift.query.order_by(Gift.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template(
        "admin/gifts.html",
        pagination=pagination,
        gifts=pagination.items,
        ton_rate_dict=get_ton_rate_dict(),
    )


@admin_bp.route("/gifts/import-preview", methods=["POST"])
@admin_required
def gift_import_preview():
    """AJAX: parse Fragment URL без сохтан."""
    payload = request.get_json(silent=True) or {}
    url = (payload.get("fragment_url") or "").strip()
    if not url:
        return jsonify({"ok": False, "error": "URL лозим аст"}), 400
    try:
        data = parse_fragment_url(url)
        return jsonify({"ok": True, "data": data.to_dict()})
    except FragmentParseError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@admin_bp.route("/gifts/import", methods=["POST"])
@admin_required
def gift_import():
    """Аз Fragment URL автомат gift месозад."""
    fragment_url = request.form.get("fragment_url", "").strip()
    if not fragment_url:
        flash("Fragment URL лозим аст.", "error")
        return redirect(url_for("admin.gift_new"))

    try:
        data = parse_fragment_url(fragment_url)
    except FragmentParseError as e:
        flash(f"Хато: {e}", "error")
        return redirect(url_for("admin.gift_new"))

    title = data.title or "Untitled Fragment Gift"
    slug = _ensure_unique_slug(_slugify(title))

    # Default markup
    default_markup = Settings.get_float("default_markup_percent", 30.0)

    # Animation download
    animation_url = None
    if data.animation_url:
        try:
            animation_url = download_animation(data.animation_url)
        except Exception:
            current_app.logger.exception("Animation download failed")

    gift = Gift(
        title=title,
        slug=slug,
        description=data.description,
        image_url=data.image_url,
        animation_url=animation_url,
        background_color=data.background_color,
        fragment_url=data.fragment_url,
        collection=data.collection,
        gift_number=data.gift_number,
        base_ton_price=data.ton_price or 0.0,
        markup_percent=default_markup,
        model_name=data.model.name,
        model_rarity=data.model.rarity,
        backdrop_name=data.backdrop.name,
        backdrop_rarity=data.backdrop.rarity,
        symbol_name=data.symbol.name,
        symbol_rarity=data.symbol.rarity,
        issued_number=data.issued_number,
        issued_total=data.issued_total,
        fragment_owner=data.fragment_owner,
        fragment_status=data.fragment_status,
        is_available=True,
        quantity=1,
    )
    db.session.add(gift)
    db.session.commit()

    flash(
        f"✓ Imported: {gift.title} ({gift.base_ton_price} TON, +{default_markup}% = {gift.final_ton_price} TON). "
        "Малумотро санҷида захира кунед.",
        "success",
    )
    return redirect(url_for("admin.gift_edit", gift_id=gift.id))


@admin_bp.route("/gifts/new", methods=["GET", "POST"])
@admin_required
def gift_new():
    if request.method == "POST":
        return _save_gift(None)
    default_markup = Settings.get_float("default_markup_percent", 30.0)
    return render_template(
        "admin/gift_form.html", gift=None, default_markup=default_markup
    )


@admin_bp.route("/gifts/<int:gift_id>/edit", methods=["GET", "POST"])
@admin_required
def gift_edit(gift_id: int):
    gift = Gift.query.get_or_404(gift_id)
    if request.method == "POST":
        return _save_gift(gift)
    return render_template(
        "admin/gift_form.html", gift=gift,
        ton_rate_dict=get_ton_rate_dict(),
    )


def _save_gift(gift):
    """Save gift form (create ё update)."""
    title = (request.form.get("title") or "").strip()
    if not title:
        flash("Title лозим аст.", "error")
        return redirect(request.url)

    is_new = gift is None
    if is_new:
        slug = _ensure_unique_slug(_slugify(title))
        gift = Gift(slug=slug)
        db.session.add(gift)

    gift.title = title
    gift.description = request.form.get("description")
    gift.collection = (request.form.get("collection") or "").strip() or None
    gift.fragment_url = (request.form.get("fragment_url") or "").strip() or None

    # Image
    new_image = _save_image(request.files.get("image"))
    if new_image:
        gift.image_url = new_image
    elif request.form.get("image_url"):
        gift.image_url = request.form["image_url"].strip() or None

    # Animation URL — direct link
    anim = (request.form.get("animation_url") or "").strip()
    gift.animation_url = anim or gift.animation_url
    gift.background_color = (request.form.get("background_color") or "").strip() or None

    # Pricing
    try:
        gift.base_ton_price = float(request.form.get("base_ton_price", 0) or 0)
    except ValueError:
        gift.base_ton_price = 0.0
    try:
        gift.markup_percent = float(request.form.get("markup_percent", 0) or 0)
    except ValueError:
        gift.markup_percent = 0.0

    manual_tjs = request.form.get("manual_tjs_price")
    gift.manual_tjs_price = float(manual_tjs) if manual_tjs else None
    gift.use_manual_price = bool(request.form.get("use_manual_price"))

    # Attributes
    gift.model_name = (request.form.get("model_name") or "").strip() or None
    gift.model_rarity = float(request.form["model_rarity"]) if request.form.get("model_rarity") else None
    gift.backdrop_name = (request.form.get("backdrop_name") or "").strip() or None
    gift.backdrop_rarity = float(request.form["backdrop_rarity"]) if request.form.get("backdrop_rarity") else None
    gift.symbol_name = (request.form.get("symbol_name") or "").strip() or None
    gift.symbol_rarity = float(request.form["symbol_rarity"]) if request.form.get("symbol_rarity") else None

    # Issued
    gift.issued_number = int(request.form["issued_number"]) if request.form.get("issued_number") else None
    gift.issued_total = int(request.form["issued_total"]) if request.form.get("issued_total") else None

    # Owner / status
    gift.fragment_owner = (request.form.get("fragment_owner") or "").strip() or None
    gift.fragment_status = (request.form.get("fragment_status") or "").strip() or None
    gift.gift_number = int(request.form["gift_number"]) if request.form.get("gift_number") else None

    # Marketplace
    try:
        gift.quantity = int(request.form.get("quantity", 1) or 1)
    except ValueError:
        gift.quantity = 1
    gift.is_available = bool(request.form.get("is_available"))
    gift.is_featured = bool(request.form.get("is_featured"))

    db.session.commit()
    flash("✓ Захира шуд." if not is_new else f"✓ Gift '{gift.title}' илова шуд.", "success")
    return redirect(url_for("admin.gifts"))


@admin_bp.route("/gifts/<int:gift_id>/delete", methods=["POST"])
@admin_required
def gift_delete(gift_id: int):
    gift = Gift.query.get_or_404(gift_id)
    db.session.delete(gift)
    db.session.commit()
    flash("Gift нест карда шуд.", "info")
    return redirect(url_for("admin.gifts"))


# ============================================================================
# Settings
# ============================================================================

@admin_bp.route("/settings", methods=["GET", "POST"])
@admin_required
def settings():
    if request.method == "POST":
        bool_keys = {"use_manual_ton_tjs", "use_manual_ton_usd", "use_manual_usd_tjs", "maintenance_mode"}
        for key in Settings.DEFAULTS:
            if key in bool_keys:
                Settings.set(key, "true" if request.form.get(key) else "false")
            else:
                value = request.form.get(key, "")
                Settings.set(key, value)
        invalidate_cache()
        flash("Settings нав шуд.", "success")
        return redirect(url_for("admin.settings"))

    items = Settings.query.all()
    return render_template(
        "admin/settings.html",
        settings={s.key: s for s in items},
        rates=get_rates(),
    )


@admin_bp.route("/settings/reset-rates", methods=["POST"])
@admin_required
def settings_reset_rates():
    """Бекор кардани manual rates → API истифода мешавад."""
    Settings.set("use_manual_ton_tjs", "false")
    Settings.set("use_manual_ton_usd", "false")
    Settings.set("use_manual_usd_tjs", "false")
    invalidate_cache()
    flash("✓ Курсҳо ба API barгашт.", "success")
    return redirect(url_for("admin.settings"))


# ============================================================================
# Orders
# ============================================================================

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
def order_status(order_id: int):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status")
    if new_status in ("pending", "paid", "completed", "cancelled", "refunded"):
        order.status = new_status
        db.session.commit()
        flash(f"Order #{order.id} → {new_status}", "success")
    return redirect(url_for("admin.orders"))


# ============================================================================
# Users + wallet topup
# ============================================================================

@admin_bp.route("/users")
@admin_required
def users():
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()
    query = User.query
    if q:
        query = query.filter(User.email.ilike(f"%{q}%") | User.name.ilike(f"%{q}%"))
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=30, error_out=False
    )
    return render_template(
        "admin/users.html",
        pagination=pagination,
        users=pagination.items,
        q=q,
    )


@admin_bp.route("/users/<int:user_id>")
@admin_required
def user_detail(user_id: int):
    user = User.query.get_or_404(user_id)
    transactions = (
        BalanceTransaction.query.filter_by(user_id=user.id)
        .order_by(BalanceTransaction.created_at.desc())
        .limit(50)
        .all()
    )
    inventory = (
        InventoryItem.query.filter_by(user_id=user.id)
        .order_by(InventoryItem.acquired_at.desc())
        .limit(20)
        .all()
    )
    return render_template(
        "admin/user_detail.html",
        user=user,
        transactions=transactions,
        inventory=inventory,
    )


@admin_bp.route("/users/<int:user_id>/topup", methods=["POST"])
@admin_required
def user_topup(user_id: int):
    user = User.query.get_or_404(user_id)
    currency = (request.form.get("currency") or "").upper().strip()
    try:
        amount = float(request.form.get("amount", "0"))
    except ValueError:
        amount = 0
    description = (request.form.get("description") or "").strip() or "Admin top-up"

    if currency not in VALID_CURRENCIES or amount <= 0:
        flash("Маълумоти нодуруст.", "error")
        return redirect(url_for("admin.user_detail", user_id=user.id))

    try:
        credit(user, currency, amount, kind="topup", description=description, admin_id=current_user.id)
        db.session.commit()
        flash(f"✓ +{amount} {currency} ба {user.email}", "success")
    except WalletError as e:
        db.session.rollback()
        flash(str(e), "error")

    return redirect(url_for("admin.user_detail", user_id=user.id))


@admin_bp.route("/users/<int:user_id>/adjust", methods=["POST"])
@admin_required
def user_adjust(user_id: int):
    user = User.query.get_or_404(user_id)
    currency = (request.form.get("currency") or "").upper().strip()
    try:
        new_balance = float(request.form.get("new_balance", "0"))
    except ValueError:
        new_balance = -1
    description = (request.form.get("description") or "").strip() or "Admin adjustment"

    if currency not in VALID_CURRENCIES or new_balance < 0:
        flash("Маълумоти нодуруст.", "error")
        return redirect(url_for("admin.user_detail", user_id=user.id))

    try:
        adjust(user, currency, new_balance, description=description, admin_id=current_user.id)
        db.session.commit()
        flash(f"✓ {currency}-и {user.email} → {new_balance}", "success")
    except WalletError as e:
        db.session.rollback()
        flash(str(e), "error")

    return redirect(url_for("admin.user_detail", user_id=user.id))


@admin_bp.route("/users/<int:user_id>/toggle-admin", methods=["POST"])
@admin_required
def user_toggle_admin(user_id: int):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Шумо наметавонед худатонро тағйир диҳед.", "error")
        return redirect(url_for("admin.users"))
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f"{user.email} → {'admin' if user.is_admin else 'user'}", "success")
    return redirect(url_for("admin.user_detail", user_id=user.id))


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@admin_required
def user_toggle_active(user_id: int):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Шумо наметавонед худатонро block кунед.", "error")
        return redirect(url_for("admin.users"))
    user.is_active = not user.is_active
    db.session.commit()
    flash(f"{user.email} → {'фаъол' if user.is_active else 'block'}", "success")
    return redirect(url_for("admin.user_detail", user_id=user.id))


# ============================================================================
# Transfer Requests
# ============================================================================

@admin_bp.route("/transfers")
@admin_required
def transfers():
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "").strip()
    query = TransferRequest.query
    if status:
        query = query.filter_by(status=status)
    pagination = query.order_by(TransferRequest.created_at.desc()).paginate(
        page=page, per_page=30, error_out=False
    )
    return render_template(
        "admin/transfers.html",
        pagination=pagination,
        transfers=pagination.items,
        status=status,
    )


@admin_bp.route("/transfers/<int:tr_id>/<action>", methods=["POST"])
@admin_required
def transfer_action(tr_id: int, action: str):
    tr = TransferRequest.query.get_or_404(tr_id)
    notes = (request.form.get("admin_notes") or "").strip() or None

    if action == "approve":
        tr.status = "approved"
        tr.processed_at = datetime.utcnow()
        tr.admin_notes = notes
    elif action == "send":
        tr.status = "sent"
        tr.processed_at = datetime.utcnow()
        tr.admin_notes = notes
        # Inventory item ҳамчун transferred медиҳем
        if tr.inventory_item:
            tr.inventory_item.status = "transferred"
            tr.inventory_item.transferred_at = datetime.utcnow()
    elif action == "reject":
        tr.status = "rejected"
        tr.processed_at = datetime.utcnow()
        tr.admin_notes = notes
        # Inventory item ба `owned` баргардонем (агар pending буд)
        if tr.inventory_item and tr.inventory_item.status == "transfer_pending":
            tr.inventory_item.status = "owned"
    else:
        flash("Action-и нодуруст.", "error")
        return redirect(url_for("admin.transfers"))

    db.session.commit()
    flash(f"✓ Transfer #{tr.id} → {tr.status}", "success")
    return redirect(url_for("admin.transfers"))
