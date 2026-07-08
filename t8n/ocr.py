"""OCR + context stage: macOS Vision text recognition and rolling window buffer.

Run standalone: `python -m t8n.ocr <image>` — prints recognized text.
Guardrail: OCR text is returned to the pipeline, never written to logs.
"""

from __future__ import annotations

import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path

import Quartz
import Vision
from Foundation import NSURL


def ocr_image(path: Path) -> str | None:
    """Recognize text in an image via VNRecognizeTextRequest.

    Returns the text as one line per recognized region, top-to-bottom.
    None on any failure (fail quiet).
    """
    try:
        url = NSURL.fileURLWithPath_(str(path))
        source = Quartz.CGImageSourceCreateWithURL(url, None)
        if source is None:
            return None
        cg_image = Quartz.CGImageSourceCreateImageAtIndex(source, 0, None)
        if cg_image is None:
            return None

        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        request.setUsesLanguageCorrection_(True)

        handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
        success, _error = handler.performRequests_error_([request], None)
        if not success:
            return None

        lines: list[str] = []
        for observation in request.results() or []:
            candidates = observation.topCandidates_(1)
            if candidates and len(candidates):
                lines.append(str(candidates[0].string()))
        return "\n".join(lines)
    except Exception:
        return None


@dataclass(frozen=True)
class WindowVisit:
    timestamp: float
    app_name: str
    window_title: str


class ContextBuffer:
    """Rolling buffer of the last N distinct window visits.

    An entry is appended only when (app, title) differs from the most recent
    entry — otherwise a static window would flood out the history.
    """

    def __init__(self, maxlen: int = 10) -> None:
        self._buffer: deque[WindowVisit] = deque(maxlen=maxlen)

    def observe(self, app_name: str, window_title: str, timestamp: float | None = None) -> None:
        if self._buffer:
            last = self._buffer[-1]
            if last.app_name == app_name and last.window_title == window_title:
                return
        self._buffer.append(
            WindowVisit(
                timestamp=time.time() if timestamp is None else timestamp,
                app_name=app_name,
                window_title=window_title,
            )
        )

    def entries(self) -> list[WindowVisit]:
        """Oldest-first list of visits."""
        return list(self._buffer)

    def render(self) -> str:
        """Human/LLM-readable summary, oldest first, for the escalation prompt."""
        return "\n".join(
            f"{time.strftime('%H:%M:%S', time.localtime(v.timestamp))} "
            f"{v.app_name} — {v.window_title or '(untitled)'}"
            for v in self._buffer
        )


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python -m t8n.ocr <image>", file=sys.stderr)
        return 2
    text = ocr_image(Path(sys.argv[1]))
    if text is None:
        print("OCR failed", file=sys.stderr)
        return 1
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
