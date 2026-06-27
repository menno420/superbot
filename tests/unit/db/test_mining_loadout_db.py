"""mining_loadout_presets CRUD — mock-pool tests (mirrors test_mining_equipment_db)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from utils.db.games import mining_loadout as ml

_EXEC = "utils.db.games.mining_loadout.pool.execute"
_FETCH = "utils.db.games.mining_loadout.pool.fetchall"


@pytest.mark.asyncio
async def test_save_loadout_replaces_then_inserts_each_slot():
    with patch(_EXEC, new_callable=AsyncMock) as mock_exec:
        await ml.save_loadout(
            "123", 999, "mining", {"tool": "iron pickaxe", "light": "torch"}
        )
    calls = mock_exec.await_args_list
    # First call clears the preset, then one INSERT per slot.
    assert "DELETE FROM mining_loadout_presets" in calls[0].args[0]
    assert calls[0].args[1] == ("123", 999, "mining")
    inserts = [c for c in calls[1:] if "INSERT" in c.args[0]]
    assert len(inserts) == 2
    assert {c.args[1][3]: c.args[1][4] for c in inserts} == {
        "tool": "iron pickaxe",
        "light": "torch",
    }


@pytest.mark.asyncio
async def test_save_empty_loadout_only_clears():
    with patch(_EXEC, new_callable=AsyncMock) as mock_exec:
        await ml.save_loadout("123", 999, "mining", {})
    assert mock_exec.await_count == 1
    assert "DELETE FROM mining_loadout_presets" in mock_exec.await_args.args[0]


@pytest.mark.asyncio
async def test_get_loadout_maps_slot_to_item():
    with patch(
        _FETCH,
        new_callable=AsyncMock,
        return_value=[
            {"slot": "tool", "item_name": "iron pickaxe"},
            {"slot": "light", "item_name": "torch"},
        ],
    ) as mock_fetch:
        result = await ml.get_loadout("123", 999, "mining")
    assert result == {"tool": "iron pickaxe", "light": "torch"}
    _, params = mock_fetch.await_args.args
    assert params == ("123", 999, "mining")


@pytest.mark.asyncio
async def test_list_loadouts_returns_names():
    with patch(
        _FETCH,
        new_callable=AsyncMock,
        return_value=[{"name": "combat"}, {"name": "mining"}],
    ):
        result = await ml.list_loadouts("123", 999)
    assert result == ["combat", "mining"]


@pytest.mark.asyncio
async def test_delete_loadout_returns_rows_removed():
    with patch(
        _FETCH,
        new_callable=AsyncMock,
        return_value=[{"slot": "tool"}, {"slot": "light"}],
    ) as mock_fetch:
        removed = await ml.delete_loadout("123", 999, "mining")
    assert removed == 2
    query, params = mock_fetch.await_args.args
    assert "DELETE FROM mining_loadout_presets" in query
    assert "RETURNING slot" in query
    assert params == ("123", 999, "mining")
