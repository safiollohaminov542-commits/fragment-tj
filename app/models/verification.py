"""VerificationCode model — 6-digit codes барои email verification."""
import secrets
from datetime import datetime, timedelta
from app import db


# Codes 10 daqiqa valid мемонанд
CODE_LIFETIME_MINUTES = 10
# Maximum 5 саҳви талошӣ кардан мумкин
MAX_ATTEMPTS = 5
# Минимум 60 сония байни send-ҳо (rate limit)
RESEND_COOLDOWN_SECONDS = 60


class VerificationCode(db.Model):
    """Code-и 6-рақама ки ба email фиристода мешавад."""

    __tablename__ = "verification_codes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )

    code = db.Column(db.String(6), nullable=False)
    purpose = db.Column(
        db.String(30), nullable=False, default="login"
    )  # login | register

    attempts = db.Column(db.Integer, default=0, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    @staticmethod
    def generate_code() -> str:
        """Дар тасодуф 6-рақамаи 100000-999999 эҷод мекунад."""
        # secrets.randbelow(900000) → 0..899999, +100000 → 100000..999999
        return f"{secrets.randbelow(900000) + 100000:06d}"

    @classmethod
    def create_for_user(cls, user_id: int, purpose: str = "login") -> "VerificationCode":
        """Code-и нав месозад (cooldown санҷида намешавад)."""
        # Code-ҳои кӯҳнаи ҳамин user-ро invalidate мекунем
        cls.query.filter_by(user_id=user_id, is_used=False).update(
            {"is_used": True}, synchronize_session=False
        )

        item = cls(
            user_id=user_id,
            code=cls.generate_code(),
            purpose=purpose,
            expires_at=datetime.utcnow() + timedelta(minutes=CODE_LIFETIME_MINUTES),
        )
        db.session.add(item)
        db.session.flush()
        return item

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return (
            not self.is_used
            and not self.is_expired
            and self.attempts < MAX_ATTEMPTS
        )

    def verify(self, submitted_code: str) -> bool:
        """Санҷиши code-и воридшуда."""
        self.attempts += 1
        if not self.is_valid:
            db.session.commit()
            return False
        # constant-time compare
        if secrets.compare_digest(self.code, submitted_code.strip()):
            self.is_used = True
            db.session.commit()
            return True
        db.session.commit()
        return False

    @classmethod
    def latest_for_user(cls, user_id: int) -> "VerificationCode | None":
        """Code-и охирини user-ро (агар бошад) бармегардонад."""
        return (
            cls.query.filter_by(user_id=user_id)
            .order_by(cls.created_at.desc())
            .first()
        )

    def can_resend(self) -> tuple[bool, int]:
        """
        Санҷиш — оё аллакай code фиристода шуд камтар аз cooldown-сония пеш.

        Returns:
            (can_resend, seconds_remaining)
        """
        elapsed = (datetime.utcnow() - self.created_at).total_seconds()
        if elapsed >= RESEND_COOLDOWN_SECONDS:
            return True, 0
        return False, int(RESEND_COOLDOWN_SECONDS - elapsed)

    def __repr__(self) -> str:
        return f"<VerificationCode {self.code} for user_id={self.user_id}>"
