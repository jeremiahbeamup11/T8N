"""Change detector: perceptual-hash dedupe of captured frames.

Run standalone: `python -m t8n.diff <image1> <image2>` — prints hash distance.
"""

from __future__ import annotations

import sys
from pathlib import Path

import imagehash
from PIL import Image


class ChangeDetector:
    """Tracks the phash of the last *processed* frame per window identity.

    A frame counts as changed when its phash distance from the last processed
    frame meets the threshold, or when the (app, window) identity changes.
    """

    def __init__(self, threshold: int = 6) -> None:
        self.threshold = threshold
        self._last_hash: imagehash.ImageHash | None = None
        self._last_identity: str | None = None

    def is_changed(self, image_path: Path, identity: str = "") -> bool:
        """True if this frame should be processed; updates state only then."""
        try:
            with Image.open(image_path) as img:
                current = imagehash.phash(img)
        except OSError:
            return False  # unreadable frame: fail quiet, treat as no change

        if (
            self._last_hash is not None
            and identity == self._last_identity
            and (current - self._last_hash) < self.threshold
        ):
            return False

        self._last_hash = current
        self._last_identity = identity
        return True


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python -m t8n.diff <image1> <image2>", file=sys.stderr)
        return 2
    a, b = Path(sys.argv[1]), Path(sys.argv[2])
    with Image.open(a) as ia, Image.open(b) as ib:
        dist = imagehash.phash(ia) - imagehash.phash(ib)
    print(f"phash distance: {dist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
