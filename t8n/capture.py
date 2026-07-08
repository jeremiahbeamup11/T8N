"""Capture stage: permission check, frontmost window metadata, windowed screenshots.

Run standalone: `python -m t8n.capture` — checks permission and prints one capture.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import Quartz
from AppKit import NSWorkspace

FRAME_DIR = Path("/tmp/t8n")
FRAME_PATH = FRAME_DIR / "frame.png"

PERMISSION_INSTRUCTIONS = """\
T8N needs the Screen Recording permission to watch the active window.

To grant it:
  1. Open System Settings > Privacy & Security > Screen & System Audio Recording.
  2. Click "+", add the terminal app you run `t8n` from (e.g. Terminal, iTerm).
  3. Quit and reopen that terminal app, then run `t8n run` again.

T8N captures the frontmost window only, keeps everything on this machine,
and never records apps on your denylist (~/.t8n/config.yaml).
"""


def has_screen_recording_permission() -> bool:
    """True if this process can capture the screen. Does not prompt."""
    return bool(Quartz.CGPreflightScreenCaptureAccess())


def request_screen_recording_permission() -> bool:
    """Trigger the macOS permission prompt (once); returns current status."""
    return bool(Quartz.CGRequestScreenCaptureAccess())


def ensure_permission_or_explain() -> bool:
    """Check permission; on failure print setup instructions and return False."""
    if has_screen_recording_permission():
        return True
    request_screen_recording_permission()
    print(PERMISSION_INSTRUCTIONS)
    return False


@dataclass(frozen=True)
class WindowInfo:
    app_name: str
    window_title: str
    window_id: int  # kCGWindowNumber, for `screencapture -l`; 0 if not found
    pid: int


def get_frontmost_window() -> WindowInfo | None:
    """Frontmost app name + window title + window id, or None if undetermined.

    Window titles require Screen Recording permission; without it the title
    comes back empty and we still return app name + window id.
    """
    app = NSWorkspace.sharedWorkspace().frontmostApplication()
    if app is None:
        return None
    app_name = str(app.localizedName() or "")
    pid = int(app.processIdentifier())

    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID,
    )
    for w in windows or []:
        if int(w.get("kCGWindowOwnerPID", -1)) != pid:
            continue
        if int(w.get("kCGWindowLayer", 0)) != 0:  # skip menubar/overlay layers
            continue
        return WindowInfo(
            app_name=app_name,
            window_title=str(w.get("kCGWindowName", "") or ""),
            window_id=int(w.get("kCGWindowNumber", 0)),
            pid=pid,
        )
    return WindowInfo(app_name=app_name, window_title="", window_id=0, pid=pid)


def capture_window(window_id: int, dest: Path = FRAME_PATH) -> Path | None:
    """Screenshot one window to `dest`; None on any failure (fail quiet)."""
    if window_id <= 0:
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            ["screencapture", "-x", "-o", "-l", str(window_id), str(dest)],
            capture_output=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not dest.exists() or dest.stat().st_size == 0:
        return None
    return dest


def main() -> int:
    granted = ensure_permission_or_explain()
    info = get_frontmost_window()
    if info is None:
        print("No frontmost window found")
        return 1
    print(f"app: {info.app_name!r}  title: {info.window_title!r}  window_id: {info.window_id}")
    frame = capture_window(info.window_id)
    print(f"screenshot: {frame if frame else 'failed (permission or window gone)'}")
    return 0 if granted and frame else 1


if __name__ == "__main__":
    raise SystemExit(main())
