"""Entry point барои Flask app."""
import os
from app import create_app, db
from app.models import User, Gift, Order, Settings, VerificationCode

app = create_app(os.getenv("FLASK_ENV", "development"))


@app.shell_context_processor
def make_shell_context():
    """`flask shell` барои тестинги моделҳо."""
    return {
        "db": db,
        "User": User,
        "Gift": Gift,
        "Order": Order,
        "Settings": Settings,
        "VerificationCode": VerificationCode,
    }


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        Settings.ensure_defaults()
    app.run(host="0.0.0.0", port=5000, debug=True)
