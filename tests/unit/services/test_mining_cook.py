"""mining_workflow.cook + the fish-as-food bridge (2026-06-22, owner decision).

Pins: cooking is gated on a built campfire, only real fish cook, the raw fish is
consumed and a generic ``cooked fish`` granted (both in one transaction), and the
catalog/structure facts the feature relies on (fish are sellable RESOURCEs, the
campfire is a buildable structure, cooked fish refills energy).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from services import mining_workflow
from utils.mining import energy, items, structures


@pytest.fixture
def _null_txn():
    @asynccontextmanager
    async def _txn():
        yield MagicMock(name="conn")

    with patch("services.mining_workflow.db.transaction", _txn):
        yield


# --- catalog / structure facts the feature relies on -------------------------


def test_caught_fish_are_sellable_resources():
    """Every fishing species is a catalogued, sellable RESOURCE tagged 'fish'."""
    from utils.fishing.fish import SPECIES
    from utils.mining import market

    assert SPECIES, "fish catalog should be non-empty"
    for s in SPECIES:
        assert items.is_fish(s.name)
        assert items.classify(s.name) is items.ItemKind.RESOURCE
        assert market.sell_price(s.name) is not None and market.sell_price(s.name) >= 1


def test_campfire_is_a_buildable_structure_that_gates_cooking():
    assert structures.is_structure("campfire")
    assert structures.build_cost(structures.CAMPFIRE, 0) is not None
    assert not structures.cooking_unlocked(0)
    assert structures.cooking_unlocked(1)


def test_cooked_fish_is_food_that_refills_energy():
    assert items.classify("cooked fish") is items.ItemKind.CONSUMABLE
    assert energy.restore_value("cooked fish") == energy.RESTORE_VALUES["cooked fish"]


# --- cook() behaviour --------------------------------------------------------


@pytest.mark.asyncio
async def test_cook_requires_a_built_campfire(_null_txn):
    update = AsyncMock()
    with patch.multiple(
        "services.mining_workflow.db",
        get_structures=AsyncMock(return_value={}),  # no campfire
        get_mining_inventory=AsyncMock(return_value={"minnow": 3}),
        update_mining_item=update,
    ):
        result = await mining_workflow.cook(7, 99, "minnow")
    assert result.ok is False
    assert "campfire" in result.message.lower()
    update.assert_not_awaited()


@pytest.mark.asyncio
async def test_cook_rejects_non_fish(_null_txn):
    with patch.multiple(
        "services.mining_workflow.db",
        get_structures=AsyncMock(return_value={structures.CAMPFIRE: 1}),
        get_mining_inventory=AsyncMock(return_value={"stone": 5}),
        update_mining_item=AsyncMock(),
    ):
        result = await mining_workflow.cook(7, 99, "stone")
    assert result.ok is False
    assert "fish" in result.message.lower()


@pytest.mark.asyncio
async def test_cook_needs_enough_fish(_null_txn):
    with patch.multiple(
        "services.mining_workflow.db",
        get_structures=AsyncMock(return_value={structures.CAMPFIRE: 1}),
        get_mining_inventory=AsyncMock(return_value={"minnow": 1}),
        update_mining_item=AsyncMock(),
    ):
        result = await mining_workflow.cook(7, 99, "minnow", qty=3)
    assert result.ok is False


@pytest.mark.asyncio
async def test_cook_consumes_fish_and_grants_cooked_fish(_null_txn):
    update = AsyncMock()
    with patch.multiple(
        "services.mining_workflow.db",
        get_structures=AsyncMock(return_value={structures.CAMPFIRE: 1}),
        get_mining_inventory=AsyncMock(return_value={"minnow": 5}),
        update_mining_item=update,
    ):
        result = await mining_workflow.cook(7, 99, "minnow", qty=2)
    assert result.ok is True
    # raw fish consumed, cooked fish granted — both on the txn conn.
    update.assert_any_await("7", 99, "minnow", -2, conn=ANY)
    update.assert_any_await("7", 99, mining_workflow.COOKED_FISH, 2, conn=ANY)
