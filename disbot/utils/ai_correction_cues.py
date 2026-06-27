"""Heuristic: does a reply to one of the bot's AI answers read as a *correction*?

Used by ``cogs/ai_review_cog.py`` to decide whether a member's reply to a bot
AI answer should be logged as a correction (the owner's "react AND reply"
detection). Deliberately conservative — a follow-up question or a thanks is not
a correction. Pure, stdlib-only, unit-tested (no Discord, no DB).
"""

from __future__ import annotations

import re

# Tokens / phrases that signal the user is telling the bot it was wrong. Matched
# case-insensitively against the stripped reply. Anchored to word boundaries so
# a leading "no" matches "no, it's X" but not "nobody", and "actually" matches
# but "factually" does not.
_CORRECTION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"^\s*no+\b",  # "no", "nooo it's..."
        r"^\s*nope\b",
        r"^\s*nah\b",
        r"\bthat'?s\s+(?:not|wrong|incorrect|false)\b",
        r"\b(?:that'?s|this\s+is|you'?re|that\s+is)\s+wrong\b",
        r"\bincorrect\b",
        r"\bnot\s+(?:true|correct|right|quite)\b",
        r"\bwrong\b",
        r"\bfalse\b",
        r"\bactually\b",  # "actually it's X"
        r"\bmistake\b",
        r"\byou\s+(?:mean|meant)\b",
        r"\bshould\s+(?:be|have\s+been)\b",
        r"\bisn'?t\s+\w+",  # "isn't right", "isn't X"
        r"\bdoesn'?t\s+\w+",
    )
)


def looks_like_correction(text: str | None) -> bool:
    """True if *text* reads like a user correcting the bot's answer.

    Conservative by design: only fires on explicit negation / correction cues,
    so ordinary follow-ups and thanks are not logged as corrections. The caller
    has already established that *text* is a reply to one of the bot's AI
    answers, so this only needs to separate "you got it wrong" from "tell me
    more".
    """
    if not text:
        return False
    stripped = text.strip()
    if not stripped:
        return False
    return any(pattern.search(stripped) for pattern in _CORRECTION_PATTERNS)


__all__ = ["looks_like_correction"]
