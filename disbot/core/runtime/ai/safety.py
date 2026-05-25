"""Pre-provider safety checks for AI requests.

These checks run synchronously inside the gateway before any
external call. They are deterministic and cheap; they never depend
on an LLM. A check that fires returns a textual reason; the gateway
short-circuits with a degraded :class:`AIResponse` and never sends
the request.

Checks (composable, ordered):

1. Empty / whitespace-only ``system_prompt`` — guards against
   misconfigured callers that build prompts dynamically.
2. Empty ``payload`` — same.
3. Payload size cap — JSON-serialised size in bytes must stay below
   :data:`MAX_PAYLOAD_BYTES`. Protects against accidental large
   dumps (e.g. an entire guild snapshot pasted in).

Future hooks: more sophisticated prompt-injection heuristics. The
plan defers those until a real abuse signal exists; deterministic
size/empty checks are the conservative baseline.
"""

from __future__ import annotations

import json

from core.runtime.ai.contracts import AIRequest

# Conservative ceiling for the serialised payload size in bytes.
# Setup advisor snapshots run well under 100 KiB; this rejects
# obvious mistakes without blocking legitimate use.
MAX_PAYLOAD_BYTES = 256 * 1024


def precheck(request: AIRequest) -> str | None:
    """Run safety checks; return the first failure reason or ``None``."""
    if not request.system_prompt or not request.system_prompt.strip():
        return "safety: empty system_prompt"
    if not request.payload:
        return "safety: empty payload"
    try:
        size = len(json.dumps(request.payload, default=str).encode("utf-8"))
    except (TypeError, ValueError):
        return "safety: payload is not JSON-serialisable"
    if size > MAX_PAYLOAD_BYTES:
        return f"safety: payload {size}B exceeds {MAX_PAYLOAD_BYTES}B cap"
    return None


# ---------------------------------------------------------------------------
# Prompt-injection containment (M2)
# ---------------------------------------------------------------------------
# Untrusted text (user submissions, channel/category instruction bodies,
# source snippets, strategy memory) must be wrapped before it is folded
# into a prompt so a hostile string like "Ignore previous instructions"
# becomes data the model can describe rather than instructions it
# follows. Official API / source data is also data, not instructions —
# both go through the same wrapper.

_CONTAIN_OPEN = "\n<<<UNTRUSTED_DATA__{kind}__BEGIN>>>\n"
_CONTAIN_CLOSE = "\n<<<UNTRUSTED_DATA__{kind}__END>>>\n"

# Strip control characters that would let untrusted text close the
# delimiter or open a fake system tag. Keep TAB / LF / CR only.
_CONTROL_RE = __import__("re").compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def wrap_untrusted_text(text: str, *, kind: str) -> str:
    """Return ``text`` wrapped in containment delimiters.

    ``kind`` is a short stable label (e.g. ``"user_message"``,
    ``"channel_instruction"``, ``"category_instruction"``,
    ``"source_snippet"``, ``"strategy_text"``) recorded in the
    delimiter for observability.

    The function:

    * strips ASCII control characters so the data cannot smuggle a
      closing delimiter or a fake ``<|im_start|>`` / ``<system>``
      marker;
    * normalises any literal occurrence of the delimiter strings by
      doubling the surrounding angle brackets so the wrapper itself
      cannot be forged.

    The opening/closing delimiters describe a single span; nested
    untrusted regions wrap independently.
    """
    if not isinstance(text, str):
        raise TypeError(f"wrap_untrusted_text expected str, got {type(text).__name__}")
    safe_kind = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in kind)[:32]
    cleaned = _CONTROL_RE.sub("", text)
    # Disarm any literal delimiter substring the attacker might inject.
    cleaned = cleaned.replace("<<<UNTRUSTED_DATA", "<<<<UNTRUSTED_DATA")
    cleaned = cleaned.replace("UNTRUSTED_DATA__", "UNTRUSTED_DATA___")
    return (
        _CONTAIN_OPEN.format(kind=safe_kind)
        + cleaned
        + _CONTAIN_CLOSE.format(kind=safe_kind)
    )


def claims_are_grounded(answer: str, allowed_facts: list[str]) -> bool:
    """Cheap, deterministic grounding check.

    The default rule is conservative: every numeric token in ``answer``
    must appear in at least one of the ``allowed_facts`` strings. This
    catches the common failure mode where AI invents a tower stat or
    round number that wasn't in the retrieved context. The
    btd6_grounding_service (M4) replaces this with a structured
    validator; until then this guard keeps M2's prompt-injection /
    grounding pin tests honest.
    """
    import re as _re

    haystack = " ".join(allowed_facts)
    for token in _re.findall(r"\b\d+(?:\.\d+)?\b", answer):
        if token not in haystack:
            return False
    return True


__all__ = [
    "MAX_PAYLOAD_BYTES",
    "claims_are_grounded",
    "precheck",
    "wrap_untrusted_text",
]
