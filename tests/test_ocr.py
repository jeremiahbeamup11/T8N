"""M1 acceptance: OCR extracts key strings from the settings fixture; buffer holds 10."""

from __future__ import annotations

from pathlib import Path

import pytest

from t8n.ocr import ContextBuffer, ocr_image

FIXTURE = Path(__file__).parent / "fixtures" / "stripe_settings.png"

KEY_STRINGS = [
    "Webhooks",
    "Endpoint URL",
    "https://api.example.com/hooks/payments",
    "Signing secret",
    "API keys",
    "sk_live_51NxampleKey",
    "Delete endpoint",
]


@pytest.fixture(scope="module")
def fixture_text() -> str:
    if not FIXTURE.exists():
        pytest.skip("run tests/fixtures/make_fixtures.py first")
    text = ocr_image(FIXTURE)
    assert text is not None, "OCR returned None on a valid fixture"
    return text


@pytest.mark.parametrize("expected", KEY_STRINGS)
def test_ocr_contains_key_string(fixture_text: str, expected: str) -> None:
    assert expected.lower() in fixture_text.lower()


def test_ocr_missing_file_fails_quiet() -> None:
    assert ocr_image(Path("/nonexistent/nope.png")) is None


def test_ocr_corrupt_file_fails_quiet(tmp_path: Path) -> None:
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"definitely not an image")
    assert ocr_image(bad) is None


def test_buffer_keeps_last_10_distinct_windows() -> None:
    buf = ContextBuffer(maxlen=10)
    for i in range(12):
        buf.observe(f"App{i}", f"Window {i}", timestamp=1000.0 + i)
    entries = buf.entries()
    assert len(entries) == 10
    assert entries[0].app_name == "App2"  # two oldest evicted
    assert entries[-1].app_name == "App11"


def test_buffer_dedupes_consecutive_same_window() -> None:
    buf = ContextBuffer(maxlen=10)
    for _ in range(5):
        buf.observe("Safari", "Stripe — Webhooks", timestamp=1000.0)
    buf.observe("Terminal", "vim .env", timestamp=1001.0)
    buf.observe("Safari", "Stripe — Webhooks", timestamp=1002.0)  # revisit: new entry
    assert len(buf.entries()) == 3


def test_buffer_render_is_oldest_first() -> None:
    buf = ContextBuffer(maxlen=10)
    buf.observe("Safari", "Stripe — Webhooks", timestamp=1000.0)
    buf.observe("Code", "config.yaml — myrepo", timestamp=1060.0)
    rendered = buf.render()
    assert rendered.index("Stripe") < rendered.index("config.yaml")
