"""ChangeDetector: identical frames drop, different frames pass."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from t8n.diff import ChangeDetector


def _make_frame(path: Path, text_lines: list[str]) -> Path:
    img = Image.new("RGB", (800, 600), "white")
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(text_lines):
        draw.text((40, 40 + i * 30), line, fill="black")
    img.save(path)
    return path


def test_first_frame_is_changed(tmp_path: Path) -> None:
    frame = _make_frame(tmp_path / "a.png", ["hello"])
    det = ChangeDetector(threshold=6)
    assert det.is_changed(frame, "app|win")


def test_identical_frame_is_dropped(tmp_path: Path) -> None:
    a = _make_frame(tmp_path / "a.png", ["settings page", "api key: sk-123"])
    b = _make_frame(tmp_path / "b.png", ["settings page", "api key: sk-123"])
    det = ChangeDetector(threshold=6)
    assert det.is_changed(a, "app|win")
    assert not det.is_changed(b, "app|win")


def test_very_different_frame_passes(tmp_path: Path) -> None:
    a = _make_frame(tmp_path / "a.png", ["settings page"] * 3)
    b = Image.new("RGB", (800, 600), "black")
    draw = ImageDraw.Draw(b)
    for i in range(0, 800, 40):
        draw.line([(i, 0), (i, 600)], fill="white", width=8)
    b_path = tmp_path / "b.png"
    b.save(b_path)
    det = ChangeDetector(threshold=6)
    assert det.is_changed(a, "app|win")
    assert det.is_changed(b_path, "app|win")


def test_identity_change_forces_processing(tmp_path: Path) -> None:
    a = _make_frame(tmp_path / "a.png", ["same content"])
    b = _make_frame(tmp_path / "b.png", ["same content"])
    det = ChangeDetector(threshold=6)
    assert det.is_changed(a, "Safari|Stripe dashboard")
    assert det.is_changed(b, "Terminal|vim .env")


def test_unreadable_frame_is_dropped(tmp_path: Path) -> None:
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not a png")
    det = ChangeDetector(threshold=6)
    assert not det.is_changed(bad, "app|win")
