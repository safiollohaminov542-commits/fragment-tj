"""Telegram Login Widget verification.

Тибқи документатсияи Telegram:
https://core.telegram.org/widgets/login#checking-authorization
"""
import hashlib
import hmac
import time


def verify_telegram_auth(data: dict, bot_token: str, max_age: int = 86400) -> bool:
    """
    Маълумоти Telegram Login Widget-ро санҷидан.

    Args:
        data: Маълумоти оянда аз Telegram (id, first_name, hash, auth_date, ...)
        bot_token: Bot token аз @BotFather
        max_age: ҳадди ақали умри auth (бо сонияҳо)

    Returns:
        True агар маълумот валид ва тоза бошад.
    """
    if not bot_token:
        return False

    received_hash = data.get("hash")
    if not received_hash:
        return False

    auth_date = data.get("auth_date")
    if not auth_date:
        return False

    try:
        if (time.time() - int(auth_date)) > max_age:
            return False
    except (TypeError, ValueError):
        return False

    # Build data check string
    pairs = []
    for key in sorted(data.keys()):
        if key == "hash":
            continue
        pairs.append(f"{key}={data[key]}")
    data_check_string = "\n".join(pairs)

    # Secret key = SHA256(bot_token)
    secret_key = hashlib.sha256(bot_token.encode()).digest()

    # HMAC-SHA256
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(calculated_hash, received_hash)
