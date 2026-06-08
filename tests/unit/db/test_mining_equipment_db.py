"""mining_equipment CRUD — mock-pool tests (mirrors test_mining_guild_scope)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from utils.db.games import mining_equipment as me


@pytest.mark.asyncio
async def test_get_equipment_filters_by_user_and_guild():
    with patch(
        "utils.db.games.mining_equipment.pool.fetchall",
        new_callable=AsyncMock,
        return_value=[{"slot": "tool", "item_name": "iron pickaxe"}],
    ) as mock_fetch:
        result = await me.get_equipment("123", 999)
    assert result == {"tool": "iron pickaxe"}
    query, params = mock_fetch.await_args.args
    assert "user_id=$1 AND guild_id=$2" in query.replace("  ", " ")
    assert params == ("123", 999)


@pytest.mark.asyncio
async def test_equip_item_upserts_on_slot_conflict():
    with patch(
        "utils.db.games.mining_equipment.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await me.equip_item("123", 999, "tool", "iron pickaxe")
    query, params = mock_exec.await_args.args
    assert "(user_id, guild_id, slot)" in query
    assert params == ("123", 999, "tool", "iron pickaxe")


@pytest.mark.asyncio
async def test_unequip_slot_deletes_one_slot():
    with patch(
        "utils.db.games.mining_equipment.pool.execute",
        new_callable=AsyncMock,
    ) as mock_exec:
        await me.unequip_slot("123", 999, "light")
    query, params = mock_exec.await_args.args
    assert "DELETE FROM mining_equipment" in query
    assert "slot=$3" in query.replace("  ", " ")
    assert params == ("123", 999, "light")
