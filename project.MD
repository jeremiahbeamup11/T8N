# PROJECT.md — T8N MVP

## What this is

T8N is a macOS background agent that watches the active window, detects when the user is in a **configuration context** (dashboards, settings pages, env files, DNS panels, deploy configs), and proactively warns them — via a native notification — when they are about to make a risky or incorrect change. It is NOT a chatbot. It never speaks unless it has something worth saying.

**The single metric that decides whether this product exists:** of all notifications shown, what percentage does the user rate "correct and worth the interruption"? Target: ≥70%. Everything in this spec serves that metric.

## Wedge scope (do not expand)

- Mac only (Apple Silicon).
- Active window only. No multi-monitor, no background windows.
- One intervention category: **risky config/settings changes** (examples: deleting/rotating an API key that's referenced elsewhere, changing a webhook URL, editing DNS records, toggling prod settings, editing .env values, destructive dashboard actions).
- Text notification only. No voice, no wake word, no overlay UI.
- Distribution: GitHub repo + install script. Target testers are technical builders.

## Explicit non-goals (reject any drift toward these)

- General coding assistance inside the IDE (Cursor/Copilot own that).
- Meeting/call assistance.
- Screen history/search (Screenpipe owns that).
- Windows/Linux support.
- Any cloud storage of screenshots. Escalated frames go to the Anthropic API and are not persisted anywhere remote.

## Architecture

```
[Capture Loop] → [Change Detector] → [OCR + Context] → [Local Filter (Ollama)]
                                                             │ escalate=true
                                                             ▼
                                              [Claude Escalation (Anthropic API)]
                                                             │ intervene=true
                                                             ▼
                                        [Notifier] → [Feedback (menubar)] → [Metrics DB]
```

### 1. Capture Loop (`capture.py`)
- Poll every 3 seconds.
- Get frontmost app name + window title via Quartz (`CGWindowListCopyWindowInfo`) / NSWorkspace (pyobjc).
- Screenshot frontmost window only: `screencapture -x -l <windowID> /tmp/t8n/frame.png`.
- Requires Screen Recording permission — detect missing permission and print clear setup instructions.

### 2. Change Detector (`diff.py`)
- Perceptual hash (imagehash, phash) of each frame.
- If hash distance from last processed frame < threshold (start: 6), skip frame entirely. This is the primary cost/CPU control.

### 3. OCR + Context (`ocr.py`)
- Use the macOS Vision framework (VNRecognizeTextRequest via pyobjc) — local, fast, free. No Tesseract.
- Output: plain text of visible window content.
- Maintain a rolling context buffer: last 10 (timestamp, app, window_title) tuples. This gives the escalation call short-term memory ("user was just in the Stripe webhook settings, now in their editor").

### 4. Local Filter (`filter_local.py`)
- Model: `llama3.1:8b` via Ollama (already installed on the dev machine).
- Two-stage, mirroring the Jarvis dumb-router philosophy:
  - **Stage A (no LLM):** keyword/domain heuristics on app name + window title + OCR text. If none of the config-context signals match (e.g. "settings", "webhook", "API key", "DNS", "environment", ".env", "deploy", "billing", "delete", "revoke", app is a browser on a known dashboard domain, editor with .env/.yaml/.toml open), drop the frame. Expect this to drop >90% of frames.
  - **Stage B (Ollama):** classify the surviving frames. Prompt returns strict JSON:
    ```json
    {"escalate": true|false, "context_type": "config|editor_config|dashboard|other", "reason": "<10 words"}
    ```
- Hard timeout 3.0s (measured floor on base M2 hardware: ~2.4s per uncached llama3.1:8b classification; 2.0s guarantees permanent silence). On timeout or parse failure, do NOT escalate (fail quiet).
- **No stacking:** at most one Stage B classification in flight at any time. If a new frame survives Stage A while a classification is running, drop it — never queue. Frames are disposable; a config screen that matters will still be on screen next poll.

### 5. Claude Escalation (`escalate.py`)
- Model: `claude-sonnet-4-6` via Anthropic API. Input: screenshot (base64 PNG), OCR text, app/window title, rolling context buffer.
- System prompt goal: "You are a mistake-prevention agent. Decide whether the user is about to make a risky or incorrect configuration change. Only intervene when you are confident AND the mistake would be costly. Silence is the default."
- Strict JSON output:
    ```json
    {"intervene": true|false, "confidence": 0.0-1.0, "severity": "low|med|high", "message": "<=200 chars, states WHAT is risky and WHY", "category": "<short tag>"}
    ```
- Notify only if `intervene && confidence >= 0.8 && severity != "low"`.
- The `message` must be specific ("This webhook URL points to localhost — it will fail in prod") — generic warnings are worse than silence.

### 6. Notifier (`notify.py`)
- Native macOS notification (terminal-notifier or rumps). Title: "T8N". Body: the message.
- Cooldowns (hard rules):
  - Max 1 notification per 5 minutes globally.
  - Max 1 notification per (app, category) per 30 minutes.
  - Never notify twice about the same message text in a session.

### 7. Feedback + Menubar (`app.py`, rumps)
- Menubar icon with: last alert text, [👍 Useful] [👎 Wrong/annoying] buttons, pause 1h, quit.
- Every rating is written to the metrics DB. Unrated alerts count against the metric in reporting (shown as unrated, not assumed useful).

### 8. Metrics (`metrics.py`, SQLite at `~/.t8n/t8n.db`)
- Tables: `frames` (count only, daily rollup), `stage_a_pass`, `ollama_escalations`, `api_calls` (tokens, cost estimate), `notifications` (message, severity, ts), `ratings` (notification_id, rating, ts).
- `python -m t8n.report` prints: frames seen, % dropped per stage, notifications shown, precision (👍 / rated), estimated API spend.

## Guardrails (non-negotiable, implement before any tester gets a build)

1. **Privacy denylist:** never OCR, store, or escalate frames when app/window matches: password managers (1Password, Bitwarden, Keychain), banking/finance domains, health portals, Messages/Mail/personal chat apps, anything in incognito/private windows where detectable. Denylist is a user-editable YAML.
2. **Escalation budget:** max 200 Claude API calls/day; when exceeded, log and go silent, show a menubar badge.
3. **All storage local.** Screenshots deleted after processing; only OCR text of ESCALATED frames is kept locally for debugging, auto-purged after 7 days.
4. **Kill switch:** menubar pause + `t8n stop` CLI must halt capture within one poll cycle.

## Stack

Python 3.11+, pyobjc (Quartz, Vision, AppKit), Pillow + imagehash, ollama (python client), anthropic SDK, rumps, terminal-notifier, sqlite3, PyYAML. Single repo, `pip install -e .`, entry point `t8n run`.

## Milestones

Each milestone must end with: code merged, acceptance test passing, STATE.md updated.

### M0 — Scaffold + capture
- Repo layout, pyproject, config file (`~/.t8n/config.yaml`), permission check.
- Capture loop producing frames + app/window metadata at 3s cadence; phash dedupe working.
- **Accept:** run 5 min while browsing; log shows frames captured and >50% dropped as unchanged; CPU < 5% average.

### M1 — OCR + context buffer
- Vision-framework OCR on surviving frames; rolling context buffer.
- **Accept:** open a Stripe-like settings page screenshot fixture; OCR output contains the key visible strings; buffer shows last 10 windows.

### M2 — Stage A heuristics + Ollama filter
- Keyword/domain heuristics; Ollama classification with strict JSON parsing + 3.0s timeout; single-classification-in-flight (no stacking, no queue).
- **Accept:** fixture set of 20 frames (10 config contexts, 10 normal browsing/coding); Stage A+B escalate ≥8 of the config frames and ≤1 of the normal frames. Firing a second Stage-A survivor while a classification is in flight drops the frame with a log line, never queues it.

### M3 — Claude escalation
- API call with image + text + buffer; JSON contract enforced; confidence/severity gating.
- **Accept:** fixture set of 10 risky-config screenshots (hand-made: localhost webhook URL, deleting a live API key, DNS record with obvious typo, prod flag toggle, etc.) and 10 benign-config screenshots; ≥7/10 risky get intervene=true with a specific message; ≤2/10 benign trigger.

### M4 — Notifier + cooldowns
- Native notifications; all three cooldown rules; dedupe.
- **Accept:** scripted test firing 10 interventions in 2 min produces exactly 1 notification.

### M5 — Menubar + feedback + metrics
- rumps app, ratings, SQLite logging, `t8n report`.
- **Accept:** rate two alerts (one up, one down); report shows precision 50% and correct counts.

### M6 — Guardrails + tester packaging
- Denylist, budget cap, purge job, kill switch, install script, README with permission walkthrough, BYOK setup (tester supplies own Anthropic key).
- **Accept:** fresh-machine install via script in <10 min by following README only; 1Password window produces zero log entries.

## Tester protocol (post-M6, not code)

- 10–20 technical users, 2 weeks, BYOK.
- Weekly `t8n report` output collected (text only, no screenshots).
- Decision rule: precision ≥70% and ≥3 alerts/user/week rated useful → keep going. Below that → the judgment engine isn't there; iterate on M3 prompt or kill.