"""Orchestrator: wires the pipeline stages together. M1 scope: capture → dedupe → OCR.

Run standalone: `python -m t8n.app [duration_seconds]`.
"""

from __future__ import annotations

import sys
import time

from t8n import capture, config
from t8n.diff import ChangeDetector
from t8n.log import get_logger, kv
from t8n.ocr import ContextBuffer, ocr_image

logger = get_logger("app")


def _is_denylisted(info: capture.WindowInfo, cfg: config.Config) -> bool:
    """Privacy guardrail: never capture denylisted apps/domains. Never stubbed."""
    app = info.app_name.lower()
    title = info.window_title.lower()
    for entry in cfg.denylist_apps:
        if entry.lower() == app:
            return True
    for domain in cfg.denylist_domains:
        if domain.lower() in title:
            return True
    return False


def run(duration_seconds: float | None = None) -> int:
    """Capture loop: poll, screenshot, phash-dedupe, OCR survivors. M1 ends here."""
    cfg = config.load()
    if not capture.ensure_permission_or_explain():
        logger.error(kv(event="permission_missing"))
        return 1

    detector = ChangeDetector(threshold=cfg.phash_threshold)
    context = ContextBuffer(maxlen=10)
    stats = {
        "polls": 0,
        "denylisted": 0,
        "capture_failed": 0,
        "unchanged": 0,
        "processed": 0,
        "ocr_failed": 0,
    }
    logger.info(
        kv(event="start", poll_s=cfg.poll_interval_seconds, phash_threshold=cfg.phash_threshold)
    )
    started = time.monotonic()

    try:
        while True:
            cycle_start = time.monotonic()
            try:
                stats["polls"] += 1
                info = capture.get_frontmost_window()
                if info is None or _is_denylisted(info, cfg):
                    stats["denylisted"] += info is not None
                else:
                    context.observe(info.app_name, info.window_title)
                    frame = capture.capture_window(info.window_id)
                    if frame is None:
                        stats["capture_failed"] += 1
                        logger.info(kv(event="capture_failed", app=info.app_name))
                    else:
                        identity = f"{info.app_name}|{info.window_title}"
                        if detector.is_changed(frame, identity):
                            stats["processed"] += 1
                            text = ocr_image(frame)  # text goes downstream, never to logs
                            if text is None:
                                stats["ocr_failed"] += 1
                                logger.info(kv(event="ocr_failed", app=info.app_name))
                            else:
                                logger.info(
                                    kv(
                                        event="frame_processed",
                                        app=info.app_name,
                                        ocr_chars=len(text),
                                        ctx_len=len(context.entries()),
                                    )
                                )
                        else:
                            stats["unchanged"] += 1
                        frame.unlink(missing_ok=True)  # guardrail: no frames kept
            except Exception as exc:  # fail quiet: log one line, keep looping
                logger.error(kv(event="cycle_error", error=type(exc).__name__, detail=str(exc)))

            if duration_seconds is not None and time.monotonic() - started >= duration_seconds:
                break
            elapsed = time.monotonic() - cycle_start
            time.sleep(max(0.0, cfg.poll_interval_seconds - elapsed))
    except KeyboardInterrupt:
        pass

    captured = stats["processed"] + stats["unchanged"]
    drop_pct = (100 * stats["unchanged"] / captured) if captured else 0.0
    summary = kv(event="stop", **stats, dropped_unchanged_pct=f"{drop_pct:.1f}")
    logger.info(summary)
    print(summary)
    return 0


def stop() -> int:
    print("t8n stop: not yet implemented (M6)")
    return 1


def main() -> int:
    duration = float(sys.argv[1]) if len(sys.argv) > 1 else None
    return run(duration)


if __name__ == "__main__":
    raise SystemExit(main())
