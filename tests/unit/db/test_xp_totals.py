"""get_guild_xp_totals — mock-pool tests (mirrors test_mining_player_state_db)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from utils.db import xp as xp_db


@pytest.mark.asyncio
async def test_totals_returns_summed_values():
    with patch(
        "utils.db.xp.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"total_xp": 1234, "total_coins": 567},
    ) as mock_fetch:
        result = await xp_db.get_guild_xp_totals(999)
    assert result == (1234, 567)
    query, params = mock_fetch.await_args.args
    assert "FROM xp WHERE guild_id=$1" in query
    assert "COALESCE(SUM(xp), 0)" in query
    assert "COALESCE(SUM(coins), 0)" in query
    assert params == (999,)


@pytest.mark.asyncio
async def test_totals_defaults_to_zero_when_no_row():
    with patch(
        "utils.db.xp.pool.fetchone",
        new_callable=AsyncMock,
        return_value=None,
    ):
        assert await xp_db.get_guild_xp_totals(999) == (0, 0)


@pytest.mark.asyncio
async def test_totals_is_reexported_from_db_package():
    from utils import db

    assert db.get_guild_xp_totals is xp_db.get_guild_xp_totals
