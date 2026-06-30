"""Question normalization shared by the AI review-log triage + preset layers.

A single, deliberately *conservative* normalizer so two places agree on what
"the same question" means:

* ``scripts/ai_review_triage.py`` uses it to dedupe the exported backlog and to
  derive a stable key for a preset candidate.
* ``services/ai_preset_service`` (the vetted-answer preset layer) uses it to key
  presets and to look one up at answer time.

Exact-normalized equality only — no fuzzy / semantic matching. A preset serves a
vetted answer with **zero model call**, so a false match would confidently serve
the wrong answer; conservative normalization keeps that risk near zero (the cost
is only that a paraphrase needs its own preset, which is acceptable for v1).

Layer: ``utils`` leaf — stdlib only, importable from anywhere.
"""

from __future__ import annotations

import re
import unicodedata

# Discord entity tokens — user/role/channel mentions and custom emoji. Stripped
# because they are noise for *question identity*: the stored review-log question
# keeps the raw bot mention (`<@123> how much cash`) while the runtime sees the
# mention-stripped text, and a preset must key the same either way.
_DISCORD_TOKEN = re.compile(r"<a?:\w+:\d+>|<[@#][!&]?\d+>")
# Collapsible whitespace runs.
_WS = re.compile(r"\s+")
# Surrounding punctuation / symbols to trim (keep inner punctuation intact so
# "0-4-1" or "what's" normalize sensibly).
_EDGE = re.compile(r"^[^0-9a-z]+|[^0-9a-z]+$")


def normalize_question(text: str | None) -> str:
    """Return a stable, case-folded key for *text* (``""`` if empty).

    Steps: strip Discord mention/emoji tokens → Unicode NFKC fold → casefold →
    collapse whitespace → strip leading / trailing punctuation & symbols.
    Deterministic and dependency-free so the triage script and the runtime preset
    lookup derive byte-identical keys whether or not the message was a mention.
    """
    if not text:
        return ""
    without_tokens = _DISCORD_TOKEN.sub(" ", text)
    folded = unicodedata.normalize("NFKC", without_tokens).casefold()
    collapsed = _WS.sub(" ", folded).strip()
    if not collapsed:
        return ""
    return _EDGE.sub("", collapsed)


__all__ = ["normalize_question"]
