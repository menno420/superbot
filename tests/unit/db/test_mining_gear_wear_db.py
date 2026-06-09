"""mining_gear_wear + last-broken CRUD — mock-pool tests (mirrors
test_mining_equipment_db)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from utils.db.games import mining_gear_wear as mgw
from utils.db.games import mining_player_state as mps


@pytest.mark.asyncio
async def test_get_gear_wear_filters_by_user_and_guild():
    with patch(
        "utils.db.games.mining_gear_wear.pool.fetchall",
        new_callable=AsyncMock,
        return_value=[{"item_name": "pickaxe", "durability": 42}],
    ) as mock_fetch:
        result = await mgw.get_gear_wear("123", 999)
    assert result == {"pickaxe": 42}
    query, params = mock_fetch.await_args.args
    assert "user_id=$1 AND guild_id=$2" in query.replace("  ", " ")
    assert params == ("123", 999)


@pytest.mark.asyncio
async def test_set_gear_wear_upserts_on_item_conflict():
    with patch(
        "utils.db.games.mining_gear_wear.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await mgw.set_gear_wear("123", 999, "pickaxe", 41)
    query, params = mock_exec.await_args.args
    assert "(user_id, guild_id, item_name)" in query
    assert params == ("123", 999, "pickaxe", 41)


@pytest.mark.asyncio
async def test_clear_gear_wear_deletes_one_item():
    with patch(
        "utils.db.games.mining_gear_wear.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await mgw.clear_gear_wear("123", 999, "torch")
    query, params = mock_exec.await_args.args
    assert "DELETE FROM mining_gear_wear" in query
    assert params == ("123", 999, "torch")


@pytest.mark.asyncio
async def test_get_last_broken_returns_none_without_row():
    with patch(
        "utils.db.games.mining_player_state.pool.fetchone",
        new_callable=AsyncMock,
        return_value=None,
    ):
        assert await mps.get_last_broken("123", 999) is None


@pytest.mark.asyncio
async def test_set_last_broken_upserts_and_accepts_none():
    with patch(
        "utils.db.games.mining_player_state.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await mps.set_last_broken("123", 999, "pickaxe")
        await mps.set_last_broken("123", 999, None)
    first, second = mock_exec.await_args_list
    assert first.args[1] == ("123", 999, "pickaxe")
    assert second.args[1] == ("123", 999, None)
    assert "ON CONFLICT (user_id, guild_id)" in first.args[0]
