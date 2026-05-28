"""Coverage for the consolidated event-window helpers.

These functions replace four previously-duplicated helpers (``_ms_to_human``,
``_event_window``, ``_format_window_status``, ``_format_ends_relative``).
The tests pin byte-identical output for each surface so the embed
builders that consume them stay stable.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from utils.btd6.event_window import (
    WindowStatus,
    format_ends_relative,
    format_ms_human,
    format_window,
    format_window_range,
    format_window_status,
)

_NOW = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)


def _ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


# ---------------------------------------------------------------------------
# format_ms_human
# ---------------------------------------------------------------------------


def test_format_ms_human_renders_utc_string() -> None:
    moment = datetime(2026, 1, 2, 3, 4, tzinfo=timezone.utc)
    assert format_ms_human(_ms(moment)) == "2026-01-02 03:04 UTC"


@pytest.mark.parametrize("bad", [None, 0, -1, "abc", float("nan")])
def test_format_ms_human_returns_dash_for_bad_inputs(bad) -> None:
    assert format_ms_human(bad) == "—"


# ---------------------------------------------------------------------------
# format_window_range
# ---------------------------------------------------------------------------


def test_format_window_range_both_present() -> None:
    a = _ms(datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc))
    b = _ms(datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc))
    assert format_window_range(a, b) == "2026-01-01 00:00 UTC → 2026-01-02 00:00 UTC"


def test_format_window_range_both_missing_returns_dash() -> None:
    assert format_window_range(None, None) == "—"
    assert format_window_range(0, 0) == "—"


def test_format_window_range_one_missing_renders_partial() -> None:
    a = _ms(datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc))
    assert format_window_range(a, None) == "2026-01-01 00:00 UTC → —"


# ---------------------------------------------------------------------------
# format_window_status (byte-identical to the previous _format_window_status)
# ---------------------------------------------------------------------------


def test_format_window_status_unknown_when_no_data() -> None:
    assert format_window_status({}, now=_NOW) == "status: `unknown`"


def test_format_window_status_upcoming() -> None:
    start = _NOW + timedelta(days=1, hours=4)
    body = {"start_ms": _ms(start), "end_ms": _ms(start + timedelta(hours=2))}
    assert (
        format_window_status(body, now=_NOW) == "status: `upcoming` · starts in 1d 4h"
    )


def test_format_window_status_live_with_end() -> None:
    end = _NOW + timedelta(days=1, hours=4)
    body = {"start_ms": _ms(_NOW - timedelta(hours=1)), "end_ms": _ms(end)}
    assert format_window_status(body, now=_NOW) == "status: `live` · ends in 1d 4h"


def test_format_window_status_live_without_end() -> None:
    body = {"start_ms": _ms(_NOW - timedelta(hours=1))}
    assert format_window_status(body, now=_NOW) == "status: `live`"


def test_format_window_status_ended() -> None:
    body = {
        "start_ms": _ms(_NOW - timedelta(days=2)),
        "end_ms": _ms(_NOW - timedelta(hours=1)),
    }
    assert format_window_status(body, now=_NOW) == "status: `ended`"


# ---------------------------------------------------------------------------
# format_ends_relative (byte-identical to the previous _format_ends_relative)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [None, 0, -1, "abc"])
def test_format_ends_relative_empty_for_bad_input(bad) -> None:
    assert format_ends_relative(bad, now=_NOW) == ""


def test_format_ends_relative_ended() -> None:
    end = _NOW - timedelta(hours=1)
    assert format_ends_relative(_ms(end), now=_NOW) == "· ended"


def test_format_ends_relative_minutes() -> None:
    end = _NOW + timedelta(minutes=42)
    assert format_ends_relative(_ms(end), now=_NOW) == "· ends 42m"


def test_format_ends_relative_hours() -> None:
    end = _NOW + timedelta(hours=5)
    assert format_ends_relative(_ms(end), now=_NOW) == "· ends 5h"


def test_format_ends_relative_days() -> None:
    end = _NOW + timedelta(days=3)
    assert format_ends_relative(_ms(end), now=_NOW) == "· ends 3d"


# ---------------------------------------------------------------------------
# format_window — typed canonical API
# ---------------------------------------------------------------------------


def test_format_window_unknown() -> None:
    status = format_window(None, None, now=_NOW)
    assert isinstance(status, WindowStatus)
    assert status.state == "unknown"
    assert status.relative == ""
    assert status.human == "status: `unknown`"
    assert status.start_iso == "—"
    assert status.end_iso == "—"


def test_format_window_upcoming() -> None:
    start = _NOW + timedelta(days=1)
    end = start + timedelta(hours=4)
    status = format_window(_ms(start), _ms(end), now=_NOW)
    assert status.state == "upcoming"
    assert "starts in" in status.human


def test_format_window_active() -> None:
    end = _NOW + timedelta(hours=5)
    status = format_window(_ms(_NOW - timedelta(hours=1)), _ms(end), now=_NOW)
    assert status.state == "active"
    assert status.relative == "· ends 5h"


def test_format_window_ended() -> None:
    status = format_window(
        _ms(_NOW - timedelta(days=2)),
        _ms(_NOW - timedelta(hours=1)),
        now=_NOW,
    )
    assert status.state == "ended"
    assert status.relative == "· ended"
    assert status.human == "status: `ended`"


def test_format_window_active_without_end_is_live() -> None:
    status = format_window(_ms(_NOW - timedelta(hours=1)), None, now=_NOW)
    assert status.state == "active"
    assert status.human == "status: `live`"
    assert status.relative == ""
