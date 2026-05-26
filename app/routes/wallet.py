"""User wallet — balance overview, currency convert."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.models import BalanceTransaction
from app.services.currency import convert as currency_convert
from app.services.wallet import (
    convert_balance,
    WalletError,
    VALID_CURRENCIES,
)

wallet_bp = Blueprint("wallet", __name__)


@wallet_bp.route("/")
@login_required
def index():
    """Wallet asosi — balances + транзаксияҳои охирин."""
    transactions = (
        BalanceTransaction.query.filter_by(user_id=current_user.id)
        .order_by(BalanceTransaction.created_at.desc())
        .limit(50)
        .all()
    )
    return render_template(
        "wallet/index.html",
        transactions=transactions,
    )


@wallet_bp.route("/convert", methods=["POST"])
@login_required
def convert_action():
    """Convert: from one currency to another бо курси феълӣ."""
    from_c = (request.form.get("from") or "").upper().strip()
    to_c = (request.form.get("to") or "").upper().strip()
    try:
        amount = float(request.form.get("amount", "0"))
    except (TypeError, ValueError):
        amount = 0.0

    if from_c not in VALID_CURRENCIES or to_c not in VALID_CURRENCIES:
        flash("Валютаи нодуруст.", "error")
        return redirect(url_for("wallet.index"))
    if amount <= 0:
        flash("Маблағ бояд > 0 бошад.", "error")
        return redirect(url_for("wallet.index"))

    try:
        convert_balance(current_user, from_c, to_c, amount)
        db.session.commit()
        flash(f"Convert муваффақ — {amount:.2f} {from_c} → {to_c}", "success")
    except WalletError as e:
        db.session.rollback()
        flash(str(e), "error")
    except Exception:
        db.session.rollback()
        flash("Хатои дохилӣ.", "error")

    return redirect(url_for("wallet.index"))


@wallet_bp.route("/preview")
@login_required
def preview():
    """AJAX preview: чанд X-ро гирам барои Y."""
    from flask import jsonify
    from_c = (request.args.get("from") or "").upper().strip()
    to_c = (request.args.get("to") or "").upper().strip()
    try:
        amount = float(request.args.get("amount", "0"))
    except (TypeError, ValueError):
        amount = 0.0
    if from_c not in VALID_CURRENCIES or to_c not in VALID_CURRENCIES or amount <= 0:
        return jsonify({"ok": False, "result": 0})
    result = currency_convert(amount, from_c, to_c)
    return jsonify({"ok": True, "result": result})
