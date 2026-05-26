"""Email service — Flask-Mail integration барои фиристодани code-ҳо."""
import logging
from threading import Thread

from flask import current_app, render_template
from flask_mail import Mail, Message

logger = logging.getLogger(__name__)

# Singleton — дар app/__init__.py init мешавад
mail = Mail()


def _send_async(app, msg: Message) -> None:
    """Email-ро дар background thread мефиристад."""
    with app.app_context():
        try:
            mail.send(msg)
            logger.info("Email фиристода шуд: %s", msg.subject)
        except Exception as e:
            logger.exception("Email send failed: %s", e)


def send_email_async(
    subject: str,
    recipients: list[str],
    html_body: str,
    text_body: str | None = None,
) -> None:
    """Email-ро ба background thread мефиристад (то request-ро block накунад)."""
    app = current_app._get_current_object()
    sender = app.config.get("MAIL_DEFAULT_SENDER")
    msg = Message(subject=subject, recipients=recipients, sender=sender)
    msg.html = html_body
    if text_body:
        msg.body = text_body
    else:
        # plain-text fallback аз html
        import re

        msg.body = re.sub(r"<[^>]+>", "", html_body).strip()

    Thread(target=_send_async, args=(app, msg), daemon=True).start()


def send_verification_code(email: str, code: str, purpose: str = "login") -> None:
    """Email-и code-и 6-рақамаро мефиристад."""
    site_name = current_app.config.get("SITE_NAME", "Fragment TJ")

    subject_map = {
        "login": f"Коди вурудат — {site_name}",
        "register": f"Коди тасдиқи сабтном — {site_name}",
    }
    title_map = {
        "login": "Коди вуруд ба ҳисоб",
        "register": "Коди тасдиқи сабтном",
    }
    intro_map = {
        "login": "Барои ворид шудан ба ҳисоби худ ин код-ро истифода кунед:",
        "register": "Барои анҷоми сабтном ин кодро истифода кунед:",
    }

    subject = subject_map.get(purpose, subject_map["login"])
    title = title_map.get(purpose, title_map["login"])
    intro = intro_map.get(purpose, intro_map["login"])

    html = render_template(
        "emails/verification_code.html",
        site_name=site_name,
        title=title,
        intro=intro,
        code=code,
        email=email,
    )

    send_email_async(subject=subject, recipients=[email], html_body=html)
