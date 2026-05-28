"""BTD6 event window formatting.

Converges four overlapping helpers that previously lived in
``cogs/btd6/_builders.py`` (``_ms_to_human``, ``_event_window``,
``_format_window_status``) and ``views/btd6/panel.py``
(``_format_ends_relative``) into one tested module.

Two surfaces:

* :func:`format_window` — canonical typed API. Returns a
  :class:`WindowStatus` that carries the human / relative / iso forms
  the new view-model service consumes.
* Thin string helpers (:func:`format_ms_human`, :func:`format_window_range`,
  :func:`format_window_status`, :func:`format_ends_relative`) preserve
  byte-identical output for the existing embed builders that consume
  them. New code should prefer :func:`format_window`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

WindowState = Literal["upcoming", "active", "ended", "unknown"]


@dataclass(frozen=True)
class WindowStatus:
    """Computed event window state plus the rendered forms."""

    state: WindowState
    human: str
    start_iso: str
    end_iso: str
    relative: str


def _ms_to_dt(ms: Any) -> datetime | None:
    if not isinstance(ms, (int, float)) or ms <= 0:
        return None
    try:
        return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _iso(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M UTC")


def _compact_unit(seconds: int) -> str:
    """`Xm` / `Xh` / `Xd` — single-unit compact form used by the panel."""
    if seconds <= 0:
        return "ended"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86_400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86_400}d"


def format_ms_human(ms: Any) -> str:
    """Render a milliseconds-since-epoch value as ``YYYY-MM-DD HH:MM UTC``.

    Returns ``"—"`` for missing / non-numeric inputs.
    """
    return _iso(_ms_to_dt(ms))


def format_window_range(start_ms: Any, end_ms: Any) -> str:
    """Render ``start_ms`` → ``end_ms`` as a single human window string.

    Returns ``"—"`` when both endpoints are missing. Mirrors the
    previous ``_event_window`` helper.
    """
    start = format_ms_human(start_ms)
    end = format_ms_human(end_ms)
    if start == "—" and end == "—":
        return "—"
    return f"{start} → {end}"


def format_window_status(
    body: dict[str, Any],
    *,
    now: datetime | None = None,
) -> str:
    """Render ``status: live · ends in 1d 4h`` and friends.

    Mirrors the previous ``_format_window_status`` helper byte-for-byte
    (days + sub-day hours form, e.g. ``"1d 4h"``). The literal backtick
    formatting wraps each status keyword in markdown code spans.
    """
    current = now if now is not None else datetime.now(tz=timezone.utc)
    start_dt = _ms_to_dt(body.get("start_ms"))
    end_dt = _ms_to_dt(body.get("end_ms"))
    if start_dt is None and end_dt is None:
        return "status: `unknown`"
    if start_dt is not None and current < start_dt:
        delta = start_dt - current
        return f"status: `upcoming` · starts in {delta.days}d {delta.seconds // 3600}h"
    if end_dt is not None and current > end_dt:
        return "status: `ended`"
    if end_dt is not None:
        delta = end_dt - current
        return f"status: `live` · ends in {delta.days}d {delta.seconds // 3600}h"
    return "status: `live`"


def format_ends_relative(
    end_ms: Any,
    *,
    now: datetime | None = None,
) -> str:
    """Compact ``· ends Xh`` / ``· ended`` / ``""`` form for the panel.

    Empty string when ``end_ms`` is missing or non-numeric. Mirrors the
    previous ``_format_ends_relative`` helper byte-for-byte.
    """
    end_dt = _ms_to_dt(end_ms)
    if end_dt is None:
        return ""
    current = now if now is not None else datetime.now(tz=timezone.utc)
    delta = end_dt - current
    seconds = int(delta.total_seconds())
    if seconds <= 0:
        return "· ended"
    return f"· ends {_compact_unit(seconds)}"


def format_window(
    start_ms: Any,
    end_ms: Any,
    *,
    now: datetime | None = None,
) -> WindowStatus:
    """Canonical typed window API. The view-model service consumes this.

    `.human` matches :func:`format_window_status` output.
    `.relative` matches :func:`format_ends_relative` output.
    `.start_iso` / `.end_iso` match :func:`format_ms_human` output.
    `.state` is one of upcoming / active / ended / unknown.
    """
    current = now if now is not None else datetime.now(tz=timezone.utc)
    start_dt = _ms_to_dt(start_ms)
    end_dt = _ms_to_dt(end_ms)
    start_iso = _iso(start_dt)
    end_iso = _iso(end_dt)
    body = {"start_ms": start_ms, "end_ms": end_ms}
    human = format_window_status(body, now=current)
    relative = format_ends_relative(end_ms, now=current)

    if start_dt is None and end_dt is None:
        state: WindowState = "unknown"
    elif start_dt is not None and current < start_dt:
        state = "upcoming"
    elif end_dt is not None and current > end_dt:
        state = "ended"
    else:
        state = "active"

    return WindowStatus(
        state=state,
        human=human,
        start_iso=start_iso,
        end_iso=end_iso,
        relative=relative,
    )


__all__ = [
    "WindowState",
    "WindowStatus",
    "format_ends_relative",
    "format_ms_human",
    "format_window",
    "format_window_range",
    "format_window_status",
]
