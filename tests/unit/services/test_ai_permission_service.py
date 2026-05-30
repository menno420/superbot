"""Tests for ``services.ai_permission_service.snapshot`` (PR1).

The XP-lookup bug fixed in PR1: previously ``snapshot`` called a
non-existent ``xp_service.get_user_record`` and silently fell back to
``level=0, is_fresh_user=True``, so every permission check below the
guild's minimum level passed the fresh-user gate regardless of the
real XP row. These tests pin the corrected behaviour.
"""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, patch

import asyncpg
import pytest

from services import ai_permission_service
from services.xp_service import UserXPRecord


@pytest.mark.asyncio
async def test_snapshot_level_32_passes_min_level_2(caplog):
    """A real level-32 row must surface as level=32, is_fresh_user=False."""
    with patch(
        "services.xp_service.get_user_record",
        new_callable=AsyncMock,
        return_value=UserXPRecord(xp=12345, level=32, messages=500),
    ):
        snap = await ai_permission_service.snapshot(guild_id=1, user_id=7)
    assert snap.level == 32
    assert snap.is_fresh_user is False
    # No log lines from a successful read.
    assert not any("xp lookup failed" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_snapshot_no_row_returns_fresh_user(caplog):
    """A None record (no XP row yet) is the silent fresh-user path."""
    caplog.set_level(logging.DEBUG, logger="bot.services.ai_permission")
    with patch(
        "services.xp_service.get_user_record",
        new_callable=AsyncMock,
        return_value=None,
    ):
        snap = await ai_permission_service.snapshot(guild_id=1, user_id=7)
    assert snap.level == 0
    assert snap.is_fresh_user is True
    # The no-row path must not emit a WARNING.
    warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert warnings == []


@pytest.mark.asyncio
async def test_snapshot_db_error_logs_warning_not_debug(caplog):
    """A real asyncpg failure produces a WARNING (not silent DEBUG)."""
    caplog.set_level(logging.DEBUG, logger="bot.services.ai_permission")
    with patch(
        "services.xp_service.get_user_record",
        new_callable=AsyncMock,
        side_effect=asyncpg.PostgresError("connection lost"),
    ):
        snap = await ai_permission_service.snapshot(guild_id=1, user_id=7)
    # Fallback is still safe (level=0, fresh=True) for availability,
    # but the WARNING surfaces the failure to operators.
    assert snap.level == 0
    assert snap.is_fresh_user is True
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("xp lookup failed" in r.message for r in warnings)
    assert any("PostgresError" in r.getMessage() for r in warnings)


@pytest.mark.asyncio
async def test_snapshot_propagates_programming_errors():
    """AttributeError / TypeError must NOT be caught — they signal bugs."""

    async def boom(*_, **__):
        raise AttributeError("xp_service has no attribute foo")

    with patch("services.xp_service.get_user_record", side_effect=boom):
        with pytest.raises(AttributeError):
            await ai_permission_service.snapshot(guild_id=1, user_id=7)


@pytest.mark.asyncio
async def test_snapshot_zero_xp_but_real_row_is_not_fresh():
    """Level 0 with positive XP is still not a fresh user."""
    with patch(
        "services.xp_service.get_user_record",
        new_callable=AsyncMock,
        return_value=UserXPRecord(xp=50, level=0, messages=3),
    ):
        snap = await ai_permission_service.snapshot(guild_id=1, user_id=7)
    assert snap.level == 0
    assert snap.is_fresh_user is False


def test_forget_guild_removes_only_that_guilds_trackers():
    """guild_lifecycle teardown must drop a departed guild's cooldown +
    fresh-allowance entries without touching other guilds (audit P1-9 —
    prevents unbounded dict growth + stale state on re-invite).
    """
    ai_permission_service._reset_for_tests()
    # Guild 100 — two users; one also consumed a fresh-mention allowance.
    ai_permission_service.mark_reply_sent(100, 1)
    ai_permission_service.mark_reply_sent(100, 2)
    ai_permission_service.consume_fresh_allowance(100, 1)
    # Guild 200 — must survive the sweep.
    ai_permission_service.mark_reply_sent(200, 3)
    ai_permission_service.consume_fresh_allowance(200, 3)

    removed = ai_permission_service.forget_guild(100)

    # 2 cooldown rows + 1 allowance row for guild 100.
    assert removed == 3
    # Membership checks only — `in` does not trip the defaultdict factory.
    assert (100, 1) not in ai_permission_service._LAST_REPLY_AT
    assert (100, 2) not in ai_permission_service._LAST_REPLY_AT
    assert (100, 1) not in ai_permission_service._FRESH_ALLOWANCE_USED
    # Guild 200 untouched.
    assert (200, 3) in ai_permission_service._LAST_REPLY_AT
    assert (200, 3) in ai_permission_service._FRESH_ALLOWANCE_USED
    ai_permission_service._reset_for_tests()


def test_forget_guild_returns_zero_for_unknown_guild():
    ai_permission_service._reset_for_tests()
    assert ai_permission_service.forget_guild(999) == 0
