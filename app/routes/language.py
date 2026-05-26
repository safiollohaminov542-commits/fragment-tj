"""Language switcher."""
from flask import Blueprint, redirect, request, session, url_for

from app.services.i18n import SUPPORTED_LANGS

language_bp = Blueprint("language", __name__)


@language_bp.route("/lang/<lang>")
def switch_language(lang: str):
    """Set language ва редирект."""
    if lang in SUPPORTED_LANGS:
        session["lang"] = lang
    next_url = request.args.get("next") or request.referrer or url_for("main.index")
    return redirect(next_url)
