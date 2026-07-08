"""M2: Stage A heuristics + strict JSON parsing (fast), plus Ollama acceptance (slow).

Acceptance run: pytest tests/test_filter.py -m acceptance
Requires Ollama running with llama3.1:8b; skips cleanly if unreachable.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from t8n import config
from t8n.filter_local import classify, parse_response, stage_a
from t8n.ocr import ocr_image
from tests.fixtures.make_fixtures import FRAMES

FIXTURE_DIR = Path(__file__).parent / "fixtures"

# ---- Stage A (no LLM, fast) ----


def test_stage_a_hits_config_signals() -> None:
    assert stage_a("Safari", "AcmePay — Webhooks", "Endpoint URL")
    assert stage_a("Code", ".env — checkout-service", "DATABASE_URL=...")
    assert stage_a("Safari", "DNS Management", "A record")
    assert stage_a("Code", "deploy.yaml — svc", "replicas: 3")
    assert stage_a("Safari", "", "Revoke token")
    assert stage_a("Safari", "", "sk_live_51NxampleKey")


def test_stage_a_drops_normal_content() -> None:
    assert not stage_a("Safari", "Morning Herald — Marathon draws big crowd", "runners lined up")
    assert not stage_a("Code", "fibonacci.py — algorithms", "def fibonacci(n): return n")
    assert not stage_a("Terminal", "zsh — ~/projects", "$ ls\nfibonacci.py sorting.py")
    assert not stage_a("Calendar", "July 2026 — Week view", "Team standup")


def test_stage_a_word_boundaries() -> None:
    # "prod" must not fire inside ordinary words
    assert not stage_a("Safari", "New products for summer", "our product lineup")
    assert stage_a("Safari", "cluster: prod-us-east", "")


# ---- strict JSON schema (no LLM, fast) ----


def test_parse_valid_response() -> None:
    r = parse_response('{"escalate": true, "context_type": "dashboard", "reason": "API keys"}')
    assert r is not None and r.escalate and r.context_type == "dashboard"


def test_parse_rejects_bad_payloads() -> None:
    assert parse_response("The user is editing config, escalate!") is None  # prose
    assert parse_response('{"escalate": "yes", "context_type": "config", "reason": ""}') is None
    assert parse_response('{"escalate": true, "context_type": "banana", "reason": ""}') is None
    assert parse_response('{"escalate": true, "context_type": "config"}') is None  # missing key
    assert parse_response('["escalate", true]') is None
    assert parse_response("") is None


# ---- M2 acceptance: 20 frames through Stage A + B (requires Ollama) ----


def _ollama_up() -> bool:
    try:
        import ollama

        ollama.Client(timeout=2).list()
        return True
    except Exception:
        return False


@pytest.mark.acceptance
def test_acceptance_20_frames() -> None:
    if not _ollama_up():
        pytest.skip("Ollama not reachable")
    from t8n.filter_local import warm

    cfg = config.load()
    warm(cfg)

    escalated: dict[str, list[str]] = {"config": [], "normal": []}
    dropped: dict[str, list[str]] = {"config": [], "normal": []}
    for frame in FRAMES:
        text = ocr_image(FIXTURE_DIR / f"{frame['name']}.png")
        assert text is not None, f"OCR failed on {frame['name']}"
        result = classify(frame["app"], frame["title"], text, cfg)
        if result is not None and result.escalate:
            escalated[frame["kind"]].append(frame["name"])
        else:
            dropped[frame["kind"]].append(frame["name"])

    print(f"\nconfig escalated ({len(escalated['config'])}/10): {escalated['config']}")
    print(f"config dropped: {dropped['config']}")
    print(f"normal escalated ({len(escalated['normal'])}/10): {escalated['normal']}")
    assert len(escalated["config"]) >= 8, f"only {len(escalated['config'])}/10 config escalated"
    assert len(escalated["normal"]) <= 1, f"{len(escalated['normal'])}/10 normal escalated"
