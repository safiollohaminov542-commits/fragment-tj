"""TON → TJS курс бо CoinGecko API + cache."""
import time
import logging
import requests
from flask import current_app

logger = logging.getLogger(__name__)

# Simple in-memory cache (барои production Redis истифода кун)
_cache = {"rate": None, "ts": 0}
CACHE_TTL = 300  # 5 дақиқа


def fetch_ton_to_usd() -> float | None:
    """Курси TON ба USD аз CoinGecko."""
    try:
        url = current_app.config["COINGECKO_API_URL"]
        resp = requests.get(
            url,
            params={"ids": "the-open-network", "vs_currencies": "usd"},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        return float(data["the-open-network"]["usd"])
    except Exception as e:
        logger.warning("CoinGecko TON/USD fetch failed: %s", e)
        return None


def fetch_usd_to_tjs() -> float | None:
    """Курси USD ба TJS. Default ~10.9 TJS = 1 USD."""
    try:
        resp = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "tether", "vs_currencies": "tjs"},
            timeout=5,
        )
        if resp.ok:
            data = resp.json()
            return float(data.get("tether", {}).get("tjs", 0)) or None
    except Exception as e:
        logger.warning("USD/TJS fetch failed: %s", e)
    return None


def fetch_ton_to_tjs_live() -> float | None:
    """TON → TJS аз live API."""
    ton_usd = fetch_ton_to_usd()
    if not ton_usd:
        return None
    usd_tjs = fetch_usd_to_tjs() or 10.9
    return round(ton_usd * usd_tjs, 2)


def get_current_ton_rate() -> float:
    """
    Курси феълии TON → TJS-ро бармегардонад.

    Афзалият:
    1. Manual rate (агар admin фаъол кардааст)
    2. Cached live rate
    3. Fresh API fetch
    4. Default fallback аз config
    """
    from app.models import Settings  # avoid circular

    try:
        if Settings.get_bool("use_manual_rate"):
            return Settings.get_float(
                "ton_tjs_rate", current_app.config["DEFAULT_TON_TJS_RATE"]
            )
    except Exception:
        pass

    # Check cache
    now = time.time()
    if _cache["rate"] and (now - _cache["ts"]) < CACHE_TTL:
        return _cache["rate"]

    # Try live
    live = fetch_ton_to_tjs_live()
    if live:
        _cache["rate"] = live
        _cache["ts"] = now
        return live

    # Fallback ба settings/config
    try:
        return Settings.get_float(
            "ton_tjs_rate", current_app.config["DEFAULT_TON_TJS_RATE"]
        )
    except Exception:
        return current_app.config.get("DEFAULT_TON_TJS_RATE", 52.0)


def invalidate_cache() -> None:
    _cache["rate"] = None
    _cache["ts"] = 0
