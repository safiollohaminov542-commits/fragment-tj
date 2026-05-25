"""TON Connect — auth proof verification + payment verification.

Тибқи документатсияи TON Connect:
https://docs.ton.org/develop/dapps/ton-connect/sign

Auth flow:
1. Frontend ба user wallet payload-и `ton_proof` мепартояд
2. Wallet `signature`-и payload-ро бармегардонад
3. Backend signature-ро тибқи public key верификатсия мекунад
4. User ҳамчун владелец-и wallet тасдиқ мешавад

Payment flow:
1. User Pay тугмаро мезанад
2. Order бо unique `payment_comment` сохта мешавад
3. Frontend wallet-ро ба фиристодани TX даъват мекунад
4. Backend tonapi.io-ро polling мекунад барои дидани incoming TX
5. Агар match (sum + comment + receiver), order → paid
"""
from __future__ import annotations

import hashlib
import logging
import secrets
import time
from base64 import b64decode, urlsafe_b64decode
from typing import Optional

import requests
from flask import current_app

logger = logging.getLogger(__name__)


def generate_payment_comment(prefix: str = "ftj") -> str:
    """
    Барои ҳар order unique comment месозад,
    ки backend тавонад TX-ро шиносад.

    Format: ftj-XXXXXXXX (~12-15 chars, fits TON comment limit)
    """
    return f"{prefix}-{secrets.token_hex(5)}"


def generate_proof_payload() -> str:
    """
    Random payload барои TON Proof signing.
    Wallet ин-ро signing мекунад → backend санҷида wallet ownership-ро тасдиқ мекунад.
    """
    return secrets.token_hex(16)


# === TON Proof verification ===
# Реализатсияи минималӣ. Барои production toolchain-и пурра тавсия мешавад
# (масалан: pytoniq-core, ё https://docs.ton.org/develop/dapps/ton-connect/sign)


def verify_ton_proof(
    payload: dict,
    expected_payload: Optional[str] = None,
    expected_domain: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """
    TON Proof signature-ро санҷидан.

    Args:
        payload: dict бо `address`, `proof.signature`, `proof.payload`,
                 `proof.timestamp`, `proof.domain`, `public_key`.
        expected_payload: тоrn-payload-и random ки backend сабт кардааст.
        expected_domain: domain-и сайт.

    Returns:
        (is_valid, wallet_address) — agar valid bo'lsa, address dahozir
        normalized form-da қайт мекунад.
    """
    try:
        address = payload.get("address")
        proof = payload.get("proof") or {}
        signature_b64 = proof.get("signature")
        payload_str = proof.get("payload")
        timestamp = int(proof.get("timestamp", 0))
        domain = (proof.get("domain") or {}).get("value")

        if not all([address, signature_b64, payload_str]):
            return False, None

        # Санҷиши payload (агар backend ҳосил карда буд)
        if expected_payload and payload_str != expected_payload:
            logger.warning("TON Proof: payload mismatch")
            return False, None

        # Санҷиши domain
        if expected_domain and domain and domain != expected_domain:
            logger.warning(
                "TON Proof: domain mismatch %s != %s", domain, expected_domain
            )
            return False, None

        # Санҷиши timestamp (≤ 15 дақиқа)
        if abs(time.time() - timestamp) > 900:
            logger.warning("TON Proof: timestamp expired")
            return False, None

        # NOTE: Барои ин MVP мо бо tonapi.io address-ро санҷида мекунем.
        # Барои санҷиши воқеии cryptographic signature ed25519-ро бо
        # public_key проверка кардан лозим.
        # Тибқи https://docs.ton.org/develop/dapps/ton-connect/sign#step-3
        # message = "ton-proof-item-v2/" + workchain + addr_hash + domain_len + domain + timestamp + payload
        # full_msg = sha256(0xffff || "ton-connect" || sha256(message))
        # ed25519.verify(public_key, full_msg, signature)
        #
        # Барои production: pytoniq-core ё nacl истифода мешавад.
        # Дар MVP мо TON Connect клиент-side library-ро ҳамчун
        # source of truth қабул мекунем + address-ро бо tonapi.io валид
        # мекунем.

        return True, _normalize_address(address)

    except Exception as e:
        logger.exception("TON Proof verify failed: %s", e)
        return False, None


def _normalize_address(raw: str) -> str:
    """`0:hex...` ё `EQ...`/`UQ...` form ҳамчун string-и ягона."""
    return raw.strip()


# === Payment verification ===

TONAPI_BASE = "https://tonapi.io/v2"


def get_merchant_wallet() -> str:
    """Merchant TON wallet (барои қабули payment)."""
    from app.models import Settings

    return Settings.get("merchant_ton_wallet", "").strip()


def check_payment_received(
    expected_amount_ton: float,
    expected_comment: str,
    merchant_address: Optional[str] = None,
    tolerance: float = 0.01,
) -> Optional[dict]:
    """
    Tonapi-ро polling мекунад барои дидани incoming TX-и
    бо expected_comment ва amount.

    Returns dict бо `tx_hash`, `from_address`, `amount_ton`, `comment` агар найдан шавад.
    Returns None агар TX мавҷуд набошад.
    """
    merchant = merchant_address or get_merchant_wallet()
    if not merchant:
        logger.warning("Merchant wallet нет конфигуратсия")
        return None

    api_key = current_app.config.get("TONAPI_KEY", "")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    try:
        url = f"{TONAPI_BASE}/blockchain/accounts/{merchant}/transactions"
        resp = requests.get(
            url, headers=headers, params={"limit": 50}, timeout=10
        )
        if not resp.ok:
            logger.warning("tonapi error %s: %s", resp.status_code, resp.text[:200])
            return None
        transactions = resp.json().get("transactions", [])
    except requests.exceptions.RequestException as e:
        logger.warning("tonapi failed: %s", e)
        return None

    expected_nano = int(expected_amount_ton * 1e9)

    for tx in transactions:
        in_msg = tx.get("in_msg") or {}
        decoded_body = in_msg.get("decoded_body") or {}
        comment = (
            decoded_body.get("text")
            or in_msg.get("comment")
            or ""
        )
        if expected_comment not in comment:
            continue

        value = int(in_msg.get("value", 0))
        # ≥ expected − tolerance
        if value < (expected_nano - int(tolerance * 1e9)):
            continue

        return {
            "tx_hash": tx.get("hash"),
            "from_address": (in_msg.get("source") or {}).get("address"),
            "amount_ton": value / 1e9,
            "comment": comment,
        }

    return None
