"""Currency service — TON/TJS/USD rates бо CoinGecko + admin manual override.

Cache: 5 daqiqa
Manual override: agar Settings.use_manual_*=true бошад, manual istifoda meshavad.
"""
import time
import logging
import requests
from flask import current_app

logger = logging.getLogger(__name__)

CACHE_TTL = 300  # 5 daqiqa
_cache: dict = {"data": None, "ts": 0}


def _fetch_live_rates() -> dict:
    """Аз CoinGecko: TON→USD, USD→TJS."""
    rates = {"ton_usd": None, "usd_tjs": None}
    try:
        url = current_app.config.get(
            "COINGECKO_API_URL",
            "https://api.coingecko.com/api/v3/simple/price",
        )
        resp = requests.get(
            url,
            params={
                "ids": "the-open-network,tether",
                "vs_currencies": "usd,tjs",
            },
            timeout=6,
        )
        resp.raise_for_status()
        data = resp.json()
        ton = data.get("the-open-network", {})
        rates["ton_usd"] = ton.get("usd")
        # USD→TJS: USDT pair
        tether = data.get("tether", {})
        rates["usd_tjs"] = tether.get("tjs")
    except Exception as e:
        logger.warning("CoinGecko fetch failed: %s", e)
    return rates


def get_rates() -> dict:
    """
    Бармегардонад dict бо ҳамаи курсҳои дилхоҳ:
    {
        "ton_usd": float,    # 1 TON = ? USD
        "usd_tjs": float,    # 1 USD = ? TJS
        "ton_tjs": float,    # 1 TON = ? TJS
        "manual_ton_tjs": bool,
        "manual_ton_usd": bool,
        "manual_usd_tjs": bool,
    }
    """
    from app.models import Settings

    # Live rates (з cache)
    now = time.time()
    if not _cache["data"] or (now - _cache["ts"]) > CACHE_TTL:
        _cache["data"] = _fetch_live_rates()
        _cache["ts"] = now
    live = _cache["data"]

    # Settings overrides
    use_man_ton_usd = Settings.get_bool("use_manual_ton_usd")
    man_ton_usd = Settings.get_float("manual_ton_usd", 5.5)

    use_man_usd_tjs = Settings.get_bool("use_manual_usd_tjs")
    man_usd_tjs = Settings.get_float("manual_usd_tjs", 10.9)

    use_man_ton_tjs = Settings.get_bool("use_manual_ton_tjs")
    man_ton_tjs = Settings.get_float("manual_ton_tjs", 52.0)

    # Resolve final rates
    ton_usd = man_ton_usd if use_man_ton_usd else (live.get("ton_usd") or man_ton_usd)
    usd_tjs = man_usd_tjs if use_man_usd_tjs else (live.get("usd_tjs") or man_usd_tjs)

    if use_man_ton_tjs:
        ton_tjs = man_ton_tjs
    else:
        # Computed: 1 TON = ton_usd × usd_tjs TJS
        ton_tjs = round(ton_usd * usd_tjs, 4)

    return {
        "ton_usd": round(ton_usd, 4),
        "usd_tjs": round(usd_tjs, 4),
        "ton_tjs": round(ton_tjs, 4),
        "manual_ton_tjs": use_man_ton_tjs,
        "manual_ton_usd": use_man_ton_usd,
        "manual_usd_tjs": use_man_usd_tjs,
        "live_ton_usd": live.get("ton_usd"),
        "live_usd_tjs": live.get("usd_tjs"),
    }


def get_ton_rate_dict() -> dict:
    """Қотани кӯтоҳ: {tjs: x, usd: y}."""
    rates = get_rates()
    return {"tjs": rates["ton_tjs"], "usd": rates["ton_usd"]}


def convert(amount: float, from_currency: str, to_currency: str) -> float:
    """
    Convert amount аз як валюта ба валютаи дигар бо курси феълӣ.
    """
    if from_currency == to_currency:
        return amount

    rates = get_rates()
    # Аввал ба USD табдил мекунем, баъд ба target
    in_usd: float
    if from_currency == "USD":
        in_usd = amount
    elif from_currency == "TON":
        in_usd = amount * rates["ton_usd"]
    elif from_currency == "TJS":
        in_usd = amount / max(rates["usd_tjs"], 0.01)
    else:
        return 0.0

    if to_currency == "USD":
        return round(in_usd, 4)
    if to_currency == "TON":
        return round(in_usd / max(rates["ton_usd"], 0.01), 6)
    if to_currency == "TJS":
        return round(in_usd * rates["usd_tjs"], 2)
    return 0.0


def invalidate_cache() -> None:
    _cache["data"] = None
    _cache["ts"] = 0
