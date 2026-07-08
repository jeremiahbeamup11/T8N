# CLAUDE.md — Operating instructions for Claude Code

You are building T8N, a macOS proactive mistake-prevention agent. Read PROJECT.md (the spec) and STATE.md (current progress) before doing anything.

## Loop protocol

1. Read STATE.md. Identify the current milestone and its next unchecked task.
2. Implement the smallest complete unit of work for that task.
3. Run the milestone's acceptance test (or the closest runnable subset).
4. Update STATE.md: check off completed tasks, record decisions, blockers, and anything the next session must know.
5. Stop at milestone boundaries. Do not start the next milestone without the user confirming the acceptance criteria passed on real hardware (screen capture, notifications, and Ollama can only be fully verified on the Mac itself).

## Hard rules

- Scope is frozen by PROJECT.md. If a task seems to need something outside the spec, write it in STATE.md under "Proposed scope changes" and stop — do not implement it.
- Non-goals in PROJECT.md are rejections, not suggestions. No voice, no overlay UI, no Windows, no cloud storage.
- Fail quiet: any error in the pipeline (OCR failure, Ollama timeout, API error, JSON parse failure) must result in NO notification, a log line, and the loop continuing. T8N being silent is always acceptable; T8N being wrong or crashing is not.
- All LLM outputs are parsed as strict JSON with a schema check. Never regex-scrape prose from a model response.
- Privacy guardrails (denylist, local-only storage, purge) are load-bearing. Never stub them out "temporarily."
- Keep secrets out of the repo. Anthropic key comes from `ANTHROPIC_API_KEY` env or `~/.t8n/config.yaml` (gitignored).

## Code conventions

- Python 3.11+, type hints throughout, `ruff` clean.
- One module per pipeline stage, matching the names in PROJECT.md (capture.py, diff.py, ocr.py, filter_local.py, escalate.py, notify.py, app.py, metrics.py).
- Every stage is independently runnable for testing: `python -m t8n.ocr <image>` etc.
- Fixtures live in `tests/fixtures/` — screenshots are synthetic or of the developer's own test accounts only.
- Log to `~/.t8n/t8n.log`, structured one-line entries, no screenshot contents in logs.

## Prompts are product

The Ollama filter prompt and the Claude escalation prompt live in `t8n/prompts/` as versioned .txt files, not inline strings. When acceptance tests fail on classification quality, iterate the prompt file and record the version + fixture scores in STATE.md. The escalation prompt's bias must always be: silence by default, intervene only when confident and the mistake is costly.

## What done looks like

M6 complete = a technical stranger can clone the repo, run `./install.sh`, follow the README to grant permissions and add their API key, and get their first (correct) warning within a day of normal work — with `t8n report` producing the precision numbers that decide this product's fate.