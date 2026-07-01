"""fishing_workflow bait layer — purchase coin-sink + per-cast consume (Q-0175 §4).

The bait is the *consumable* how-well knob: ``buy_bait`` is an audited coin sink
(mirrors ``buy_rod``), and ``begin_cast`` spends one charge per cast and compounds
the bait's ``rarity_pull`` onto the rod's before rolling the catch.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from tests.unit.services._fishing_helpers import (
    CATCH,
    fake_roll_catch,
    recording_roll_catch,
)

from services import economy_service
from services import fishing_workflow as wf
from utils.fishing import bait as bait_mod
from utils.fishing import rods as rods_mod

_CATCH = CATCH  # the shared sentinel the helpers return (identity asserts)
_WORM = bait_mod.bait_by_key("worm")
_LURE = bait_mod.bait_by_key("lure")
_SPINNER = bait_mod.bait_by_key("spinner")  # a pure speed bait (bite_speed < 1)
_FEAST = bait_mod.bait_by_key("feast")  # the premium combo — pearl-craft only
_FEAST_PEARLS = bait_mod.pearl_recipe("feast")  # pearls per Royal Feast pack


@pytest.fixture(autouse=True)
def _no_fishing_gear():
    """Default the cast's gear + structure reads (the 4th/5th knobs) to empty so the
    bait-layer assertions stay rod×bait-only — fishing gear is exercised in
    ``test_fishing_workflow.py``. Tests that need gear can re-patch these."""
    with (
        patch.object(wf.db, "get_equipment", AsyncMock(return_value={})),
        patch.object(wf.db, "get_skills", AsyncMock(return_value={})),
        patch.object(wf.db, "get_structures", AsyncMock(return_value={})),
    ):
        yield


# ---------------------------------------------------------------------------
# get_active_bait — key → Bait resolution
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_active_bait_resolves_the_loaded_pack():
    with patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("worm", 5))):
        bait, charges = await wf.get_active_bait(99, 1)
    assert bait is _WORM
    assert charges == 5


@pytest.mark.asyncio
async def test_get_active_bait_is_none_for_zero_charges_or_unknown_key():
    with patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("worm", 0))):
        assert await wf.get_active_bait(99, 1) == (None, 0)
    with patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("gone", 4))):
        assert await wf.get_active_bait(99, 1) == (None, 0)


# ---------------------------------------------------------------------------
# buy_bait — the audited coin-sink purchase
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_buy_bait_debits_coins_and_loads_a_fresh_pack():
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    with (
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(
            wf.economy_service,
            "debit_in_txn",
            AsyncMock(return_value=900),
        ) as debit,
        patch.object(wf.db, "set_active_bait", AsyncMock()) as set_bait,
        patch.object(wf.bus, "emit", AsyncMock()) as emit,
    ):
        result = await wf.buy_bait(99, 1, "worm")

    assert result.success is True
    assert result.bait is _WORM
    assert result.charges == _WORM.charges
    args, kwargs = debit.await_args
    assert args[0] is sentinel_conn
    assert _WORM.price in args
    assert kwargs["reason"] == wf.BAIT_PURCHASE_REASON
    set_bait.assert_awaited_once_with(99, 1, "worm", _WORM.charges, conn=sentinel_conn)
    emit.assert_awaited_once()  # balance event after commit


@pytest.mark.asyncio
async def test_buy_bait_stacks_charges_for_the_same_bait():
    @asynccontextmanager
    async def _ctx():
        yield MagicMock()

    with (
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("worm", 3))),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.economy_service, "debit_in_txn", AsyncMock(return_value=10)),
        patch.object(wf.db, "set_active_bait", AsyncMock()) as set_bait,
        patch.object(wf.bus, "emit", AsyncMock()),
    ):
        result = await wf.buy_bait(99, 1, "worm")

    assert result.charges == 3 + _WORM.charges  # stacked, not replaced
    _, _, key, charges = set_bait.await_args.args
    assert (key, charges) == ("worm", 3 + _WORM.charges)


@pytest.mark.asyncio
async def test_buy_bait_replaces_a_different_loaded_bait():
    @asynccontextmanager
    async def _ctx():
        yield MagicMock()

    with (
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("worm", 3))),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.economy_service, "debit_in_txn", AsyncMock(return_value=10)),
        patch.object(wf.db, "set_active_bait", AsyncMock()) as set_bait,
        patch.object(wf.bus, "emit", AsyncMock()),
    ):
        result = await wf.buy_bait(99, 1, "lure")

    assert result.bait is _LURE
    assert result.charges == _LURE.charges  # fresh pack, old worm charges dropped
    _, _, key, charges = set_bait.await_args.args
    assert (key, charges) == ("lure", _LURE.charges)


@pytest.mark.asyncio
async def test_buy_bait_with_insufficient_funds_loads_nothing():
    @asynccontextmanager
    async def _ctx():
        yield MagicMock()

    with (
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(
            wf.economy_service,
            "debit_in_txn",
            AsyncMock(side_effect=economy_service.InsufficientFundsError("broke")),
        ),
        patch.object(wf.db, "set_active_bait", AsyncMock()) as set_bait,
        patch.object(wf.db, "get_coins", AsyncMock(return_value=10)),
        patch.object(wf.bus, "emit", AsyncMock()) as emit,
    ):
        result = await wf.buy_bait(99, 1, "worm")

    assert result.success is False
    set_bait.assert_not_awaited()  # rolled back with the transaction
    emit.assert_not_awaited()


@pytest.mark.asyncio
async def test_buy_bait_rejects_an_unknown_key():
    with patch.object(wf.economy_service, "debit_in_txn", AsyncMock()) as debit:
        result = await wf.buy_bait(99, 1, "nonexistent")
    assert result.success is False
    debit.assert_not_awaited()  # never touches the economy for a phantom bait


# ---------------------------------------------------------------------------
# begin_cast — per-cast bait consume + rarity compounding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_begin_cast_consumes_a_bait_charge_and_compounds_rarity():
    rec: dict = {}
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="shore")),
        patch.object(wf.weather_mod, "current_weather", lambda: wf.weather_mod.CONDITIONS[0]),
        patch.object(
            wf.db, "get_rod_tier", AsyncMock(return_value=0)
        ),  # starter, pull 1.0
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("worm", 2))),
        patch.object(wf, "roll_catch", recording_roll_catch(rec)),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()),
        patch.object(wf.db, "set_active_bait", AsyncMock()) as set_bait,
        patch.object(wf.db, "clear_active_bait", AsyncMock()) as clear_bait,
    ):
        start = await wf.begin_cast(99, 1)

    assert start.ok is True
    assert start.bait_used is _WORM
    assert start.bait_charges_left == 1  # spent one of the two
    assert rec["rarity_pull"] == pytest.approx(_WORM.rarity_pull)  # 1.0 (rod) × worm pull
    set_bait.assert_awaited_once_with(99, 1, "worm", 1)
    clear_bait.assert_not_awaited()


@pytest.mark.asyncio
async def test_begin_cast_clears_bait_when_the_last_charge_is_spent():
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="shore")),
        patch.object(wf.weather_mod, "current_weather", lambda: wf.weather_mod.CONDITIONS[0]),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("worm", 1))),
        patch.object(
            wf, "roll_catch", fake_roll_catch()
        ),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()),
        patch.object(wf.db, "set_active_bait", AsyncMock()) as set_bait,
        patch.object(wf.db, "clear_active_bait", AsyncMock()) as clear_bait,
    ):
        start = await wf.begin_cast(99, 1)

    assert start.bait_charges_left == 0
    clear_bait.assert_awaited_once_with(99, 1)  # pack ran out
    set_bait.assert_not_awaited()


@pytest.mark.asyncio
async def test_begin_cast_without_bait_uses_only_the_rod_pull():
    rec: dict = {}
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="shore")),
        patch.object(wf.weather_mod, "current_weather", lambda: wf.weather_mod.CONDITIONS[0]),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(wf, "roll_catch", recording_roll_catch(rec)),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()),
        patch.object(wf.db, "set_active_bait", AsyncMock()) as set_bait,
        patch.object(wf.db, "clear_active_bait", AsyncMock()) as clear_bait,
    ):
        start = await wf.begin_cast(99, 1)

    assert start.bait_used is None
    assert rec["rarity_pull"] == pytest.approx(1.0)  # bare starter, no bait
    set_bait.assert_not_awaited()
    clear_bait.assert_not_awaited()


# ---------------------------------------------------------------------------
# begin_cast — bite-speed knob compounding (rod × bait), exposed on CastStart
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_begin_cast_compounds_bite_speed_from_rod_and_bait():
    # Gold rod (tier 3, bite_speed 0.80) + a pure speed bait → product on CastStart.
    gold = rods_mod.rod_for_tier(3)
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="shore")),
        patch.object(wf.weather_mod, "current_weather", lambda: wf.weather_mod.CONDITIONS[0]),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=3)),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("spinner", 2))),
        patch.object(
            wf, "roll_catch", fake_roll_catch()
        ),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()),
        patch.object(wf.db, "set_active_bait", AsyncMock()),
        patch.object(wf.db, "clear_active_bait", AsyncMock()),
    ):
        start = await wf.begin_cast(99, 1)

    assert start.bait_used is _SPINNER
    assert start.effective_bite_speed == pytest.approx(
        gold.bite_speed * _SPINNER.bite_speed
    )


@pytest.mark.asyncio
async def test_begin_cast_bite_speed_is_rod_only_without_bait():
    gold = rods_mod.rod_for_tier(3)
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="shore")),
        patch.object(wf.weather_mod, "current_weather", lambda: wf.weather_mod.CONDITIONS[0]),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=3)),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(
            wf, "roll_catch", fake_roll_catch()
        ),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()),
        patch.object(wf.db, "set_active_bait", AsyncMock()),
        patch.object(wf.db, "clear_active_bait", AsyncMock()),
    ):
        start = await wf.begin_cast(99, 1)

    assert start.effective_bite_speed == pytest.approx(gold.bite_speed)  # rod only


# ---------------------------------------------------------------------------
# _plan_fish_spend — choose which eligible fish to consume (smallest-first)
# ---------------------------------------------------------------------------
# fish.json size ranks: minnow=1, guppy=2, sardine=3, anchovy=4 … trout=8.
_WORM_RECIPE = bait_mod.craft_recipe("worm")  # 3 fish, size ≤ 3


def test_plan_fish_spend_takes_smallest_eligible_first():
    inv = {"sardine": 5, "minnow": 5, "guppy": 5, "trout": 5}  # trout is rank 8 (>3)
    spend = wf._plan_fish_spend(inv, _WORM_RECIPE)
    assert spend == {"minnow": 3}  # smallest rank fills the recipe, bigger kept


def test_plan_fish_spend_spreads_across_ranks_when_needed():
    inv = {"minnow": 2, "guppy": 5}  # need 3 small fish; only 2 minnow
    spend = wf._plan_fish_spend(inv, _WORM_RECIPE)
    assert spend == {"minnow": 2, "guppy": 1}  # smallest first, then next rank


def test_plan_fish_spend_returns_none_without_enough_eligible_fish():
    # 10 trout (rank 8) are all too big for the size-≤-3 recipe → no plan.
    assert wf._plan_fish_spend({"trout": 10}, _WORM_RECIPE) is None
    assert wf._plan_fish_spend({"minnow": 2}, _WORM_RECIPE) is None  # short by one
    assert wf._plan_fish_spend({}, _WORM_RECIPE) is None
    # non-fish inventory items never count as ingredients
    assert wf._plan_fish_spend({"copper ore": 50}, _WORM_RECIPE) is None


# ---------------------------------------------------------------------------
# craft_bait — the inventory→bait conversion (catch→bait loop)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_craft_bait_debits_fish_and_loads_a_fresh_pack():
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    with (
        patch.object(
            wf.db,
            "get_mining_inventory",
            AsyncMock(return_value={"minnow": 5}),
        ),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "apply_inventory_deltas", AsyncMock()) as deltas,
        patch.object(wf.db, "set_active_bait", AsyncMock()) as set_bait,
        patch.object(wf.economy_service, "debit_in_txn", AsyncMock()) as debit,
    ):
        result = await wf.craft_bait(99, 1, "worm")

    assert result.success is True
    assert result.bait is _WORM
    assert result.charges == _WORM.charges
    # consumed 3 minnow (the recipe), no coins ever touched
    deltas.assert_awaited_once_with("99", 1, {"minnow": -3}, conn=sentinel_conn)
    set_bait.assert_awaited_once_with(99, 1, "worm", _WORM.charges, conn=sentinel_conn)
    debit.assert_not_awaited()


@pytest.mark.asyncio
async def test_craft_bait_stacks_charges_for_the_same_bait():
    @asynccontextmanager
    async def _ctx():
        yield MagicMock()

    with (
        patch.object(
            wf.db,
            "get_mining_inventory",
            AsyncMock(return_value={"minnow": 9}),
        ),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("worm", 4))),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "apply_inventory_deltas", AsyncMock()),
        patch.object(wf.db, "set_active_bait", AsyncMock()) as set_bait,
    ):
        result = await wf.craft_bait(99, 1, "worm")

    assert result.charges == 4 + _WORM.charges  # stacked onto the loaded worm
    _, _, key, charges = set_bait.await_args.args
    assert (key, charges) == ("worm", 4 + _WORM.charges)


@pytest.mark.asyncio
async def test_craft_bait_replaces_a_different_loaded_bait():
    @asynccontextmanager
    async def _ctx():
        yield MagicMock()

    with (
        patch.object(
            wf.db,
            "get_mining_inventory",
            AsyncMock(return_value={"minnow": 9}),
        ),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("lure", 5))),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "apply_inventory_deltas", AsyncMock()),
        patch.object(wf.db, "set_active_bait", AsyncMock()) as set_bait,
    ):
        result = await wf.craft_bait(99, 1, "worm")

    assert result.bait is _WORM
    assert result.charges == _WORM.charges  # fresh pack, old lure charges dropped


@pytest.mark.asyncio
async def test_craft_bait_without_enough_fish_writes_nothing():
    with (
        patch.object(
            wf.db,
            "get_mining_inventory",
            AsyncMock(return_value={"trout": 10}),  # all too big for size ≤ 3
        ),
        patch.object(wf.db, "apply_inventory_deltas", AsyncMock()) as deltas,
        patch.object(wf.db, "set_active_bait", AsyncMock()) as set_bait,
    ):
        result = await wf.craft_bait(99, 1, "worm")

    assert result.success is False
    deltas.assert_not_awaited()
    set_bait.assert_not_awaited()


@pytest.mark.asyncio
async def test_craft_bait_rejects_an_uncraftable_or_unknown_bait():
    with (
        patch.object(wf.db, "get_mining_inventory", AsyncMock()) as inv,
        patch.object(wf.db, "apply_inventory_deltas", AsyncMock()) as deltas,
    ):
        feast = await wf.craft_bait(99, 1, "feast")  # premium = coin-only
        nope = await wf.craft_bait(99, 1, "nonexistent")

    assert feast.success is False and nope.success is False
    inv.assert_not_awaited()  # bails before reading inventory
    deltas.assert_not_awaited()


# ---------------------------------------------------------------------------
# craft_pearl_bait — the rare-material → premium-bait conversion (pearl sink)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_craft_pearl_bait_debits_pearls_and_loads_the_premium_pack():
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    with (
        patch.object(
            wf.db,
            "get_mining_inventory",
            AsyncMock(return_value={wf.PEARL_ITEM: _FEAST_PEARLS + 1}),
        ),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "update_mining_item", AsyncMock()) as spend,
        patch.object(wf.db, "set_active_bait", AsyncMock()) as set_bait,
        patch.object(wf.economy_service, "debit_in_txn", AsyncMock()) as debit,
    ):
        result = await wf.craft_pearl_bait(99, 1, "feast")

    assert result.success is True
    assert result.bait is _FEAST
    assert result.charges == _FEAST.charges
    # exactly the recipe's pearls were debited, no coins ever touched
    spend.assert_awaited_once_with(
        "99", 1, wf.PEARL_ITEM, -_FEAST_PEARLS, conn=sentinel_conn
    )
    set_bait.assert_awaited_once_with(99, 1, "feast", _FEAST.charges, conn=sentinel_conn)
    debit.assert_not_awaited()


@pytest.mark.asyncio
async def test_craft_pearl_bait_stacks_charges_for_the_same_bait():
    @asynccontextmanager
    async def _ctx():
        yield MagicMock()

    with (
        patch.object(
            wf.db,
            "get_mining_inventory",
            AsyncMock(return_value={wf.PEARL_ITEM: 10}),
        ),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("feast", 3))),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "update_mining_item", AsyncMock()),
        patch.object(wf.db, "set_active_bait", AsyncMock()) as set_bait,
    ):
        result = await wf.craft_pearl_bait(99, 1, "feast")

    assert result.charges == 3 + _FEAST.charges  # stacked onto the loaded feast
    _, _, key, charges = set_bait.await_args.args
    assert (key, charges) == ("feast", 3 + _FEAST.charges)


@pytest.mark.asyncio
async def test_craft_pearl_bait_without_enough_pearls_writes_nothing():
    with (
        patch.object(
            wf.db,
            "get_mining_inventory",
            AsyncMock(return_value={wf.PEARL_ITEM: _FEAST_PEARLS - 1}),
        ),
        patch.object(wf.db, "update_mining_item", AsyncMock()) as spend,
        patch.object(wf.db, "set_active_bait", AsyncMock()) as set_bait,
    ):
        result = await wf.craft_pearl_bait(99, 1, "feast")

    assert result.success is False
    spend.assert_not_awaited()
    set_bait.assert_not_awaited()


@pytest.mark.asyncio
async def test_craft_pearl_bait_rejects_a_non_pearl_or_unknown_bait():
    with (
        patch.object(wf.db, "get_mining_inventory", AsyncMock()) as inv,
        patch.object(wf.db, "update_mining_item", AsyncMock()) as spend,
    ):
        # a fish-craftable bait has no pearl recipe; neither does a phantom bait
        worm = await wf.craft_pearl_bait(99, 1, "worm")
        nope = await wf.craft_pearl_bait(99, 1, "nonexistent")

    assert worm.success is False and nope.success is False
    inv.assert_not_awaited()  # bails before reading inventory
    spend.assert_not_awaited()
