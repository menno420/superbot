"""fishing_workflow rod-craft layer — the fish→rod craft path (S1, follow-up to #1508).

``craft_rod`` is the non-coin earn path for the rod ladder: an inventory-only
conversion (mirrors ``craft_charm``) that debits caught fish (smallest-first, via
the shared ``_plan_fish_spend`` planner) and raises the owned rod tier by one in
ONE transaction. Like ``buy_rod`` it crafts the *next* tier from the one you own.
No coins, no audit, no external call.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import fishing_workflow as wf
from utils.fishing import rods as rods_mod

# fish.json size ranks: minnow=1 … (recipe into tier 1 = 10 fish, size ≤ 6).


# ---------------------------------------------------------------------------
# _plan_fish_spend works for rod recipes too (shared planner / Protocol)
# ---------------------------------------------------------------------------


def test_plan_fish_spend_accepts_a_rod_recipe():
    recipe = rods_mod.rod_recipe(1)  # 10 fish, size ≤ 6
    inv = {"minnow": 20, "trout": 5}  # minnow rank 1 (≤ 6), trout rank 8 (> 6)
    spend = wf._plan_fish_spend(inv, recipe)
    assert spend == {"minnow": 10}  # smallest-first fills the 10-fish recipe


# ---------------------------------------------------------------------------
# eligible_fish_total — the live-progress readout (rod recipe browser)
# ---------------------------------------------------------------------------


def test_eligible_fish_total_counts_only_eligible_species():
    recipe = rods_mod.rod_recipe(1)  # 10 fish, size ≤ 6
    inv = {"minnow": 4, "trout": 50}  # minnow rank 1 (≤ 6), trout rank 8 (> 6)
    assert wf.eligible_fish_total(inv, recipe) == 4  # trout never counts


def test_eligible_fish_total_sums_multiple_eligible_species():
    recipe = rods_mod.rod_recipe(1)
    inv = {"minnow": 4, "perch": 3}  # both rank ≤ 6
    assert wf.eligible_fish_total(inv, recipe) == 7


def test_eligible_fish_total_never_gates_on_the_requirement():
    # Unlike _plan_fish_spend (which returns None when short), the progress
    # readout reports the partial total even when it's below recipe.fish_count.
    recipe = rods_mod.rod_recipe(1)  # needs 10
    inv = {"minnow": 3}
    assert wf.eligible_fish_total(inv, recipe) == 3
    assert wf._plan_fish_spend(inv, recipe) is None


def test_eligible_fish_total_ignores_zero_and_unknown_entries():
    recipe = rods_mod.rod_recipe(1)
    inv = {"minnow": 0, "not-a-real-fish": 99}
    assert wf.eligible_fish_total(inv, recipe) == 0


# ---------------------------------------------------------------------------
# craft_rod — the inventory→tier conversion (catch→rod loop)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_craft_rod_debits_fish_and_raises_the_tier_by_one():
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    with (
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(
            wf.db, "get_mining_inventory", AsyncMock(return_value={"minnow": 20})
        ),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "apply_inventory_deltas", AsyncMock()) as deltas,
        patch.object(wf.db, "set_rod_tier", AsyncMock()) as set_tier,
        patch.object(wf.economy_service, "debit_in_txn", AsyncMock()) as debit,
    ):
        result = await wf.craft_rod(99, 1)

    assert result.success is True
    assert result.tier == 1
    # consumed 10 minnow, raised the tier — no coins debited.
    deltas.assert_awaited_once_with("99", 1, {"minnow": -10}, conn=sentinel_conn)
    set_tier.assert_awaited_once_with(99, 1, 1, conn=sentinel_conn)
    debit.assert_not_awaited()


@pytest.mark.asyncio
async def test_craft_rod_crafts_the_next_tier_from_the_one_owned():
    @asynccontextmanager
    async def _ctx():
        yield MagicMock()

    with (
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=1)),  # owns bronze
        patch.object(
            wf.db, "get_mining_inventory", AsyncMock(return_value={"minnow": 50})
        ),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "apply_inventory_deltas", AsyncMock()),
        patch.object(wf.db, "set_rod_tier", AsyncMock()) as set_tier,
    ):
        result = await wf.craft_rod(99, 1)

    assert result.success is True and result.tier == 2  # bronze → silver
    set_tier.assert_awaited_once()
    assert set_tier.await_args.args[2] == 2


@pytest.mark.asyncio
async def test_craft_rod_without_enough_fish_writes_nothing():
    with (
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(
            wf.db,
            "get_mining_inventory",
            AsyncMock(return_value={"minnow": 3}),  # short of the 10 needed
        ),
        patch.object(wf.db, "apply_inventory_deltas", AsyncMock()) as deltas,
        patch.object(wf.db, "set_rod_tier", AsyncMock()) as set_tier,
    ):
        result = await wf.craft_rod(99, 1)

    assert result.success is False
    assert result.tier == 0  # unchanged
    deltas.assert_not_awaited()
    set_tier.assert_not_awaited()


@pytest.mark.asyncio
async def test_craft_rod_at_the_top_tier_is_a_no_op():
    with (
        patch.object(
            wf.db, "get_rod_tier", AsyncMock(return_value=rods_mod.MAX_TIER)
        ),
        patch.object(wf.db, "get_mining_inventory", AsyncMock()) as inv,
        patch.object(wf.db, "apply_inventory_deltas", AsyncMock()) as deltas,
    ):
        result = await wf.craft_rod(99, 1)

    assert result.success is False
    assert result.tier == rods_mod.MAX_TIER
    inv.assert_not_awaited()  # bails before reading inventory
    deltas.assert_not_awaited()


@pytest.mark.asyncio
async def test_craft_rod_ignores_oversize_fish_for_a_capped_recipe():
    # The tier-1 recipe caps eligibility at size ≤ 6; a hold of only rank-21 fish
    # (the largest species) cannot craft it even though the count is plentiful.
    big = next(s.name for s in wf.fish_mod.SPECIES if s.size_rank == 21)
    with (
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(
            wf.db, "get_mining_inventory", AsyncMock(return_value={big: 50})
        ),
        patch.object(wf.db, "apply_inventory_deltas", AsyncMock()) as deltas,
        patch.object(wf.db, "set_rod_tier", AsyncMock()) as set_tier,
    ):
        result = await wf.craft_rod(99, 1)

    assert result.success is False
    deltas.assert_not_awaited()
    set_tier.assert_not_awaited()
