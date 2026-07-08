"""Structured one-line logging to ~/.t8n/t8n.log.

Guardrail: log events and metadata only — never screenshot contents or OCR text.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_PATH = Path.home() / ".t8n" / "t8n.log"
_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def get_logger(name: str) -> logging.Logger:
    """Logger writing one-line structured entries to ~/.t8n/t8n.log."""
    logger = logging.getLogger(f"t8n.{name}")
    root = logging.getLogger("t8n")
    if not root.handlers:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(LOG_PATH, maxBytes=5_000_000, backupCount=2)
        handler.setFormatter(logging.Formatter(_FORMAT))
        root.addHandler(handler)
        root.setLevel(logging.INFO)
    return logger


def kv(**fields: object) -> str:
    """Render key=value pairs for one-line structured entries."""
    return " ".join(f"{k}={v}" for k, v in fields.items())
