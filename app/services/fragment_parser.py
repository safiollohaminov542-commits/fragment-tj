"""Fragment.com parser — auto-import gift metadata.

Стратегия:
1. Аввал Playwright (агар installed) — чун Fragment SPA-аст ва бо JS render мешавад.
2. Fallback: requests + BeautifulSoup (мумкин аст партия пок гирад agar Fragment
   server-side render кунад).

Барои инсталл:
    pip install playwright
    playwright install chromium
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class GiftAttribute:
    name: Optional[str] = None
    rarity: Optional[float] = None  # percentage (e.g. 2.0 = 2%)


@dataclass
class FragmentGiftData:
    title: Optional[str] = None
    collection: Optional[str] = None
    gift_number: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    animation_url: Optional[str] = None  # link to .tgs ё .json
    background_color: Optional[str] = None

    ton_price: Optional[float] = None
    fragment_status: Optional[str] = None  # "for_sale" | "auction"
    fragment_owner: Optional[str] = None

    model: GiftAttribute = field(default_factory=GiftAttribute)
    backdrop: GiftAttribute = field(default_factory=GiftAttribute)
    symbol: GiftAttribute = field(default_factory=GiftAttribute)

    issued_number: Optional[int] = None
    issued_total: Optional[int] = None

    fragment_url: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @property
    def is_valid(self) -> bool:
        return bool(self.title or self.image_url)


class FragmentParseError(Exception):
    pass


# ============================================================================
# URL VALIDATION
# ============================================================================

def _is_valid_fragment_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and "fragment.com" in parsed.netloc
    except Exception:
        return False


# ============================================================================
# RAW HTML extraction helpers
# ============================================================================

PRICE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:TON|💎|тон)", re.IGNORECASE)
PERCENT_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
ISSUED_RE = re.compile(r"(\d[\d\s,]*)\s*of\s*(\d[\d\s,]*)", re.IGNORECASE)


def _meta(soup: BeautifulSoup, key: str, attr: str = "property") -> Optional[str]:
    tag = soup.find("meta", attrs={attr: key})
    if tag and tag.get("content"):
        return tag["content"].strip()
    if attr == "property":
        tag = soup.find("meta", attrs={"name": key})
        if tag and tag.get("content"):
            return tag["content"].strip()
    return None


def _absolute_url(base: str, url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    from urllib.parse import urljoin
    if url.startswith("//"):
        return "https:" + url
    if url.startswith(("http://", "https://")):
        return url
    return urljoin(base, url)


def _parse_int(text: str) -> Optional[int]:
    if not text:
        return None
    cleaned = re.sub(r"[\s,]", "", text)
    if cleaned.isdigit():
        return int(cleaned)
    m = re.search(r"\d+", cleaned)
    return int(m.group()) if m else None


def _parse_float(text: str) -> Optional[float]:
    if not text:
        return None
    m = re.search(r"\d+(?:[.,]\d+)?", text)
    if not m:
        return None
    try:
        return float(m.group().replace(",", "."))
    except ValueError:
        return None


# ============================================================================
# Strategy 1: Playwright (когда установлен)
# ============================================================================

def _try_playwright(url: str) -> Optional[str]:
    """HTML-и render шуда бо Playwright. Бармегардонад None агар Playwright нест."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.info("Playwright нест — fallback ба requests")
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=USER_AGENT, locale="en-US")
            page = context.new_page()
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=15000)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        logger.warning("Playwright failed: %s", e)
        return None


# ============================================================================
# Strategy 2: requests fallback
# ============================================================================

def _fetch_with_requests(url: str) -> str:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
    resp.raise_for_status()
    return resp.text


# ============================================================================
# HTML → FragmentGiftData parser
# ============================================================================

