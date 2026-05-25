"""Auto-parser барои саҳифаҳои fragment.com.

Вазифа: аз URL ба монанди https://fragment.com/gift/xxxxx
автомат title, image, TON price ва collection-ро гирифтан.

Стратегия — бисёрқабата:
1. Аввал Open Graph meta-tags-ро месанҷад (og:title, og:image, og:description)
2. Сипас class-based selectors (Fragment HTML structure)
3. Барои narx — regex-и универсалӣ ("X TON", "X.YY TON")

Note: Fragment.com метавонад anti-bot protection дошта бошад.
Барои production бо headless browser (Playwright) истифода шавад.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, asdict
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

REQUEST_TIMEOUT = 10
PRICE_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:TON|💎|тон)", re.IGNORECASE
)


@dataclass
class FragmentGiftData:
    """Натиҷаи parsing."""

    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    ton_price: Optional[float] = None
    collection: Optional[str] = None
    rarity: Optional[str] = None
    fragment_url: Optional[str] = None
    raw_html_snippet: Optional[str] = None  # барои debug

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @property
    def is_valid(self) -> bool:
        """Ҳадди ақал title ё image лозим аст."""
        return bool(self.title or self.image_url)


class FragmentParseError(Exception):
    """Хатои parsing — URL-и нодуруст, network, ё структураи нашиносу."""


def _is_valid_fragment_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and "fragment.com" in parsed.netloc
    except Exception:
        return False


def _absolute_url(base: str, url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    if url.startswith("//"):
        return "https:" + url
    if url.startswith(("http://", "https://")):
        return url
    return urljoin(base, url)


def _meta(soup: BeautifulSoup, key: str, attr: str = "property") -> Optional[str]:
    """Ҷустуҷӯи `<meta property="key" content="...">`."""
    tag = soup.find("meta", attrs={attr: key})
    if tag and tag.get("content"):
        return tag["content"].strip()
    # ҳамчун fallback name= санҷида мешавад
    if attr == "property":
        tag = soup.find("meta", attrs={"name": key})
        if tag and tag.get("content"):
            return tag["content"].strip()
    return None


def _extract_price(text: str) -> Optional[float]:
    """`5 TON`, `5.50 TON`, `5,50 TON` ё `5 💎`-ро ёбад."""
    if not text:
        return None
    match = PRICE_RE.search(text)
    if not match:
        return None
    raw = match.group(1).replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def _extract_title_from_html(soup: BeautifulSoup) -> Optional[str]:
    """Title аз h1 ё title element."""
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    title_tag = soup.find("title")
    if title_tag:
        text = title_tag.get_text(strip=True)
        # Fragment одатан "Title – Fragment" ё "Title | Fragment" аст
        for sep in (" – ", " | ", " - "):
            if sep in text:
                return text.split(sep)[0].strip()
        return text
    return None


def _extract_image_from_html(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    """Image аз `<img>` бо class-и hint-и Fragment ё аввалин image."""
    # Fragment selectors (heuristic)
    candidates = soup.select(
        "img[class*='gift'], img[class*='Gift'], "
        "picture img, .tm-product-photo img, .photo img, "
        "main img"
    )
    for img in candidates:
        src = img.get("src") or img.get("data-src")
        if src:
            return _absolute_url(base_url, src)
    # Fallback: ҳама `<img>`
    img = soup.find("img")
    if img:
        src = img.get("src") or img.get("data-src")
        if src:
            return _absolute_url(base_url, src)
    return None


def _extract_price_from_html(soup: BeautifulSoup) -> Optional[float]:
    """TON price аз HTML."""
    # Бо class-ҳои маъмулии Fragment
    for selector in [
        "[class*='ton-amount']",
        "[class*='Price']",
        "[class*='price']",
        ".tm-value",
        ".value",
    ]:
        for el in soup.select(selector):
            price = _extract_price(el.get_text(" ", strip=True))
            if price is not None:
                return price

    # Дар ҳама cas-ҳои дигар — full text-ро search мекунем
    body_text = soup.get_text(" ", strip=True)
    return _extract_price(body_text)


def _extract_collection(soup: BeautifulSoup) -> Optional[str]:
    """Collection / category."""
    # Breadcrumbs ё subtitle
    for selector in [
        "[class*='breadcrumb'] a",
        "[class*='Breadcrumb'] a",
        "[class*='collection']",
        "[class*='Collection']",
        ".tm-section-header",
    ]:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(strip=True)
            if text and len(text) < 80:
                return text
    return None


def _extract_rarity(soup: BeautifulSoup, full_text: str) -> Optional[str]:
    """Rarity — ҷустуҷӯи калимаҳои маъмул."""
    rarity_keywords = [
        "Legendary", "Epic", "Rare", "Common", "Mythic", "Unique",
    ]
    for kw in rarity_keywords:
        if re.search(rf"\b{kw}\b", full_text, re.IGNORECASE):
            return kw
    return None


def fetch_html(url: str, timeout: int = REQUEST_TIMEOUT) -> str:
    """Ҳомил кардани HTML аз URL."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()
    return resp.text


def parse_fragment_url(url: str) -> FragmentGiftData:
    """
    URL-и Fragment-ро таҳлил ва маълумоти gift-ро бармегардонад.

    Raises:
        FragmentParseError: агар URL нодуруст ё request fail.
    """
    url = (url or "").strip()
    if not _is_valid_fragment_url(url):
        raise FragmentParseError(
            "URL бояд аз fragment.com бошад (масалан https://fragment.com/gift/...)"
        )

    try:
        html = fetch_html(url)
    except requests.exceptions.RequestException as e:
        logger.warning("Fragment fetch failed: %s", e)
        raise FragmentParseError(f"Сахифа дастрас нашуд: {e}") from e

    soup = BeautifulSoup(html, "html.parser")

    data = FragmentGiftData(fragment_url=url)

    # 1. Open Graph meta tags
    data.title = _meta(soup, "og:title")
    data.description = _meta(soup, "og:description")
    og_image = _meta(soup, "og:image")
    if og_image:
        data.image_url = _absolute_url(url, og_image)

    # 2. HTML fallback
    if not data.title:
        data.title = _extract_title_from_html(soup)
    if not data.image_url:
        data.image_url = _extract_image_from_html(soup, url)

    # 3. Price — ҳамеша аз HTML, чун og: price надорад
    data.ton_price = _extract_price_from_html(soup)

    # 4. Collection ва rarity
    data.collection = _extract_collection(soup)
    full_text = soup.get_text(" ", strip=True)
    data.rarity = _extract_rarity(soup, full_text)

    if not data.is_valid:
        raise FragmentParseError(
            "Маълумот пайдо нашуд. Эҳтимол Fragment структураи сахифаро тағйир додааст ё anti-bot."
        )

    logger.info("Fragment parsed: %s", data.title)
    return data
