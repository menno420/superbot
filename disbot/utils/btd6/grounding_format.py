"""Shared text-formatting helpers for BTD6 → AI grounding lines.

These helpers turn raw fact bodies into single, length-bounded strings
suitable for the AI instruction stack's untrusted-data envelope. They
were promoted from private helpers in ``services.btd6_context_service``
so the new ``services.btd6_ai_context_service`` facade can share the
exact same sanitisation and provenance rules.

The helpers are:

* :func:`sanitise` — strip control characters, collapse whitespace, cap
  at ``cap`` characters (default 240).
* :func:`relative_time` — render a ``fetched_at`` timestamp as
  ``Ns / Nm / Nh / Nd ago``.
* :func:`render_grounding_line` — compose ``<body> (source: <name>,
  fetched <Nm ago>)`` and truncate the body BEFORE the provenance
  suffix so source / fetched is never cut off.

All helpers are sync, format-only, and never perform I/O.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

DEFAULT_CAP = 240


def sanitise(value: object, *, cap: int = DEFAULT_CAP) -> str:
    """Strip control chars, collapse whitespace, cap at ``cap`` chars.

    Non-strings return an empty string. ``cap`` is a hard upper bound;
    the helper does not pre-reserve provenance space — use
    :func:`render_grounding_line` when both body and provenance need to
    fit inside a single budget.
    """
    if not isinstance(value, str):
        return ""
    cleaned = _CONTROL_CHARS.sub("", value)
    cleaned = " ".join(cleaned.split())
    if cap > 0 and len(cleaned) > cap:
        cleaned = cleaned[: cap - 1] + "…"
    return cleaned


def relative_time(fetched_at: datetime | None) -> str:
    """Render a ``fetched_at`` timestamp as ``Ns / Nm / Nh / Nd ago``.

    Naive datetimes are interpreted as UTC. Future timestamps render as
    ``"just now"`` rather than a negative duration.
    """
    if not isinstance(fetched_at, datetime):
        return "unknown"
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - fetched_at
    seconds = int(delta.total_seconds())
    if seconds < 0:
        return "just now"
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


def render_grounding_line(
    body: str,
    *,
    source_name: str,
    fetched_at: datetime | None,
    max_chars: int = DEFAULT_CAP,
) -> str:
    """Compose ``<body> (source: <name>, fetched <when>)``.

    The body is truncated BEFORE the provenance suffix is appended so
    the source label is never cut off. Both ``body`` and ``source_name``
    are sanitised via :func:`sanitise` (no per-arg cap — the overall
    budget is enforced after composition).
    """
    safe_source = sanitise(source_name, cap=0) or "unknown source"
    rel = relative_time(fetched_at)
    suffix = f" (source: {safe_source}, fetched {rel})"
    body_budget = max(8, max_chars - len(suffix))
    safe_body = sanitise(body, cap=body_budget)
    if not safe_body:
        safe_body = "(no summary)"
    return f"{safe_body}{suffix}"


# BTD6 stores 9,999,999 as an "infinite" sentinel for instant-pop collision
# layers (Druid's Spirit-of-the-Forest vines, etc.). It must render as ∞, never
# the raw number — a literal "9,999,999 dmg" in grounding misleads the model into
# reporting it as the tower's main-attack damage.
INFINITE_SENTINEL = 9_999_999


def is_infinite(value: object) -> bool:
    """True for BTD6's 9,999,999 'infinite' (instant-pop) sentinel value."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value >= INFINITE_SENTINEL
    )


__all__ = [
    "DEFAULT_CAP",
    "INFINITE_SENTINEL",
    "is_infinite",
    "relative_time",
    "render_grounding_line",
    "sanitise",
]