def _parse_html(html: str, url: str) -> FragmentGiftData:
    soup = BeautifulSoup(html, "html.parser")
    data = FragmentGiftData(fragment_url=url)

    # === OG tags ===
    og_title = _meta(soup, "og:title")
    if og_title:
        data.title = og_title.strip()
        # Extract collection + number аз "Vice Cream #150025"
        m = re.match(r"^(.+?)\s+#(\d+)$", og_title)
        if m:
            data.collection = m.group(1).strip()
            data.gift_number = int(m.group(2))

    data.description = _meta(soup, "og:description")
    og_image = _meta(soup, "og:image")
    if og_image:
        data.image_url = _absolute_url(url, og_image)

    # === Animation (TGS / Lottie) — Fragment одатан JSON link дорад ===
    # ҷустуҷӯ дар <script>-ҳо ё <link rel="preload" as="fetch">
    for script in soup.find_all("script"):
        text = script.string or ""
        # Линк ба `.tgs` ё `tgs/lottie.json`
        m = re.search(r'(https?://[^"\'\s]+\.(?:tgs|json))', text)
        if m and ("lottie" in m.group(1).lower() or "tgs" in m.group(1).lower()):
            data.animation_url = m.group(1)
            break

    # Альтернатива: <link rel="preload">
    if not data.animation_url:
        for link in soup.find_all("link", rel=lambda v: v and "preload" in v):
            href = link.get("href", "")
            if href and (".tgs" in href or "lottie" in href):
                data.animation_url = _absolute_url(url, href)
                break

    # === Price ===
    body_text = soup.get_text(" ", strip=True)
    price_m = PRICE_RE.search(body_text)
    if price_m:
        try:
            data.ton_price = float(price_m.group(1).replace(",", "."))
        except ValueError:
            pass

    # === Status ===
    body_lower = body_text.lower()
    if "for sale" in body_lower:
        data.fragment_status = "for_sale"
    elif "auction" in body_lower or "bid" in body_lower:
        data.fragment_status = "auction"

    # === Issued (X of Y) ===
    issued_m = ISSUED_RE.search(body_text)
    if issued_m:
        data.issued_number = _parse_int(issued_m.group(1))
        data.issued_total = _parse_int(issued_m.group(2))

    # === Owner — UQ... ё EQ... address ===
    owner_m = re.search(r"\b(UQ[A-Za-z0-9_-]{40,55}|EQ[A-Za-z0-9_-]{40,55})\b", body_text)
    if owner_m:
        data.fragment_owner = owner_m.group(1)

    # === Attributes (Model / Backdrop / Symbol) ===
    # Fragment одатан structure: <div>Model<span>Ube Cream</span><span>2%</span></div>
    # Селекторҳои гуногунро санҷем
    attr_pairs = _extract_attribute_pairs(soup)
    for label, name, rarity in attr_pairs:
        ll = label.lower()
        attr = GiftAttribute(name=name, rarity=rarity)
        if "model" in ll:
            data.model = attr
        elif "backdrop" in ll or "background" in ll:
            data.backdrop = attr
            # Background color attempt
            data.background_color = _guess_color_from_name(name)
        elif "symbol" in ll or "pattern" in ll:
            data.symbol = attr

    return data


def _extract_attribute_pairs(soup: BeautifulSoup) -> list[tuple[str, str, Optional[float]]]:
    """
    Барои ҳар атрибут (Model, Backdrop, Symbol) кашф мекунад.

    Returns: list of (label, name, rarity_pct)
    """
    pairs = []
    # Стратегия: <table>-ҳо ё <dl>-ҳо
    for table in soup.find_all(["table", "tbody"]):
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(" ", strip=True)
                if label.lower() in ("model", "backdrop", "background", "symbol", "pattern"):
                    name, rarity = _split_value_rarity(value)
                    pairs.append((label, name, rarity))

    # Стратегия: text patterns "Model: Ube Cream 2%"
    if not pairs:
        text = soup.get_text("\n", strip=True)
        for label in ("Model", "Backdrop", "Symbol"):
            m = re.search(rf"{label}\s*\n?\s*([^\n]+?)\s+(\d+(?:[.,]\d+)?)\s*%", text, re.IGNORECASE)
            if m:
                name = m.group(1).strip()
                rarity = float(m.group(2).replace(",", "."))
                pairs.append((label, name, rarity))

    return pairs


def _split_value_rarity(value: str) -> tuple[str, Optional[float]]:
    """`Ube Cream 2%` → ('Ube Cream', 2.0)."""
    m = re.match(r"^(.+?)\s+(\d+(?:[.,]\d+)?)\s*%\s*$", value)
    if m:
        return m.group(1).strip(), float(m.group(2).replace(",", "."))
    return value.strip(), None


# Намунаи ҷустуҷӯи рангҳо аз номҳои Fragment
COLOR_HINTS = {
    "mustard": "#cd9b3a",
    "white": "#f5f5f5",
    "black": "#1a1a1a",
    "gold": "#d4af37",
    "silver": "#c0c0c0",
    "red": "#dc2626",
    "blue": "#2563eb",
    "green": "#16a34a",
    "purple": "#9333ea",
    "pink": "#ec4899",
}


def _guess_color_from_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    nl = name.lower()
    for hint, color in COLOR_HINTS.items():
        if hint in nl:
            return color
    return None


# ============================================================================
# Public API
# ============================================================================

def parse_fragment_url(url: str, *, prefer_playwright: bool = True) -> FragmentGiftData:
    """URL-и Fragment-ро таҳлил ва маълумоти gift-ро бармегардонад."""
    url = (url or "").strip()
    if not _is_valid_fragment_url(url):
        raise FragmentParseError(
            "URL бояд аз fragment.com бошад (мисол: https://fragment.com/gift/...)"
        )

    html: Optional[str] = None
    if prefer_playwright:
        html = _try_playwright(url)

    if not html:
        try:
            html = _fetch_with_requests(url)
        except requests.RequestException as e:
            raise FragmentParseError(f"Сахифа дастрас нашуд: {e}") from e

    if not html:
        raise FragmentParseError("HTML-и пасст ёфта нашуд.")

    data = _parse_html(html, url)
    if not data.is_valid:
        raise FragmentParseError(
            "Маълумот пайдо нашуд. Эҳтимол Fragment структура тағйир дод "
            "ё anti-bot фаъол шуд. Лутфан manual entry истифода кунед."
        )
    logger.info("Fragment parsed: %s", data.title)
    return data
