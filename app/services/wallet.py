"""Wallet service — balance management, transactions, conversions."""
from decimal import Decimal
from typing import Optional

from app import db
from app.models import User, BalanceTransaction
from app.services.currency import convert


class WalletError(Exception):
    """Хатои wallet — insufficient funds, бад currency, etc."""


VALID_CURRENCIES = ("TJS", "TON", "USD")


def _validate_currency(c: str) -> str:
    c = (c or "").upper().strip()
    if c not in VALID_CURRENCIES:
        raise WalletError(f"Currency-и нодуруст: {c}")
    return c


def _record_tx(
    user: User,
    kind: str,
    currency: str,
    amount: float,
    description: Optional[str] = None,
    related_order_id: Optional[int] = None,
    admin_id: Optional[int] = None,
) -> BalanceTransaction:
    """Транзаксия log мекунад. NB: amount аллакай ба balance илова шуд!"""
    tx = BalanceTransaction(
        user_id=user.id,
        kind=kind,
        currency=currency,
        amount=amount,
        balance_after=user.get_balance(currency),
        description=description,
        related_order_id=related_order_id,
        admin_id=admin_id,
    )
    db.session.add(tx)
    return tx


def credit(
    user: User,
    currency: str,
    amount: float,
    *,
    kind: str = "topup",
    description: Optional[str] = None,
    admin_id: Optional[int] = None,
) -> BalanceTransaction:
    """Balance-ро зиёд мекунад (admin top-up, refund, и т.д.)."""
    currency = _validate_currency(currency)
    amount = float(amount)
    if amount <= 0:
        raise WalletError("Маблағ бояд > 0 бошад.")
    new_balance = user.get_balance(currency) + amount
    user.set_balance(currency, new_balance)
    return _record_tx(user, kind, currency, amount, description, admin_id=admin_id)


def debit(
    user: User,
    currency: str,
    amount: float,
    *,
    kind: str = "purchase",
    description: Optional[str] = None,
    related_order_id: Optional[int] = None,
) -> BalanceTransaction:
    """Balance-ро кам мекунад (харид, conversion, и т.д.)."""
    currency = _validate_currency(currency)
    amount = float(amount)
    if amount <= 0:
        raise WalletError("Маблағ бояд > 0 бошад.")
    current = user.get_balance(currency)
    if current < amount - 1e-9:
        raise WalletError(
            f"Balance-и кофӣ нест. Дар balance: {current:.2f} {currency}, "
            f"Лозим: {amount:.2f} {currency}"
        )
    user.set_balance(currency, current - amount)
    return _record_tx(
        user,
        kind,
        currency,
        -amount,
        description,
        related_order_id=related_order_id,
    )


def adjust(
    user: User,
    currency: str,
    new_balance: float,
    *,
    description: str = "Admin adjustment",
    admin_id: Optional[int] = None,
) -> BalanceTransaction:
    """Set absolute balance (admin only — масалан refund + correction)."""
    currency = _validate_currency(currency)
    new_balance = float(new_balance)
    if new_balance < 0:
        raise WalletError("Balance-и манфӣ намешавад.")
    diff = new_balance - user.get_balance(currency)
    user.set_balance(currency, new_balance)
    return _record_tx(
        user,
        "adjust",
        currency,
        diff,
        description,
        admin_id=admin_id,
    )


def convert_balance(
    user: User,
    from_currency: str,
    to_currency: str,
    amount: float,
) -> tuple[BalanceTransaction, BalanceTransaction]:
    """
    Convert amount аз from_currency ба to_currency бо курси феълӣ.
    Дар натиҷа 2 transaction (out + in).
    """
    from_currency = _validate_currency(from_currency)
    to_currency = _validate_currency(to_currency)
    if from_currency == to_currency:
        raise WalletError("Валютаҳо ҳамон як хеланд.")

    converted = convert(amount, from_currency, to_currency)
    if converted <= 0:
        raise WalletError("Натиҷаи conversion 0 шуд (курс?)")

    # Аз account-и user → из from кам мекунем
    out_tx = debit(
        user,
        from_currency,
        amount,
        kind="convert_out",
        description=f"Convert {amount:.4f} {from_currency} → {converted:.4f} {to_currency}",
    )
    # → ба to илова мекунем
    in_tx = credit(
        user,
        to_currency,
        converted,
        kind="convert_in",
        description=f"Convert {amount:.4f} {from_currency} → {converted:.4f} {to_currency}",
    )
    return out_tx, in_tx
