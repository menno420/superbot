"""Workflow tests for the Forge — build_structure + the craft forge-gate (Slice B).

The build is the §7.5 coin + material sink: one transaction debits coins,
consumes materials, and raises the level.  The craft gate blocks gold/diamond
gear until the forge is built, and (critically) does NOT touch the structures
table for forge-free recipes — the additive property.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import mining_workflow
from services.economy_service import InsufficientFundsError

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
# The craft forge-gate
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_craft_gold_gear_blocked_without_forge():
    with patch(
        f"{_WF}.db.get_structures",
        new_callable=AsyncMock,
        return_value={},  # no forge built
    ):
        result = await mining_workflow.craft(1, 99, "gold helmet")
    assert result.ok is False
    assert "Forge I" in result.message
    assert "!forge" in result.message


@pytest.mark.asyncio
async def test_craft_diamond_gear_needs_forge_two():
    with patch(
        f"{_WF}.db.get_structures",
        new_callable=AsyncMock,
        return_value={"forge": 1},  # Forge I is not enough for diamond
    ):
        result = await mining_workflow.craft(1, 99, "diamond sword")
    assert result.ok is False
    assert "Forge II" in result.message


@pytest.mark.asyncio
async def test_craft_gold_gear_allowed_with_forge(_null_txn):
    with (
        patch(
            f"{_WF}.db.get_structures",
            new_callable=AsyncMock,
            return_value={"forge": 1},
        ),
        patch(
            f"{_WF}.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"gold": 99},
        ),
        patch(f"{_WF}.db.apply_inventory_deltas", new_callable=AsyncMock),
        patch(
            f"{_WF}.game_xp_service.award",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        result = await mining_workflow.craft(1, 99, "gold helmet")
    assert result.ok is True
    assert result.message == "Crafted **gold helmet**!"


@pytest.mark.asyncio
async def test_craft_free_tier_never_reads_structures():
    """The additive property — forge-free recipes do NOT touch the forge table."""
    with (
        patch(f"{_WF}.db.get_structures", new_callable=AsyncMock) as gs,
        patch(
            f"{_WF}.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"wood": 1},  # not enough → fails before any write
        ),
    ):
        result = await mining_workflow.craft(1, 99, "pickaxe")
    assert result.ok is False  # missing-materials, the pre-Slice-B behaviour
    gs.assert_not_awaited()


# --------------------------------------------------------------------------- #
# build_structure — the coin + material sink
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_build_forge_success(_null_txn):
    with (
        patch(f"{_WF}.db.get_structures", new_callable=AsyncMock, return_value={}),
        patch(
            f"{_WF}.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"iron": 50, "stone": 50},
        ),
        patch(
            f"{_WF}.economy_service.debit_in_txn",
            new_callable=AsyncMock,
            return_value=4_200,
        ),
        patch(f"{_WF}.db.apply_inventory_deltas", new_callable=AsyncMock) as deltas,
        patch(f"{_WF}.db.set_structure_level", new_callable=AsyncMock) as lvl,
        patch(f"{_WF}._emit_balance", new_callable=AsyncMock),
    ):
        result = await mining_workflow.build_structure(1, 99, "forge")
    assert result.ok is True
    assert "Forge I" in result.message
    assert "gold-tier" in result.message
    # Materials consumed as negative deltas; level raised 0 → 1.
    assert deltas.await_args.args[2] == {"iron": -25, "stone": -15}
    assert lvl.await_args.args[:4] == (1, 99, "forge", 1)


@pytest.mark.asyncio
async def test_build_forge_insufficient_materials():
    with (
        patch(f"{_WF}.db.get_structures", new_callable=AsyncMock, return_value={}),
        patch(
            f"{_WF}.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"iron": 1},  # short
        ),
    ):
        result = await mining_workflow.build_structure(1, 99, "forge")
    assert result.ok is False
    assert "short on materials" in result.message


@pytest.mark.asyncio
async def test_build_forge_insufficient_coins(_null_txn):
    with (
        patch(f"{_WF}.db.get_structures", new_callable=AsyncMock, return_value={}),
        patch(
            f"{_WF}.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"iron": 50, "stone": 50},
        ),
        patch(
            f"{_WF}.economy_service.debit_in_txn",
            new_callable=AsyncMock,
            side_effect=InsufficientFundsError(),
        ),
        patch(f"{_WF}.db.get_coins", new_callable=AsyncMock, return_value=10),
    ):
        result = await mining_workflow.build_structure(1, 99, "forge")
    assert result.ok is False
    assert "3000" in result.message.replace(",", "")


@pytest.mark.asyncio
async def test_build_forge_maxed():
    with patch(
        f"{_WF}.db.get_structures",
        new_callable=AsyncMock,
        return_value={"forge": 2},  # already at MAX_FORGE_LEVEL
    ):
        result = await mining_workflow.build_structure(1, 99, "forge")
    assert result.ok is False
    assert "maximum level" in result.message


@pytest.mark.asyncio
async def test_build_unknown_structure():
    result = await mining_workflow.build_structure(1, 99, "spaceport")
    assert result.ok is False
    assert "isn't a buildable structure" in result.message


@pytest.mark.asyncio
async def test_build_tide_pool_consumes_coral_and_reports_the_bonus(_null_txn):
    """The Tide Pool routes through the same audited build seam: coral consumed
    as a negative delta + level raised, with the fishing-bonus reward line."""
    with (
        patch(f"{_WF}.db.get_structures", new_callable=AsyncMock, return_value={}),
        patch(
            f"{_WF}.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"coral": 20},
        ),
        patch(
            f"{_WF}.economy_service.debit_in_txn",
            new_callable=AsyncMock,
            return_value=8_500,
        ),
        patch(f"{_WF}.db.apply_inventory_deltas", new_callable=AsyncMock) as deltas,
        patch(f"{_WF}.db.set_structure_level", new_callable=AsyncMock) as lvl,
        patch(f"{_WF}._emit_balance", new_callable=AsyncMock),
    ):
        result = await mining_workflow.build_structure(1, 99, "tide_pool")
    assert result.ok is True
    assert "Reef Pool" in result.message
    assert "+4%" in result.message  # the level-1 rarity-pull bonus reward line
    # Coral consumed as a negative delta; level raised 0 → 1.
    assert deltas.await_args.args[2] == {"coral": -3}
    assert lvl.await_args.args[:4] == (1, 99, "tide_pool", 1)


@pytest.mark.asyncio
async def test_build_dock_consumes_coral_and_wood_and_reports_the_bonus(_null_txn):
    """The Dock routes through the same audited build seam: coral + wood consumed
    as negative deltas + level raised, with the bite-speed reward line."""
    with (
        patch(f"{_WF}.db.get_structures", new_callable=AsyncMock, return_value={}),
        patch(
            f"{_WF}.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"coral": 10, "wood": 40},
        ),
        patch(
            f"{_WF}.economy_service.debit_in_txn",
            new_callable=AsyncMock,
            return_value=6_000,
        ),
        patch(f"{_WF}.db.apply_inventory_deltas", new_callable=AsyncMock) as deltas,
        patch(f"{_WF}.db.set_structure_level", new_callable=AsyncMock) as lvl,
        patch(f"{_WF}._emit_balance", new_callable=AsyncMock),
    ):
        result = await mining_workflow.build_structure(1, 99, "dock")
    assert result.ok is True
    assert "Fishing Dock" in result.message
    assert "6%" in result.message  # the level-1 bite-speed reward line
    # Both materials consumed as negative deltas; level raised 0 → 1.
    assert deltas.await_args.args[2] == {"coral": -2, "wood": -15}
    assert lvl.await_args.args[:4] == (1, 99, "dock", 1)
