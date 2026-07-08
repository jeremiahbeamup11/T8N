"""Local filter stage: Stage A keyword heuristics + Stage B Ollama classification.

Run standalone: `python -m t8n.filter_local <image> [app_name] [window_title]`.
Fail quiet: any Stage B error/timeout/parse failure means NO escalation.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import ollama

from t8n import config
from t8n.log import get_logger, kv

logger = get_logger("filter")

FILTER_PROMPT_VERSION = "filter_v1"

# Stage A: if none of these match app+title+OCR text, the frame is dropped
# without any LLM call. Word boundaries keep short tokens from matching inside
# ordinary words ("prod" must not fire on "product").
_STAGE_A_PATTERNS: list[str] = [
    r"\bsettings\b",
    r"\bwebhooks?\b",
    r"\bapi[ _-]?keys?\b",
    r"\bdns\b",
    r"\benvironment\b",
    r"\.env\b",
    r"\bdeploy\w*\b",
    r"\bbilling\b",
    r"\bsubscription\b",
    r"\bdelete\b",
    r"\bdrop\b",
    r"\brevoke\b",
    r"\bregenerate\b",
    r"\brotate\b",
    r"\btokens?\b",
    r"\bsecrets?\b",
    r"\bcredentials?\b",
    r"\bprod\b",
    r"\bproduction\b",
    r"\biam\b",
    r"\bdashboard\b",
    r"\badmin\b",
    r"\bfeature flags?\b",
    r"\bmaintenance mode\b",
    r"\.ya?ml\b",
    r"\.toml\b",
    r"\bsk_live_",
    r"\bwhsec_",
]
_STAGE_A_RE = re.compile("|".join(_STAGE_A_PATTERNS), re.IGNORECASE)

_OCR_TEXT_LIMIT = 1400  # chars sent to the local model; keeps latency under the 2s cap

_VALID_CONTEXT_TYPES = frozenset({"config", "editor_config", "dashboard", "other"})


@dataclass(frozen=True)
class FilterResult:
    escalate: bool
    context_type: str
    reason: str


def stage_a(app_name: str, window_title: str, ocr_text: str) -> bool:
    """True if the frame shows any config-context signal and survives to Stage B."""
    haystack = f"{app_name}\n{window_title}\n{ocr_text}"
    return _STAGE_A_RE.search(haystack) is not None


def load_prompt(version: str = FILTER_PROMPT_VERSION) -> str:
    return (resources.files("t8n.prompts") / f"{version}.txt").read_text()


def parse_response(raw: str) -> FilterResult | None:
    """Strict JSON + schema check. None on any deviation (fail quiet)."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    escalate = data.get("escalate")
    context_type = data.get("context_type")
    reason = data.get("reason")
    if not isinstance(escalate, bool):
        return None
    if context_type not in _VALID_CONTEXT_TYPES:
        return None
    if not isinstance(reason, str):
        return None
    return FilterResult(escalate=escalate, context_type=context_type, reason=reason[:100])


def stage_b(
    app_name: str, window_title: str, ocr_text: str, cfg: config.Config
) -> FilterResult | None:
    """Classify via Ollama. None on timeout/error/bad JSON — caller must not escalate."""
    # .replace, not .format: prompt files contain literal JSON braces
    prompt = (
        load_prompt()
        .replace("{app_name}", app_name)
        .replace("{window_title}", window_title)
        .replace("{ocr_text}", ocr_text[:_OCR_TEXT_LIMIT])
    )
    try:
        client = ollama.Client(timeout=cfg.ollama_timeout_seconds)
        response = client.generate(
            model=cfg.ollama_model,
            prompt=prompt,
            format="json",
            keep_alive="30m",
            options={"temperature": 0, "num_predict": 48},
        )
        raw = response["response"]
    except Exception as exc:
        logger.info(kv(event="stage_b_failed", error=type(exc).__name__))
        return None
    result = parse_response(raw)
    if result is None:
        logger.info(kv(event="stage_b_bad_json", prompt_version=FILTER_PROMPT_VERSION))
    return result


def classify(
    app_name: str, window_title: str, ocr_text: str, cfg: config.Config
) -> FilterResult | None:
    """Full local filter: Stage A gate, then Stage B. None means drop the frame."""
    if not stage_a(app_name, window_title, ocr_text):
        return None
    return stage_b(app_name, window_title, ocr_text, cfg)


def warm(cfg: config.Config) -> bool:
    """Load the model and exercise a full-size prompt eval. Non-fatal.

    A trivial 1-token warm-up loads weights but leaves the first real
    (large-batch) prompt eval slow enough to breach the hard timeout; a
    representative dummy call pays that cost up front instead.
    """
    dummy = (
        load_prompt()
        .replace("{app_name}", "Warmup")
        .replace("{window_title}", "warmup")
        .replace("{ocr_text}", "warmup text " * 200)
    )
    try:
        ollama.Client(timeout=60).generate(
            model=cfg.ollama_model,
            prompt=dummy,
            format="json",
            keep_alive="30m",
            options={"temperature": 0, "num_predict": 48},
        )
        return True
    except Exception as exc:
        logger.info(kv(event="ollama_warm_failed", error=type(exc).__name__))
        return False


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python -m t8n.filter_local <image> [app_name] [window_title]")
        return 2
    from t8n.ocr import ocr_image

    image = Path(sys.argv[1])
    app_name = sys.argv[2] if len(sys.argv) > 2 else ""
    window_title = sys.argv[3] if len(sys.argv) > 3 else ""
    cfg = config.load()

    text = ocr_image(image)
    if text is None:
        print("OCR failed", file=sys.stderr)
        return 1
    passed_a = stage_a(app_name, window_title, text)
    print(f"stage_a: {'pass' if passed_a else 'drop'}")
    if not passed_a:
        return 0
    warm(cfg)
    result = stage_b(app_name, window_title, text, cfg)
    if result is None:
        print("stage_b: failed quiet (no escalation)")
        return 0
    print(f"stage_b: escalate={result.escalate} type={result.context_type} reason={result.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
