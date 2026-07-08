"""Command-line entry point: `t8n run|stop|report`."""

from __future__ import annotations

import sys

from t8n import __version__

USAGE = """\
t8n {__version__} — macOS proactive mistake-prevention agent

usage: t8n <command>

commands:
  run      start the capture loop
  stop     stop a running capture loop
  report   print metrics summary
"""


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args or args[0] in ("-h", "--help"):
        print(USAGE.format(__version__=__version__))
        return 0

    command = args[0]
    if command == "run":
        from t8n.app import run as app_run

        return app_run()
    if command == "stop":
        from t8n.app import stop as app_stop

        return app_stop()
    if command == "report":
        from t8n.metrics import report

        return report()

    print(f"t8n: unknown command {command!r}", file=sys.stderr)
    print(USAGE.format(__version__=__version__), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
