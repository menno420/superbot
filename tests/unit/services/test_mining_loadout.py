"""Workflow tests for gear loadout presets (V-14 / Q-0175 unified-loadout model).

Saving snapshots the player's current equipped gear under a name; applying
restores that exact set — equipping every saved item still owned and clearing
any other filled slot — so a preset behaves like a gear set.  Equip/unequip
never consume the item, so applying is reversible.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import mining_workflow

_WF = "services.mining_workflow"


@pytest.fixture
def _null_txn():
    """db.transaction() → a no-op context manager yielding a sentinel conn."""

    @asynccontextmanager
    async def _txn():
        yield MagicMock(name="conn")

    with patch(f"{_WF}.db.transaction", _txn):
        yield


# --------------------------------------------------------------------------- #
# save_loadout
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_save_requires_a_name():
    result = await mining_workflow.save_loadout(1, 99, "   ")
    assert result.ok is False
    assert "name" in result.message.lower()


@pytest.mark.asyncio
async def test_save_requires_equipped_gear():
    with patch(f"{_WF}.db.get_equipment", new_callable=AsyncMock, return_value={}):
        result = await mining_workflow.save_loadout(1, 99, "mining")
    assert result.ok is False
    assert "no gear equipped" in result.message.lower()


@pytest.mark.asyncio
async def test_save_snapshots_current_equipment():
    equipped = {"tool": "iron pickaxe", "light": "torch"}
    with (
        patch(
            f"{_WF}.db.get_equipment", new_callable=AsyncMock, return_value=equipped
        ),
        patch(f"{_WF}.db.list_loadouts", new_callable=AsyncMock, return_value=[]),
        patch(f"{_WF}.db.save_loadout", new_callable=AsyncMock) as mock_save,
    ):
        result = await mining_workflow.save_loadout(1, 99, "  Mining  ")
    assert result.ok is True
    # Name is normalised (lowercase, trimmed) and the full snapshot is stored.
    assert mock_save.await_args.args == ("1", 99, "mining", equipped)
    assert "2 slots" in result.message


@pytest.mark.asyncio
async def test_save_blocked_at_the_preset_cap():
    full = [f"set{i}" for i in range(mining_workflow.MAX_LOADOUT_PRESETS)]
    with (
        patch(
            f"{_WF}.db.get_equipment",
            new_callable=AsyncMock,
            return_value={"tool": "iron pickaxe"},
        ),
        patch(f"{_WF}.db.list_loadouts", new_callable=AsyncMock, return_value=full),
        patch(f"{_WF}.db.save_loadout", new_callable=AsyncMock) as mock_save,
    ):
        result = await mining_workflow.save_loadout(1, 99, "newname")
    assert result.ok is False
    assert str(mining_workflow.MAX_LOADOUT_PRESETS) in result.message
    mock_save.assert_not_awaited()


@pytest.mark.asyncio
async def test_save_overwrite_of_existing_name_is_allowed_at_cap():
    full = [f"set{i}" for i in range(mining_workflow.MAX_LOADOUT_PRESETS)]
    with (
        patch(
            f"{_WF}.db.get_equipment",
            new_callable=AsyncMock,
            return_value={"tool": "iron pickaxe"},
        ),
        patch(f"{_WF}.db.list_loadouts", new_callable=AsyncMock, return_value=full),
        patch(f"{_WF}.db.save_loadout", new_callable=AsyncMock) as mock_save,
    ):
        result = await mining_workflow.save_loadout(1, 99, "set3")
    assert result.ok is True
    mock_save.assert_awaited_once()


# --------------------------------------------------------------------------- #
# apply_loadout
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_apply_unknown_loadout_errors():
    with patch(f"{_WF}.db.get_loadout", new_callable=AsyncMock, return_value={}):
        result = await mining_workflow.apply_loadout(1, 99, "ghost")
    assert result.ok is False
    assert "no loadout" in result.message.lower()


@pytest.mark.asyncio
async def test_apply_equips_owned_clears_others_and_reports_missing(_null_txn):
    preset = {"tool": "iron pickaxe", "light": "torch", "charm": "lucky charm"}
    inventory = {"iron pickaxe": 1, "torch": 1}  # lucky charm no longer owned
    current = {"tool": "bronze pickaxe", "weapon": "iron sword"}  # weapon to clear
    with (
        patch(f"{_WF}.db.get_loadout", new_callable=AsyncMock, return_value=preset),
        patch(
            f"{_WF}.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value=inventory,
        ),
        patch(f"{_WF}.db.get_equipment", new_callable=AsyncMock, return_value=current),
        patch(f"{_WF}.db.equip_item", new_callable=AsyncMock) as mock_equip,
        patch(f"{_WF}.db.unequip_slot", new_callable=AsyncMock) as mock_unequip,
    ):
        result = await mining_workflow.apply_loadout(1, 99, "mining")
    assert result.ok is True
    equipped = {c.args[2]: c.args[3] for c in mock_equip.await_args_list}
    assert equipped == {"tool": "iron pickaxe", "light": "torch"}
    # The currently-filled weapon slot (not in the preset) is cleared; the
    # never-equipped slots are left untouched.
    cleared = {c.args[2] for c in mock_unequip.await_args_list}
    assert cleared == {"weapon"}
    assert "lucky charm" in result.message.lower()


@pytest.mark.asyncio
async def test_apply_with_nothing_owned_errors_and_writes_nothing(_null_txn):
    preset = {"tool": "diamond pickaxe"}
    with (
        patch(f"{_WF}.db.get_loadout", new_callable=AsyncMock, return_value=preset),
        patch(
            f"{_WF}.db.get_mining_inventory", new_callable=AsyncMock, return_value={}
        ),
        patch(f"{_WF}.db.equip_item", new_callable=AsyncMock) as mock_equip,
        patch(f"{_WF}.db.unequip_slot", new_callable=AsyncMock) as mock_unequip,
    ):
        result = await mining_workflow.apply_loadout(1, 99, "mining")
    assert result.ok is False
    assert "no longer own" in result.message.lower()
    mock_equip.assert_not_awaited()
    mock_unequip.assert_not_awaited()


# --------------------------------------------------------------------------- #
# list / delete
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_list_loadouts_passes_through():
    with patch(
        f"{_WF}.db.list_loadouts",
        new_callable=AsyncMock,
        return_value=["combat", "mining"],
    ):
        assert await mining_workflow.list_loadouts(1, 99) == ["combat", "mining"]


@pytest.mark.asyncio
async def test_delete_missing_loadout_errors():
    with patch(f"{_WF}.db.delete_loadout", new_callable=AsyncMock, return_value=0):
        result = await mining_workflow.delete_loadout(1, 99, "ghost")
    assert result.ok is False


@pytest.mark.asyncio
async def test_delete_existing_loadout_ok():
    with patch(f"{_WF}.db.delete_loadout", new_callable=AsyncMock, return_value=3):
        result = await mining_workflow.delete_loadout(1, 99, "Mining")
    assert result.ok is True
    assert "mining" in result.message.lower()
