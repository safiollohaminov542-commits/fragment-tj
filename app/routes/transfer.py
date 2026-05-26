"""Transfer requests — user-и заявка ба admin."""
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort,
)
from flask_login import login_required, current_user

from app import db
from app.models import InventoryItem, TransferRequest

transfer_bp = Blueprint("transfer", __name__)


@transfer_bp.route("/<int:item_id>/request", methods=["GET", "POST"])
@login_required
def request_transfer(item_id: int):
    item = InventoryItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    if item.status != "owned":
        flash("Ин gift аллакай дар transfer аст ё гузаронда шуд.", "error")
        return redirect(url_for("profile.inventory"))

    if request.method == "POST":
        username = (request.form.get("telegram_username") or "").strip().lstrip("@")[:64]
        if not username:
            flash("Telegram username лозим аст.", "error")
            return render_template("transfer/request.html", item=item)
        note = (request.form.get("note") or "").strip()[:500] or None

        # Эҷоди request
        tr = TransferRequest(
            user_id=current_user.id,
            inventory_item_id=item.id,
            telegram_username=username,
            note=note,
            status="pending",
        )
        item.status = "transfer_pending"
        db.session.add(tr)
        db.session.commit()

        flash("Заявка фиристода шуд. Дар муддати кӯтоҳ admin онро баррасӣ мекунад.", "success")
        return redirect(url_for("profile.transfers"))

    return render_template("transfer/request.html", item=item)
