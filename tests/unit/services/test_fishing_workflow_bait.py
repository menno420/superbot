"""fishing_workflow bait layer — purchase coin-sink + per-cast consume (Q-0175 §4).

The bait is the *consumable* how-well knob: ``buy_bait`` is an audited coin sink
(mirrors ``buy_rod``), and ``begin_cast`` spends one charge per cast and compounds
the bait's ``rarity_pull`` onto the rod's before rolling the catch.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import economy_service
from services import fishing_workflow as wf
from utils.fishing import bait as bait_mod
from utils.fishing.fish import Catch, FishSpecies

_CATCH = Catch(species=FishSpecies("trout", 8, "🐠"))
_WORM = bait_mod.bait_by_key("worm")
_LURE = bait_mod.bait_by_key("lure")


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


def _rarity_recorder(seen: list[float]):
    def _roll(level, rng=None, *, rarity_pull=1.0):
        seen.append(rarity_pull)
        return _CATCH

    return _roll


@pytest.mark.asyncio
async def test_begin_cast_consumes_a_bait_charge_and_compounds_rarity():
    seen: list[float] = []
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),  # starter, pull 1.0
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("worm", 2))),
        patch.object(wf, "roll_catch", _rarity_recorder(seen)),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()),
        patch.object(wf.db, "set_active_bait", AsyncMock()) as set_bait,
        patch.object(wf.db, "clear_active_bait", AsyncMock()) as clear_bait,
    ):
        start = await wf.begin_cast(99, 1)

    assert start.ok is True
    assert start.bait_used is _WORM
    assert start.bait_charges_left == 1  # spent one of the two
    assert seen == [pytest.approx(_WORM.rarity_pull)]  # 1.0 (rod) × worm pull
    set_bait.assert_awaited_once_with(99, 1, "worm", 1)
    clear_bait.assert_not_awaited()


@pytest.mark.asyncio
async def test_begin_cast_clears_bait_when_the_last_charge_is_spent():
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("worm", 1))),
        patch.object(wf, "roll_catch", lambda level, rng=None, *, rarity_pull=1.0: _CATCH),
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
    seen: list[float] = []
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(wf, "roll_catch", _rarity_recorder(seen)),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()),
        patch.object(wf.db, "set_active_bait", AsyncMock()) as set_bait,
        patch.object(wf.db, "clear_active_bait", AsyncMock()) as clear_bait,
    ):
        start = await wf.begin_cast(99, 1)

    assert start.bait_used is None
    assert seen == [pytest.approx(1.0)]  # bare starter, no bait
    set_bait.assert_not_awaited()
    clear_bait.assert_not_awaited()
