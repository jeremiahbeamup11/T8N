"""Config loader: ~/.t8n/config.yaml with defaults, created on first run.

The Anthropic key is read from the ANTHROPIC_API_KEY env var first, then from
the (gitignored, chmod 600) config file. It is never written to logs.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

T8N_DIR = Path.home() / ".t8n"
CONFIG_PATH = T8N_DIR / "config.yaml"

DEFAULT_DENYLIST: list[str] = [
    "1Password",
    "Bitwarden",
    "Keychain Access",
    "Messages",
    "Mail",
    "WhatsApp",
    "Signal",
    "Telegram",
]

DEFAULT_CONFIG: dict[str, Any] = {
    "poll_interval_seconds": 3.0,
    "phash_threshold": 6,
    "ollama_model": "llama3.1:8b",
    "ollama_timeout_seconds": 2.0,
    "escalation_model": "claude-sonnet-4-6",
    "escalation_daily_budget": 200,
    "anthropic_api_key": "",  # prefer ANTHROPIC_API_KEY env var
    "denylist_apps": DEFAULT_DENYLIST,
    "denylist_domains": [],
    "ocr_retention_days": 7,
}


@dataclass(frozen=True)
class Config:
    poll_interval_seconds: float
    phash_threshold: int
    ollama_model: str
    ollama_timeout_seconds: float
    escalation_model: str
    escalation_daily_budget: int
    anthropic_api_key: str
    denylist_apps: list[str] = field(default_factory=list)
    denylist_domains: list[str] = field(default_factory=list)
    ocr_retention_days: int = 7


def _write_default_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        yaml.safe_dump(DEFAULT_CONFIG, f, sort_keys=False)
    path.chmod(0o600)  # may hold the API key


def load(path: Path = CONFIG_PATH) -> Config:
    """Load config, creating the file with defaults on first run.

    Unknown keys in the file are ignored; missing keys fall back to defaults.
    """
    if not path.exists():
        _write_default_config(path)

    with path.open() as f:
        raw = yaml.safe_load(f) or {}
    if not isinstance(raw, dict):
        raw = {}

    merged = {**DEFAULT_CONFIG, **{k: v for k, v in raw.items() if k in DEFAULT_CONFIG}}
    env_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if env_key:
        merged["anthropic_api_key"] = env_key

    return Config(
        poll_interval_seconds=float(merged["poll_interval_seconds"]),
        phash_threshold=int(merged["phash_threshold"]),
        ollama_model=str(merged["ollama_model"]),
        ollama_timeout_seconds=float(merged["ollama_timeout_seconds"]),
        escalation_model=str(merged["escalation_model"]),
        escalation_daily_budget=int(merged["escalation_daily_budget"]),
        anthropic_api_key=str(merged["anthropic_api_key"]),
        denylist_apps=list(merged["denylist_apps"]),
        denylist_domains=list(merged["denylist_domains"]),
        ocr_retention_days=int(merged["ocr_retention_days"]),
    )


def main() -> int:
    """`python -m t8n.config` — print the effective config (key redacted)."""
    cfg = load()
    for k, v in vars(cfg).items():
        if k == "anthropic_api_key":
            v = "<set>" if v else "<unset>"
        print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
