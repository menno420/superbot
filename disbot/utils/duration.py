"""Human-friendly duration parsing/formatting (``30m`` / ``2h`` / ``7d``).

A small, dependency-free helper shared by any feature that takes a duration from
a user (temp roles today; reusable for timeouts / reminders later). Lives in
``utils`` because it is pure and layer-agnostic (``docs/helper-policy.md``: a
helper needed by services + cogs belongs in ``utils``).
"""

from __future__ import annotations

import re

_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
_TOKEN_RE = re.compile(r"(\d+)([smhdw])")
# The whole (space-stripped) string must be one or more value+unit tokens — so
# stray characters like a leading '-' are rejected rather than silently ignored.
_FULL_RE = re.compile(r"(?:\d+[smhdw])+")

# Sanity cap: a year. Beyond this a "temporary" grant is effectively permanent
# and almost certainly a typo (e.g. a stray digit), so callers reject it.
MAX_DURATION_SECONDS = 365 * 86400


def parse_duration(text: str) -> int | None:
    """Parse a duration string to **total seconds**, or ``None`` if unparseable.

    Accepts compound unit forms (``"2h30m"``, ``"7d"``, ``"90s"``) and a bare
    number, which is read as **minutes** (the common moderation default — Carl's
    ``temp 30`` = 30 minutes). Returns ``None`` for empty / non-duration input and
    for values over :data:`MAX_DURATION_SECONDS`.
    """
    text = text.strip().lower()
    if not text:
        return None
    if text.isdigit():
        total = int(text) * 60
        return total if 0 < total <= MAX_DURATION_SECONDS else None
    compact = text.replace(" ", "")
    if not _FULL_RE.fullmatch(compact):
        return None
    total = sum(
        int(value) * _UNIT_SECONDS[unit] for value, unit in _TOKEN_RE.findall(compact)
    )
    if total <= 0 or total > MAX_DURATION_SECONDS:
        return None
    return total


def format_duration(seconds: int) -> str:
    """Render seconds as a compact human string (``5400`` → ``"1h 30m"``).

    Returns a space-separated duration string using day/hour/minute/second units.
    """
    if seconds <= 0:
        return "0s"
    parts: list[str] = []
    for unit, size in (("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        whole, seconds = divmod(seconds, size)
        if whole:
            parts.append(f"{whole}{unit}")
    return " ".join(parts)


__all__ = ["MAX_DURATION_SECONDS", "format_duration", "parse_duration"]
