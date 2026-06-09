"""mining_player_state CRUD — mock-pool tests (mirrors test_mining_equipment_db)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from utils.db.games import mining_player_state as mps


@pytest.mark.asyncio
async def test_get_depth_returns_stored_value():
    with patch(
        "utils.db.games.mining_player_state.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"depth": 2},
    ) as mock_fetch:
        result = await mps.get_depth("123", 999)
    assert result == 2
    query, params = mock_fetch.await_args.args
    assert "user_id=$1 AND guild_id=$2" in query.replace("  ", " ")
    assert params == ("123", 999)


@pytest.mark.asyncio
async def test_get_depth_defaults_to_zero_when_no_row():
    with patch(
        "utils.db.games.mining_player_state.pool.fetchone",
        new_callable=AsyncMock,
        return_value=None,
    ):
        assert await mps.get_depth("123", 999) == 0


@pytest.mark.asyncio
async def test_set_depth_upserts_on_conflict():
    with patch(
        "utils.db.games.mining_player_state.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await mps.set_depth("123", 999, 3)
    query, params = mock_exec.await_args.args
    assert "INSERT INTO mining_player_state" in query
    assert "(user_id, guild_id)" in query
    assert params == ("123", 999, 3)
