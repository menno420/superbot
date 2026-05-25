"""Tests for ``services.xp_service.get_user_record`` (PR1).

The helper is the canonical XP read for permission/level checks.
``ai_permission_service.snapshot`` calls through here so its consumers
never learn the underlying row shape from ``utils.db.xp.get_xp``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services import xp_service
from services.xp_service import UserXPRecord


@pytest.mark.asyncio
async def test_returns_record_for_existing_xp_row():
    """A real row (messages >= 1) returns a typed UserXPRecord."""
    row = {
        "user_id": 7,
        "guild_id": 42,
        "xp": 1234,
        "level": 32,
        "messages": 250,
        "last_xp": 0,
        "coins": 0,
    }
    with patch(
        "services.xp_service.db.get_xp",
        new_callable=AsyncMock,
        return_value=row,
    ):
        record = await xp_service.get_user_record(42, 7)
    assert record == UserXPRecord(xp=1234, level=32, messages=250)


@pytest.mark.asyncio
async def test_returns_none_when_no_row_sentinel():
    """The synthesised all-zeros dict from get_xp signals "no row yet"."""
    synthesised = {
        "user_id": 7,
        "guild_id": 42,
        "xp": 0,
        "level": 0,
        "messages": 0,
        "last_xp": 0,
        "coins": 0,
    }
    with patch(
        "services.xp_service.db.get_xp",
        new_callable=AsyncMock,
        return_value=synthesised,
    ):
        record = await xp_service.get_user_record(42, 7)
    assert record is None


@pytest.mark.asyncio
async def test_returns_record_for_real_row_with_zero_xp():
    """A row with xp=0 but messages>=1 is still a real row."""
    row = {
        "user_id": 7,
        "guild_id": 42,
        "xp": 0,
        "level": 0,
        "messages": 1,
        "last_xp": 0,
        "coins": 0,
    }
    with patch(
        "services.xp_service.db.get_xp",
        new_callable=AsyncMock,
        return_value=row,
    ):
        record = await xp_service.get_user_record(42, 7)
    assert record is not None
    assert record.messages == 1


@pytest.mark.asyncio
async def test_propagates_db_error():
    """Real DB failures must propagate — the helper does not catch them."""
    import asyncpg

    with patch(
        "services.xp_service.db.get_xp",
        new_callable=AsyncMock,
        side_effect=asyncpg.PostgresError("connection lost"),
    ):
        with pytest.raises(asyncpg.PostgresError):
            await xp_service.get_user_record(42, 7)
