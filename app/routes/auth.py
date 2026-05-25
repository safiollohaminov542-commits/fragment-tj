"""Auth routes — Telegram Login + Google OAuth."""
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    session,
    abort,
)
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import User
from app.services.telegram_auth import verify_telegram_auth
from app.services.google_auth import oauth, init_google_oauth

auth_bp = Blueprint("auth", __name__)

_google_initialized = False


def _ensure_google_initialized():
    global _google_initialized
    if not _google_initialized:
        if current_app.config.get("GOOGLE_CLIENT_ID"):
            init_google_oauth(current_app._get_current_object())
            _google_initialized = True


@auth_bp.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    return render_template("auth/login.html")


@auth_bp.route("/telegram-callback")
def telegram_callback():
    """
    Callback аз Telegram Login Widget.
    Widget query параметрҳоро мефиристад.
    """
    data = request.args.to_dict()
    bot_token = current_app.config["TELEGRAM_BOT_TOKEN"]

    if not verify_telegram_auth(data, bot_token):
        flash("Маълумоти Telegram-и нодуруст ё кӯҳна.", "error")
        return redirect(url_for("auth.login"))

    tg_id = int(data["id"])
    user = User.query.filter_by(telegram_id=tg_id).first()
    if not user:
        user = User(telegram_id=tg_id)
        db.session.add(user)

    user.username = data.get("username")
    user.first_name = data.get("first_name")
    user.last_name = data.get("last_name")
    user.photo_url = data.get("photo_url")
    user.last_login_at = datetime.utcnow()
    db.session.commit()

    login_user(user, remember=True)
    flash(f"Хуш омадед, {user.display_name}!", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/google")
def google_login():
    _ensure_google_initialized()
    if not current_app.config.get("GOOGLE_CLIENT_ID"):
        flash("Google login ҳоло конфигуратсия нашудааст.", "error")
        return redirect(url_for("auth.login"))
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/google/callback")
def google_callback():
    _ensure_google_initialized()
    try:
        token = oauth.google.authorize_access_token()
    except Exception:
        flash("Хато дар Google login.", "error")
        return redirect(url_for("auth.login"))

    info = token.get("userinfo") or oauth.google.parse_id_token(token, None)
    if not info:
        flash("Маълумоти Google гирифта нашуд.", "error")
        return redirect(url_for("auth.login"))

    google_id = info.get("sub")
    email = info.get("email")
    user = User.query.filter_by(google_id=google_id).first()
    if not user and email:
        user = User.query.filter_by(email=email).first()

    if not user:
        user = User(google_id=google_id, email=email)
        db.session.add(user)
    else:
        user.google_id = google_id

    user.first_name = info.get("given_name")
    user.last_name = info.get("family_name")
    user.photo_url = info.get("picture")
    user.last_login_at = datetime.utcnow()
    db.session.commit()

    login_user(user, remember=True)
    flash(f"Хуш омадед, {user.display_name}!", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Шумо аз система баромадед.", "info")
    return redirect(url_for("main.index"))
