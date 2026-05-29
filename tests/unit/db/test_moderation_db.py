"""Regression test for ``utils.db.moderation.log_mod_action``.

``mod_logs.timestamp`` is ``timestamp with time zone``; asyncpg requires
a real ``datetime`` instance for that column.  A previous revision bound
``datetime.now(...).strftime("%Y-%m-%d %H:%M:%S")`` — a *string* — which
raised ``asyncpg.DataError`` at insert time and silently broke the audit
log for every moderation action (warn / timeout / kick / ban / unban /
clear_warnings) and crashed the counting stage's auto-delete path.

This pins the contract: ``log_mod_action`` must bind a tz-aware
``datetime``, not a formatted string.
"""

from __future__ import annotations

import datetime as dt

import pytest

from utils.db import moderation


@pytest.mark.asyncio
async def test_log_mod_action_binds_datetime_not_string(monkeypatch):
    captured: dict = {}

    async def fake_execute(sql, params):
        captured["sql"] = sql
        captured["params"] = params

    monkeypatch.setattr(moderation.pool, "execute", fake_execute)

    await moderation.log_mod_action(1, "ban", 2, 3, "spam")

    ts = captured["params"][0]
    assert isinstance(ts, dt.datetime), f"timestamp must be datetime, got {type(ts)!r}"
    assert ts.tzinfo is not None, "timestamp must be tz-aware for a timestamptz column"
    assert "INSERT INTO mod_logs" in captured["sql"]
