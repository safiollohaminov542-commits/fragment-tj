"""DEPRECATED — wrapper around services/currency.py барои backward compat."""
from app.services.currency import get_rates, invalidate_cache as _invalidate


def get_current_ton_rate() -> float:
    """Курси TON→TJS (compatibility shim)."""
    return get_rates()["ton_tjs"]


def invalidate_cache() -> None:
    _invalidate()
