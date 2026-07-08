# STATE.md — T8N build state

## Current milestone: M0 — Scaffold + capture

## Task checklist

### M0 — Scaffold + capture
- [x] Repo layout + pyproject.toml + `pip install -e .` entry point (`t8n run`)
- [x] Config loader (`~/.t8n/config.yaml`) with defaults + gitignored key handling
- [x] Screen Recording permission check with clear setup instructions on failure
- [x] Frontmost app + window title via pyobjc
- [x] Windowed screenshot via `screencapture -l <windowID>` at 3s cadence (code done; real capture verified only after permission grant)
- [x] phash change detection with configurable threshold (default 6)
- [x] Structured logging to `~/.t8n/t8n.log`
- [x] Acceptance: 5-min run, >50% frames dropped as unchanged, avg CPU < 5% — PASSED 2026-07-07: 101 polls, 95.0% dropped as unchanged, avg CPU 1.13% (max 9.2% momentary), 0 capture failures. Caveat: screen was mostly idle during the run, not active browsing; drop rate under real browsing will be lower but headroom vs the 50% bar is large. Awaiting user confirmation before starting M1.

### M1 — OCR + context buffer
- [ ] (see PROJECT.md)

### M2 — Stage A heuristics + Ollama filter
- [ ] (see PROJECT.md)

### M3 — Claude escalation
- [ ] (see PROJECT.md)

### M4 — Notifier + cooldowns
- [ ] (see PROJECT.md)

### M5 — Menubar + feedback + metrics
- [ ] (see PROJECT.md)

### M6 — Guardrails + tester packaging
- [ ] (see PROJECT.md)

## Decisions log
- 2026-07-07: Project initialized. Wedge = risky config/settings changes, Mac-only, notification-only. Success metric = ≥70% of rated notifications marked useful by testers.
- 2026-07-07: Native capture (pyobjc + screencapture) chosen over Screenpipe dependency for MVP control; revisit only if capture becomes a time sink.
- 2026-07-07: Local model = llama3.1:8b via Ollama (already on dev machine). Escalation model = claude-sonnet-4-6, BYOK for testers.
- 2026-07-07: Package name is `t8n` (per CLAUDE.md/PROJECT.md), not `sentinel` as one kickoff message suggested — prompts live in `t8n/prompts/`, modules run as `python -m t8n.<module>`.
- 2026-07-07: Dev venv uses Python 3.12 (system default 3.14 has uncertain pyobjc/rumps wheel support). `requires-python >= 3.11` unchanged.
- 2026-07-07: Repo connected to github.com/jeremiahbeamup11/T8N (empty repo, remote `origin`, branch `main`).

## Blockers
- None. (Screen Recording permission was granted mid-session; capture verified working.)

## Proposed scope changes
- None. (Anything here requires explicit user approval before implementation.)

## Notes for next session
- M0 complete pending user sign-off. Next: M1 (Vision-framework OCR + rolling context buffer). Dev venv: `.venv` (Python 3.12), `pip install -e ".[dev]"` already done. Tests: `.venv/bin/pytest tests/`. Lint: `.venv/bin/ruff check t8n/ tests/`.
- Cross-cutting logging helper lives in `t8n/log.py` (not a PROJECT.md stage module — infra, not pipeline). `kv()` renders one-line key=value entries; never log OCR text or screenshot contents.
- Denylist app-skip is already enforced in the M0 loop (`app._is_denylisted`); M6 extends it (domains, incognito, YAML editing UX), never replaces it.
- Repo pushed to github.com/jeremiahbeamup11/T8N (gh credential helper configured via `gh auth setup-git`).