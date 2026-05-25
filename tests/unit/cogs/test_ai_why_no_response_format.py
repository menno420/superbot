"""Tests for the ``!ai why-no-response`` embed format (PR1).

Before PR1 the command rendered ``decision | reason_code | channel |
user | task`` only. PR1 adds the columns that the audit table already
contains — relative timestamp, provider, model, route — and switches
from a bare ``ctx.send`` text block to a titled embed.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import pytest

from cogs.ai_cog import _format_audit_row, _relative_time

# ---------------------------------------------------------------------------
# _relative_time
# ---------------------------------------------------------------------------


def test_relative_time_seconds():
    now = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)
    ts = now - timedelta(seconds=12)
    assert _relative_time(ts, now=now) == "12s ago"


def test_relative_time_minutes():
    now = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)
    ts = now - timedelta(minutes=5)
    assert _relative_time(ts, now=now) == "5m ago"


def test_relative_time_hours():
    now = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)
    ts = now - timedelta(hours=3)
    assert _relative_time(ts, now=now) == "3h ago"


def test_relative_time_days():
    now = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)
    ts = now - timedelta(days=2)
    assert _relative_time(ts, now=now) == "2d ago"


def test_relative_time_handles_naive_datetime():
    """Naive datetimes are treated as UTC."""
    now = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)
    ts_naive = datetime(2026, 5, 25, 11, 30, 0)
    assert _relative_time(ts_naive, now=now) == "30m ago"


def test_relative_time_future_returns_sentinel():
    """Clock skew must not raise."""
    now = datetime(2026, 5, 25, 12, 0, 0, tzinfo=timezone.utc)
    ts = now + timedelta(seconds=10)
    assert _relative_time(ts, now=now) == "in the future"


# ---------------------------------------------------------------------------
# _format_audit_row
# ---------------------------------------------------------------------------


def _row(**overrides):
    base = {
        "id": 1,
        "guild_id": 1,
        "channel_id": 12345,
        "category_id": None,
        "user_id": 67890,
        "message_id": None,
        "task": "BTD6_ANSWER",
        "route": "primary",
        "decision": "denied",
        "reason_code": "POLICY_CHANNEL_DENY",
        "policy_snapshot_hash": None,
        "instruction_profile_ids": None,
        "provider": "openai",
        "model": "gpt-4o-mini",
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=2),
    }
    base.update(overrides)
    return base


def test_format_audit_row_includes_all_required_columns():
    line = _format_audit_row(_row())
    assert "denied" in line
    assert "POLICY_CHANNEL_DENY" in line
    assert "task=BTD6_ANSWER" in line
    assert "route=primary" in line
    assert "<#12345>" in line
    assert "<@67890>" in line
    assert "provider=openai" in line
    assert "model=gpt-4o-mini" in line


def test_format_audit_row_renders_relative_timestamp():
    line = _format_audit_row(_row())
    assert re.search(r"\d+[smhd] ago", line), f"no relative-time pattern in {line!r}"


def test_format_audit_row_handles_null_optionals():
    line = _format_audit_row(_row(task=None, route=None, provider=None, model=None))
    assert "task=—" in line
    assert "route=—" in line
    assert "provider=—" in line
    assert "model=—" in line


def test_format_audit_row_handles_missing_created_at():
    """A row without a parseable timestamp falls back to '—'."""
    line = _format_audit_row(_row(created_at=None))
    assert "`—       `" in line or "—" in line


def test_format_audit_row_does_not_leak_message_content():
    """The audit table has no content column; the renderer must not pretend it."""
    line = _format_audit_row(_row())
    assert "content" not in line.lower()
