"""TGS / Lottie download service.

TGS = gzip(Lottie JSON). Telegram sticker animation format.
Барои дар browser намоиш додан, мо ба `.json` decompresss мекунем.
"""
import gzip
import json
import logging
import uuid
from pathlib import Path
from typing import Optional

import requests
from flask import current_app

logger = logging.getLogger(__name__)


def download_animation(url: str) -> Optional[str]:
    """
    .tgs ё .json-ро download мекунад → дар static/uploads/lottie/-да .json нигоҳ медорад.

    Returns: relative URL (масалан '/static/uploads/lottie/abc.json') ё None
    """
    if not url:
        return None

    upload_dir: Path = current_app.config["UPLOAD_FOLDER"] / "lottie"
    upload_dir.mkdir(parents=True, exist_ok=True)

    try:
        resp = requests.get(url, timeout=10, stream=True)
        resp.raise_for_status()
        raw = resp.content
    except requests.RequestException as e:
        logger.warning("Animation download failed: %s", e)
        return None

    # Detect format: TGS (gzipped) ё JSON
    content: Optional[bytes] = None
    if raw[:2] == b"\x1f\x8b":  # gzip magic
        try:
            content = gzip.decompress(raw)
        except OSError as e:
            logger.warning("TGS decompress failed: %s", e)
            return None
    else:
        # Probably plain JSON
        content = raw

    # Validate JSON
    try:
        json.loads(content)
    except (ValueError, TypeError):
        logger.warning("Animation: invalid JSON")
        return None

    name = f"{uuid.uuid4().hex}.json"
    path = upload_dir / name
    path.write_bytes(content)

    return f"/static/uploads/lottie/{name}"
