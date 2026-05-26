"""Auth routes — email + 6-digit code authentication."""
from datetime import datetime
from email_validator import validate_email, EmailNotValidError

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    current_app,
)
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import User, VerificationCode
from app.models.verification import RESEND_COOLDOWN_SECONDS
from app.services.mail import send_verification_code

auth_bp = Blueprint("auth", __name__)


# ============================================================================
# HELPERS
# ============================================================================

def _normalize_email(raw: str) -> str | None:
    """Email-ро санҷида ва normalize мекунад. None агар нодуруст бошад."""
    if not raw:
        return None
    try:
        result = validate_email(raw.strip(), check_deliverability=False)
        return result.normalized.lower()
    except EmailNotValidError:
        return None


def _flash_success(msg: str) -> None:
    flash(msg, "success")


def _flash_error(msg: str) -> None:
    flash(msg, "error")


# ============================================================================
# REGISTER
# ============================================================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Сабтнома: email + name + password → code мефиристад → verify."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "GET":
        return render_template("auth/register.html")

    # POST
    email = _normalize_email(request.form.get("email", ""))
    name = (request.form.get("name") or "").strip()[:120]
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")

    if not email:
        _flash_error("Email-и нодуруст.")
        return render_template("auth/register.html", form_email="", form_name=name)

    if len(password) < 6:
        _flash_error("Password бояд ҳадди ақал 6 ҳарф бошад.")
        return render_template("auth/register.html", form_email=email, form_name=name)

    if password != password_confirm:
        _flash_error("Password-ҳо мутобиқат намекунанд.")
        return render_template("auth/register.html", form_email=email, form_name=name)

    existing = User.query.filter_by(email=email).first()
    if existing:
        if existing.is_email_verified:
            _flash_error("Чунин email аллакай сабт шудааст. Login кунед.")
            return redirect(url_for("auth.login"))
        # Email сабт шуд аммо verify нашуд — code-и нав мефиристем
        user = existing
        user.set_password(password)
        if name:
            user.name = name
    else:
        user = User(email=email, name=name or None, is_email_verified=False)
        user.set_password(password)
        db.session.add(user)

    db.session.flush()

    code_obj = VerificationCode.create_for_user(user.id, purpose="register")
    db.session.commit()

    try:
        send_verification_code(email, code_obj.code, purpose="register")
    except Exception as e:
        current_app.logger.exception("Email send failed: %s", e)
        _flash_error("Хато ҳангоми фиристодани email. Лутфан баъдтар кӯшиш кунед.")
        return render_template("auth/register.html", form_email=email, form_name=name)

    session["pending_verify_user_id"] = user.id
    session["pending_verify_purpose"] = "register"
    _flash_success(f"Коди 6-рақама ба {email} фиристода шуд.")
    return redirect(url_for("auth.verify"))


# ============================================================================
# LOGIN — email + password
# ============================================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login: email + password → code → verify."""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "GET":
        return render_template("auth/login.html")

    # POST
    email = _normalize_email(request.form.get("email", ""))
    password = request.form.get("password", "")

    if not email or not password:
        _flash_error("Email ва password лозиманд.")
        return render_template("auth/login.html", form_email=email or "")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        _flash_error("Email ё password нодуруст.")
        return render_template("auth/login.html", form_email=email)

    if not user.is_active:
        _flash_error("Ҳисоб блок шудааст.")
        return render_template("auth/login.html", form_email=email)

    if not user.is_email_verified:
        # Email тасдиқ нашуд — ба register flow равем
        code_obj = VerificationCode.create_for_user(user.id, purpose="register")
        db.session.commit()
        send_verification_code(email, code_obj.code, purpose="register")

        session["pending_verify_user_id"] = user.id
        session["pending_verify_purpose"] = "register"
        _flash_success(f"Email-и шумо ҳоло тасдиқ нашудааст. Коди тасдиқ ба {email} фиристода шуд.")
        return redirect(url_for("auth.verify"))

    # Code-и login мефиристем
    code_obj = VerificationCode.create_for_user(user.id, purpose="login")
    db.session.commit()
    send_verification_code(email, code_obj.code, purpose="login")

    session["pending_verify_user_id"] = user.id
    session["pending_verify_purpose"] = "login"
    _flash_success(f"Коди 6-рақама ба {email} фиристода шуд.")
    return redirect(url_for("auth.verify"))


# ============================================================================
# VERIFY
# ============================================================================

@auth_bp.route("/verify", methods=["GET", "POST"])
def verify():
    """Code-ро санҷида user-ро login мекунад."""
    user_id = session.get("pending_verify_user_id")
    purpose = session.get("pending_verify_purpose", "login")

    if not user_id:
        _flash_error("Аввал register ё login кунед.")
        return redirect(url_for("auth.login"))

    user = db.session.get(User, user_id)
    if not user:
        session.pop("pending_verify_user_id", None)
        return redirect(url_for("auth.login"))

    if request.method == "GET":
        latest = VerificationCode.latest_for_user(user.id)
        cooldown = 0
        if latest:
            _, cooldown = latest.can_resend()
        return render_template(
            "auth/verify.html",
            email=user.email,
            cooldown=cooldown,
            purpose=purpose,
        )

    # POST
    submitted = (request.form.get("code") or "").strip()
    if not submitted or len(submitted) != 6 or not submitted.isdigit():
        _flash_error("Коди 6-рақама гузоред.")
        return redirect(url_for("auth.verify"))

    latest = VerificationCode.latest_for_user(user.id)
    if not latest:
        _flash_error("Коди фаъол ёфт нашуд. Аз нав login кунед.")
        return redirect(url_for("auth.login"))

    if not latest.verify(submitted):
        if latest.is_expired:
            _flash_error("Код кӯҳна шуд. Боз бифиристед.")
        elif latest.is_used:
            _flash_error("Ин код аллакай истифода шуд.")
        elif latest.attempts >= 5:
            _flash_error("Хеле зиёд кӯшиш. Кодро аз нав бифиристед.")
        else:
            _flash_error("Коди нодуруст.")
        return redirect(url_for("auth.verify"))

    # ✓ Verified!
    if purpose == "register":
        user.is_email_verified = True

    user.last_login_at = datetime.utcnow()
    db.session.commit()

    session.pop("pending_verify_user_id", None)
    session.pop("pending_verify_purpose", None)

    login_user(user, remember=True)
    _flash_success(f"Хуш омадед, {user.display_name}!")
    return redirect(url_for("main.index"))


# ============================================================================
# RESEND CODE
# ============================================================================

@auth_bp.route("/resend-code", methods=["POST"])
def resend_code():
    """Code-и нав мефиристад (бо cooldown санҷӣ)."""
    user_id = session.get("pending_verify_user_id")
    purpose = session.get("pending_verify_purpose", "login")

    if not user_id:
        return redirect(url_for("auth.login"))

    user = db.session.get(User, user_id)
    if not user:
        return redirect(url_for("auth.login"))

    latest = VerificationCode.latest_for_user(user.id)
    if latest:
        ok, remaining = latest.can_resend()
        if not ok:
            _flash_error(f"Лутфан {remaining} сония интизор шавед.")
            return redirect(url_for("auth.verify"))

    code_obj = VerificationCode.create_for_user(user.id, purpose=purpose)
    db.session.commit()
    send_verification_code(user.email, code_obj.code, purpose=purpose)

    _flash_success(f"Коди нав ба {user.email} фиристода шуд.")
    return redirect(url_for("auth.verify"))


# ============================================================================
# LOGOUT
# ============================================================================

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    _flash_success("Шумо аз система баромадед.")
    return redirect(url_for("main.index"))
