"""fishing_workflow charm layer — the fish→charm craft path (S1, follow-up to #1504).

``craft_charm`` is the non-coin earn path for the three CHARM-slot fishing charms:
an inventory-only conversion (mirrors ``craft_bait``) that debits caught fish
(smallest-first, via the shared ``_plan_fish_spend`` planner) and grants one charm
into the mining inventory in ONE transaction. No coins, no audit, no external call.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import fishing_workflow as wf
from utils.fishing import gear as fishing_gear

# fish.json size ranks: minnow=1, guppy=2, sardine=3, anchovy=4 … trout=8.
_FISHING_CHARM = "fishing charm"  # recipe: 8 fish, size ≤ 8


# ---------------------------------------------------------------------------
# _plan_fish_spend works for charm recipes too (shared planner / Protocol)
# ---------------------------------------------------------------------------


def test_plan_fish_spend_accepts_a_charm_recipe():
    recipe = fishing_gear.charm_recipe(_FISHING_CHARM)
    inv = {"minnow": 20, "trout": 5}  # minnow rank 1, trout rank 8 (both ≤ 8)
    spend = wf._plan_fish_spend(inv, recipe)
    assert spend == {"minnow": 8}  # smallest-first fills the 8-fish recipe


# ---------------------------------------------------------------------------
# craft_charm — the inventory→charm conversion (catch→charm loop)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_craft_charm_debits_fish_and_grants_one_charm():
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    with (
        patch.object(
            wf.db,
            "get_mining_inventory",
            AsyncMock(return_value={"minnow": 20}),
        ),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "apply_inventory_deltas", AsyncMock()) as deltas,
        patch.object(wf.economy_service, "debit_in_txn", AsyncMock()) as debit,
    ):
        result = await wf.craft_charm(99, 1, _FISHING_CHARM)

    assert result.success is True
    assert result.charm == _FISHING_CHARM
    # consumed 8 minnow AND granted +1 charm — both in one delta map, no coins.
    deltas.assert_awaited_once_with(
        "99", 1, {"minnow": -8, _FISHING_CHARM: 1}, conn=sentinel_conn
    )
    debit.assert_not_awaited()


@pytest.mark.asyncio
async def test_craft_charm_is_case_insensitive_in_the_charm_name():
    @asynccontextmanager
    async def _ctx():
        yield MagicMock()

    with (
        patch.object(
            wf.db, "get_mining_inventory", AsyncMock(return_value={"minnow": 20})
        ),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "apply_inventory_deltas", AsyncMock()),
    ):
        result = await wf.craft_charm(99, 1, "Fishing Charm")

    assert result.success is True
    assert result.charm == _FISHING_CHARM


@pytest.mark.asyncio
async def test_craft_charm_without_enough_fish_writes_nothing():
    with (
        patch.object(
            wf.db,
            "get_mining_inventory",
            AsyncMock(return_value={"minnow": 3}),  # short of the 8 needed
        ),
        patch.object(wf.db, "apply_inventory_deltas", AsyncMock()) as deltas,
    ):
        result = await wf.craft_charm(99, 1, _FISHING_CHARM)

    assert result.success is False
    deltas.assert_not_awaited()


@pytest.mark.asyncio
async def test_craft_charm_ignores_oversize_fish_for_a_capped_recipe():
    # The fishing charm caps eligibility at size ≤ 8; a hold of only rank-21 fish
    # (the largest species) cannot craft it even though the count is plentiful.
    big = next(s.name for s in wf.fish_mod.SPECIES if s.size_rank == 21)
    with (
        patch.object(
            wf.db, "get_mining_inventory", AsyncMock(return_value={big: 50})
        ),
        patch.object(wf.db, "apply_inventory_deltas", AsyncMock()) as deltas,
    ):
        result = await wf.craft_charm(99, 1, _FISHING_CHARM)

    assert result.success is False
    deltas.assert_not_awaited()


@pytest.mark.asyncio
async def test_craft_charm_rejects_an_uncraftable_or_unknown_charm():
    with (
        patch.object(wf.db, "get_mining_inventory", AsyncMock()) as inv,
        patch.object(wf.db, "apply_inventory_deltas", AsyncMock()) as deltas,
    ):
        lucky = await wf.craft_charm(99, 1, "lucky charm")  # a charm, no fish recipe
        nope = await wf.craft_charm(99, 1, "nonexistent")

    assert lucky.success is False and nope.success is False
    inv.assert_not_awaited()  # bails before reading inventory
    deltas.assert_not_awaited()
