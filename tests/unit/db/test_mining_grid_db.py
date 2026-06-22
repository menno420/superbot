"""mining_grid CRUD — mock-pool tests (mirrors test_mining_player_state_db)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from utils.db.games import mining_grid as mg


@pytest.mark.asyncio
async def test_get_position_returns_stored_xy():
    with patch(
        "utils.db.games.mining_grid.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"pos_x": 4, "pos_y": -2},
    ):
        assert await mg.get_position("123", 999) == (4, -2)


@pytest.mark.asyncio
async def test_get_position_defaults_to_origin_when_no_row():
    with patch(
        "utils.db.games.mining_grid.pool.fetchone",
        new_callable=AsyncMock,
        return_value=None,
    ):
        assert await mg.get_position("123", 999) == (0, 0)


@pytest.mark.asyncio
async def test_set_position_upserts():
    with patch(
        "utils.db.games.mining_grid.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await mg.set_position("123", 999, 5, 6)
    query, params = mock_exec.await_args.args
    assert "INSERT INTO mining_player_state" in query
    assert "pos_x=$3, pos_y=$4" in query
    assert params == ("123", 999, 5, 6)


@pytest.mark.asyncio
async def test_get_world_seed_defaults_to_guild_id():
    with patch(
        "utils.db.games.mining_grid.pool.fetchone",
        new_callable=AsyncMock,
        return_value=None,
    ):
        # No row → the world is the guild's own deterministic seed.
        assert await mg.get_world_seed(555) == 555


@pytest.mark.asyncio
async def test_get_world_seed_returns_override():
    with patch(
        "utils.db.games.mining_grid.pool.fetchone",
        new_callable=AsyncMock,
        return_value={"seed": 12345},
    ):
        assert await mg.get_world_seed(555) == 12345


@pytest.mark.asyncio
async def test_set_world_seed_upserts():
    with patch(
        "utils.db.games.mining_grid.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await mg.set_world_seed(555, 999)
    query, params = mock_exec.await_args.args
    assert "INSERT INTO mining_world" in query
    assert params == (555, 999)


@pytest.mark.asyncio
async def test_mark_discovered_is_idempotent_insert():
    with patch(
        "utils.db.games.mining_grid.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await mg.mark_discovered("123", 999, 1, 2, 3)
    query, params = mock_exec.await_args.args
    assert "INSERT INTO mining_discovered" in query
    assert "ON CONFLICT" in query and "DO NOTHING" in query
    assert params == ("123", 999, 1, 2, 3)


@pytest.mark.asyncio
async def test_get_discovered_window_returns_xy_set():
    with patch(
        "utils.db.games.mining_grid.pool.fetchall",
        new_callable=AsyncMock,
        return_value=[{"x": 1, "y": 2}, {"x": -1, "y": 0}],
    ) as mock_fetch:
        result = await mg.get_discovered_window("123", 999, 0, -2, 2, -2, 2)
    assert result == {(1, 2), (-1, 0)}
    query, params = mock_fetch.await_args.args
    assert "FROM mining_discovered" in query
    assert params == ("123", 999, 0, -2, 2, -2, 2)
