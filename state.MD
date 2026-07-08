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
- [ ] Acceptance: 5-min run, >50% frames dropped as unchanged, avg CPU < 5%

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
- Start with M0 task 1. Nothing exists yet.