"""fishing_workflow — level-gated catch, transaction membership, no coins.

The Q-0071 contract: the catch-log write + the xp award run on the SAME
workflow-owned connection, and the xp event emits only after the transaction
exits (= commits). v1 pays no coins (owner Q-0175 — fish value is deferred).
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
from services import game_xp_service
from utils.fishing import MAX_LEVEL, rods
from utils.fishing.fish import FishSpecies


def _txn(sentinel_conn, events):
    @asynccontextmanager
    async def _ctx():
        events.append("txn_enter")
        yield sentinel_conn
        events.append("txn_exit")

    return _ctx


_CATCH = CATCH  # the shared sentinel the helpers return (identity asserts)


def _award(*, game_total, leveled_up=False, level=1, amount=5):
    return game_xp_service.GameXpAward(
        guild_id=1,
        user_id=99,
        game=game_xp_service.GAME_FISHING,
        action="fish",
        amount=amount,
        game_total=game_total,
        shared_total=game_total,
        level=level,
        leveled_up=leveled_up,
    )


# ---------------------------------------------------------------------------
# fishing_level_from_xp — the level curve reuse
# ---------------------------------------------------------------------------


def test_zero_xp_is_fishing_level_one():
    assert wf.fishing_level_from_xp(0) == 1


def test_fishing_level_is_capped_at_max_level():
    assert wf.fishing_level_from_xp(10_000_000) == MAX_LEVEL


def test_fishing_level_is_monotonic_in_xp():
    levels = [wf.fishing_level_from_xp(x) for x in range(0, 3000, 50)]
    assert levels == sorted(levels)


# ---------------------------------------------------------------------------
# fish() — the cast
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_both_legs_on_one_conn_and_emit_after_commit():
    sentinel_conn = MagicMock(name="conn")
    events: list[str] = []

    async def _record(user_id, guild_id, species, weight=0.0, *, conn=None):
        events.append("record")
        assert conn is sentinel_conn
        assert species == "trout"
        return

    async def _award_fn(guild_id, user_id, *, game, action, conn=None, depth=0):
        events.append("award")
        assert conn is sentinel_conn
        assert game == game_xp_service.GAME_FISHING
        return _award(game_total=10)

    async def _grant(user_id, guild_id, item, qty, *, conn=None):
        events.append("grant")
        assert conn is sentinel_conn
        assert item == "trout" and qty == 1  # the caught fish enters the inventory

    with (
        patch.object(wf, "roll_catch", fake_roll_catch()),
        # Force no lucky-double-catch so the single-fish grant qty is deterministic
        # (the bonus is its own seeded path, exercised in its own tests below).
        patch.object(wf, "roll_bonus_catch", lambda *a, **k: False),
        # Force no pearl drop so the only grant is the single fish (the pearl drop
        # is its own seeded path, exercised in its own tests below).
        patch.object(wf, "roll_pearl_drop", lambda *a, **k: False),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 5})),
        patch.object(wf.db, "transaction", _txn(sentinel_conn, events)),
        patch.object(wf.db, "record_catch", AsyncMock(side_effect=_record)),
        patch.object(wf.db, "update_mining_item", AsyncMock(side_effect=_grant)),
        patch.object(wf.game_xp_service, "award", AsyncMock(side_effect=_award_fn)),
        patch.object(wf.game_xp_service, "emit_award_events", AsyncMock()) as emit_xp,
    ):
        result = await wf.fish(99, 1)

    for leg in ("record", "grant", "award"):
        assert events.index(leg) < events.index("txn_exit")
    # XP events emit only after the transaction commits.
    emit_xp.assert_awaited_once()
    # A *catch* pays no coins (only the separate rod purchase touches the
    # economy seam) — the catch flow never debited/credited here.
    assert result.catch is _CATCH


@pytest.mark.asyncio
async def test_crossing_a_fishing_level_flags_unlocked_bigger():
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    # Pre-read xp 50 → level 1; post-award game_total huge → MAX_LEVEL.
    with (
        patch.object(wf, "roll_catch", fake_roll_catch()),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 50})),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "record_catch", AsyncMock()),
        patch.object(wf.db, "update_mining_item", AsyncMock()),
        patch.object(
            wf.game_xp_service,
            "award",
            AsyncMock(return_value=_award(game_total=10_000_000)),
        ),
        patch.object(wf.game_xp_service, "emit_award_events", AsyncMock()),
    ):
        result = await wf.fish(99, 1)

    assert result.unlocked_bigger is True
    assert result.fishing_level == MAX_LEVEL


@pytest.mark.asyncio
async def test_roll_is_gated_by_the_players_current_fishing_level():
    """The roll is called with the level derived from the pre-read fishing xp."""
    sentinel_conn = MagicMock(name="conn")
    rec: dict = {}

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    with (
        patch.object(wf, "roll_catch", recording_roll_catch(rec)),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "record_catch", AsyncMock()),
        patch.object(wf.db, "update_mining_item", AsyncMock()),
        patch.object(
            wf.game_xp_service,
            "award",
            AsyncMock(return_value=_award(game_total=5)),
        ),
        patch.object(wf.game_xp_service, "emit_award_events", AsyncMock()),
    ):
        await wf.fish(99, 1)

    assert rec["level"] == 1  # 0 xp → level 1


@pytest.mark.asyncio
async def test_empty_catalog_writes_nothing():
    with (
        patch.object(wf, "roll_catch", fake_roll_catch(None)),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={})),
        patch.object(wf.db, "record_catch", AsyncMock()) as record,
    ):
        result = await wf.fish(99, 1)

    assert result.catch is None
    record.assert_not_awaited()


# ---------------------------------------------------------------------------
# roll_cast / commit_catch — the minigame split (roll at cast, write on reel)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_roll_cast_reads_the_level_and_rolls_without_writing():
    """The read-only half: a cast rolls a catch but touches no write seam."""
    with (
        patch.object(wf, "roll_catch", fake_roll_catch()),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "record_catch", AsyncMock()) as record,
        patch.object(wf.db, "update_mining_item", AsyncMock()) as grant,
        patch.object(wf.game_xp_service, "award", AsyncMock()) as award,
    ):
        cast = await wf.roll_cast(99, 1)

    assert cast.catch is _CATCH
    assert cast.level_before == 1  # 0 xp → level 1
    record.assert_not_awaited()  # nothing is written until the reel succeeds
    grant.assert_not_awaited()
    award.assert_not_awaited()


@pytest.mark.asyncio
async def test_commit_catch_writes_the_held_cast():
    """The write half: committing a rolled cast runs the audited transaction."""
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    cast = wf.Cast(catch=_CATCH, level_before=1)
    with (
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf, "roll_pearl_drop", lambda *a, **k: False),
        patch.object(wf.db, "record_catch", AsyncMock()) as record,
        patch.object(wf.db, "update_mining_item", AsyncMock()) as grant,
        patch.object(
            wf.game_xp_service,
            "award",
            AsyncMock(return_value=_award(game_total=10)),
        ),
        patch.object(wf.game_xp_service, "emit_award_events", AsyncMock()) as emit,
    ):
        result = await wf.commit_catch(99, 1, cast)

    record.assert_awaited_once()
    grant.assert_awaited_once()
    emit.assert_awaited_once()
    assert result.catch is _CATCH


@pytest.mark.asyncio
async def test_commit_catch_threads_weight_and_flags_a_new_personal_best():
    """The catch's weight reaches record_catch; a heavier-than-prior catch = PB."""
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    heavy = wf.Catch(species=FishSpecies("trout", 8, "🐠"), weight=4.2)
    cast = wf.Cast(catch=heavy, level_before=1)
    with (
        patch.object(wf.db, "transaction", _ctx),
        # Prior best 1.5 kg < this 4.2 kg catch → a new personal best.
        patch.object(wf.db, "record_catch", AsyncMock(return_value=1.5)) as record,
        patch.object(wf.db, "update_mining_item", AsyncMock()),
        patch.object(
            wf.game_xp_service,
            "award",
            AsyncMock(return_value=_award(game_total=10)),
        ),
        patch.object(wf.game_xp_service, "emit_award_events", AsyncMock()),
    ):
        result = await wf.commit_catch(99, 1, cast)

    # The rolled weight is passed positionally to the audited write.
    args, _ = record.await_args
    assert args[3] == 4.2
    assert result.weight == 4.2
    assert result.new_personal_best is True


@pytest.mark.asyncio
async def test_commit_catch_not_a_personal_best_when_lighter_than_prior():
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    light = wf.Catch(species=FishSpecies("trout", 8, "🐠"), weight=0.9)
    cast = wf.Cast(catch=light, level_before=1)
    with (
        patch.object(wf.db, "transaction", _ctx),
        # Prior best 3.0 kg > this 0.9 kg catch → not a record.
        patch.object(wf.db, "record_catch", AsyncMock(return_value=3.0)),
        patch.object(wf.db, "update_mining_item", AsyncMock()),
        patch.object(
            wf.game_xp_service,
            "award",
            AsyncMock(return_value=_award(game_total=10)),
        ),
        patch.object(wf.game_xp_service, "emit_award_events", AsyncMock()),
    ):
        result = await wf.commit_catch(99, 1, cast)

    assert result.new_personal_best is False


@pytest.mark.asyncio
async def test_commit_catch_first_catch_of_a_species_is_a_personal_best():
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    first = wf.Catch(species=FishSpecies("trout", 8, "🐠"), weight=1.1)
    cast = wf.Cast(catch=first, level_before=1)
    with (
        patch.object(wf.db, "transaction", _ctx),
        # No prior row → record_catch returns None → the first catch is a PB.
        patch.object(wf.db, "record_catch", AsyncMock(return_value=None)),
        patch.object(wf.db, "update_mining_item", AsyncMock()),
        patch.object(
            wf.game_xp_service,
            "award",
            AsyncMock(return_value=_award(game_total=10)),
        ),
        patch.object(wf.game_xp_service, "emit_award_events", AsyncMock()),
    ):
        result = await wf.commit_catch(99, 1, cast)

    assert result.new_personal_best is True


@pytest.mark.asyncio
async def test_commit_catch_on_empty_cast_writes_nothing():
    cast = wf.Cast(catch=None, level_before=2)
    with patch.object(wf.db, "record_catch", AsyncMock()) as record:
        result = await wf.commit_catch(99, 1, cast)

    assert result.catch is None
    assert result.fishing_level == 2
    record.assert_not_awaited()


# ---------------------------------------------------------------------------
# commit_catch — the lucky-double-catch bonus (extra craft fodder, PR #1515)
# ---------------------------------------------------------------------------


async def _commit_with_grant(rng, *, double_catch_chance=None):
    """Commit a fixed cast under a forced *rng* and return (result, grant mock).

    *double_catch_chance* overrides the cast's fishery-fixed double-catch chance
    (``None`` = the dataclass default, the base ``BONUS_CATCH_CHANCE``).
    """
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    kw = {} if double_catch_chance is None else {"double_catch_chance": double_catch_chance}
    cast = wf.Cast(catch=_CATCH, level_before=1, **kw)
    with (
        patch.object(wf.db, "transaction", _ctx),
        # Isolate the bonus path from the pearl drop — the fish grant stays the
        # last update_mining_item call this helper inspects (args[3]).
        patch.object(wf, "roll_pearl_drop", lambda *a, **k: False),
        patch.object(wf.db, "record_catch", AsyncMock(return_value=None)),
        patch.object(wf.db, "update_mining_item", AsyncMock()) as grant,
        patch.object(
            wf.game_xp_service,
            "award",
            AsyncMock(return_value=_award(game_total=10)),
        ),
        patch.object(wf.game_xp_service, "emit_award_events", AsyncMock()),
    ):
        result = await wf.commit_catch(99, 1, cast, rng=rng)
    return result, grant


@pytest.mark.asyncio
async def test_commit_catch_grants_two_and_flags_the_bonus_on_a_lucky_reel():
    # rng.random() == 0.0 < BONUS_CATCH_CHANCE → the bonus fires.
    forced = MagicMock()
    forced.random.return_value = 0.0
    result, grant = await _commit_with_grant(forced)

    assert result.bonus_catch is True
    # the inventory grant is 2 of the species; the dex row is still written once.
    args, kwargs = grant.await_args
    assert args[3] == 2


@pytest.mark.asyncio
async def test_commit_catch_grants_one_and_no_bonus_on_an_unlucky_reel():
    # rng.random() == 0.99 ≥ BONUS_CATCH_CHANCE → no bonus, byte-identical path.
    forced = MagicMock()
    forced.random.return_value = 0.99
    result, grant = await _commit_with_grant(forced)

    assert result.bonus_catch is False
    args, _ = grant.await_args
    assert args[3] == 1


@pytest.mark.asyncio
async def test_fishery_raises_the_double_catch_chance_on_commit():
    """A built Fishery lifts ``cast.double_catch_chance`` above the base, so a reel
    that would MISS the base 0.10 chance can still double at the fishery-raised chance."""
    from utils.fishing import rewards

    # A roll just above the base chance but under a Grand Fishery's +0.10 → 0.20.
    forced = MagicMock()
    forced.random.return_value = 0.15
    assert rewards.BONUS_CATCH_CHANCE == 0.10  # 0.15 misses the base…

    # Unbuilt cast (base chance): no double.
    _, base_grant = await _commit_with_grant(forced, double_catch_chance=0.10)
    assert base_grant.await_args.args[3] == 1

    # Grand-Fishery cast (chance 0.20): the same 0.15 roll now doubles.
    _, fishery_grant = await _commit_with_grant(forced, double_catch_chance=0.20)
    assert fishery_grant.await_args.args[3] == 2


# ---------------------------------------------------------------------------
# commit_catch — the pearl rare-material drop (with this PR)
# ---------------------------------------------------------------------------


async def _commit_collecting_grants(rng):
    """Commit a fixed cast under a forced *rng*, returning (result, grant calls)."""
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    cast = wf.Cast(catch=_CATCH, level_before=1)
    with (
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "record_catch", AsyncMock(return_value=None)),
        patch.object(wf.db, "update_mining_item", AsyncMock()) as grant,
        patch.object(
            wf.game_xp_service,
            "award",
            AsyncMock(return_value=_award(game_total=10)),
        ),
        patch.object(wf.game_xp_service, "emit_award_events", AsyncMock()),
    ):
        result = await wf.commit_catch(99, 1, cast, rng=rng)
    return result, grant


@pytest.mark.asyncio
async def test_commit_catch_grants_a_pearl_on_a_lucky_reel():
    # random()==0.0: bonus roll fires (drawn first), then the pearl roll fires.
    forced = MagicMock()
    forced.random.return_value = 0.0
    result, grant = await _commit_collecting_grants(forced)

    assert result.pearl_found is True
    items = [call.args[2] for call in grant.await_args_list]
    # one pearl grant + the fish grant; the fish grant stays the LAST call.
    assert wf.PEARL_ITEM in items
    assert grant.await_args_list[-1].args[2] == _CATCH.species.name


@pytest.mark.asyncio
async def test_commit_catch_no_pearl_on_an_unlucky_reel_is_byte_identical():
    # random()==0.99 ≥ every chance → no bonus, no pearl; only the fish grant.
    forced = MagicMock()
    forced.random.return_value = 0.99
    result, grant = await _commit_collecting_grants(forced)

    assert result.pearl_found is False
    items = [call.args[2] for call in grant.await_args_list]
    assert wf.PEARL_ITEM not in items
    assert items == [_CATCH.species.name]  # the single fish grant, nothing else


# ---------------------------------------------------------------------------
# commit_catch — the coral rare-material drop (deepwater-only, this PR)
# ---------------------------------------------------------------------------


async def _commit_venue(rng, venue):
    """Commit a fixed cast made in *venue* under a forced *rng*."""
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    cast = wf.Cast(catch=_CATCH, level_before=1, venue=venue)
    with (
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "record_catch", AsyncMock(return_value=None)),
        patch.object(wf.db, "update_mining_item", AsyncMock()) as grant,
        patch.object(
            wf.game_xp_service,
            "award",
            AsyncMock(return_value=_award(game_total=10)),
        ),
        patch.object(wf.game_xp_service, "emit_award_events", AsyncMock()),
    ):
        result = await wf.commit_catch(99, 1, cast, rng=rng)
    return result, grant


@pytest.mark.asyncio
async def test_commit_catch_grants_coral_on_a_lucky_deepwater_reel():
    forced = MagicMock()
    forced.random.return_value = 0.0  # every roll fires
    result, grant = await _commit_venue(forced, wf.venue_mod.DEEPWATER)

    assert result.coral_found is True
    items = [call.args[2] for call in grant.await_args_list]
    assert wf.CORAL_ITEM in items
    assert grant.await_args_list[-1].args[2] == _CATCH.species.name  # fish stays last


@pytest.mark.asyncio
async def test_commit_catch_never_grants_coral_on_shore_even_when_lucky():
    forced = MagicMock()
    forced.random.return_value = 0.0
    result, grant = await _commit_venue(forced, wf.venue_mod.SHORE)

    assert result.coral_found is False
    items = [call.args[2] for call in grant.await_args_list]
    assert wf.CORAL_ITEM not in items


@pytest.mark.asyncio
async def test_commit_catch_no_coral_on_an_unlucky_deepwater_reel():
    forced = MagicMock()
    forced.random.return_value = 0.99  # nothing fires
    result, grant = await _commit_venue(forced, wf.venue_mod.DEEPWATER)

    assert result.coral_found is False
    items = [call.args[2] for call in grant.await_args_list]
    assert wf.CORAL_ITEM not in items
    assert items == [_CATCH.species.name]  # only the fish, byte-identical


# ---------------------------------------------------------------------------
# roll_cast — the rod's rarity_pull reaches the roll
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_roll_cast_passes_the_rods_rarity_pull_to_the_roll():
    rec: dict = {}
    gold = rods.rod_for_tier(3)
    with (
        patch.object(wf, "roll_catch", recording_roll_catch(rec)),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
    ):
        await wf.roll_cast(99, 1, gold)

    assert rec["rarity_pull"] == gold.rarity_pull  # the rod knob reaches the roll


@pytest.mark.asyncio
async def test_roll_cast_defaults_to_the_starter_rod():
    rec: dict = {}
    with (
        patch.object(wf, "roll_catch", recording_roll_catch(rec)),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={})),
    ):
        await wf.roll_cast(99, 1)  # no rod given

    assert rec["rarity_pull"] == 1.0  # starter → neutral pull


# ---------------------------------------------------------------------------
# buy_rod — the audited coin-sink purchase
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_buy_rod_debits_coins_and_raises_the_tier():
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    bronze = rods.rod_for_tier(1)
    with (
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(wf.db, "get_equipment", AsyncMock(return_value={})),
        patch.object(wf.db, "get_skills", AsyncMock(return_value={})),
        patch.object(wf.db, "get_structures", AsyncMock(return_value={})),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(
            wf.economy_service,
            "debit_in_txn",
            AsyncMock(return_value=900),
        ) as debit,
        patch.object(wf.db, "set_rod_tier", AsyncMock()) as set_tier,
        patch.object(wf.bus, "emit", AsyncMock()) as emit,
    ):
        result = await wf.buy_rod(99, 1)

    assert result.success is True
    assert result.tier == 1
    # debited the bronze price on the workflow's own conn, with the audit reason
    args, kwargs = debit.await_args
    assert args[0] is sentinel_conn
    assert bronze.price in args
    assert kwargs["reason"] == wf.ROD_PURCHASE_REASON
    set_tier.assert_awaited_once_with(99, 1, 1, conn=sentinel_conn)
    emit.assert_awaited_once()  # balance event after commit


@pytest.mark.asyncio
async def test_buy_rod_with_insufficient_funds_writes_nothing():
    @asynccontextmanager
    async def _ctx():
        yield MagicMock()

    with (
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(wf.db, "get_equipment", AsyncMock(return_value={})),
        patch.object(wf.db, "get_skills", AsyncMock(return_value={})),
        patch.object(wf.db, "get_structures", AsyncMock(return_value={})),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(
            wf.economy_service,
            "debit_in_txn",
            AsyncMock(side_effect=economy_service.InsufficientFundsError("broke")),
        ),
        patch.object(wf.db, "set_rod_tier", AsyncMock()) as set_tier,
        patch.object(wf.db, "get_coins", AsyncMock(return_value=10)),
        patch.object(wf.bus, "emit", AsyncMock()) as emit,
    ):
        result = await wf.buy_rod(99, 1)

    assert result.success is False
    assert result.tier == 0  # unchanged
    set_tier.assert_not_awaited()  # rolled back with the transaction
    emit.assert_not_awaited()  # no balance event on failure


@pytest.mark.asyncio
async def test_buy_rod_at_max_tier_is_a_noop():
    with (
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=rods.MAX_TIER)),
        patch.object(wf.economy_service, "debit_in_txn", AsyncMock()) as debit,
    ):
        result = await wf.buy_rod(99, 1)

    assert result.success is False
    assert result.tier == rods.MAX_TIER
    debit.assert_not_awaited()  # never touches the economy at the top of the ladder


@pytest.mark.asyncio
async def test_get_rod_resolves_the_owned_tier():
    with patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=2)):
        rod = await wf.get_rod(99, 1)
    assert rod is rods.rod_for_tier(2)


# ---------------------------------------------------------------------------
# begin_cast — the energy-gated cast start (separate fishing energy bar)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_begin_cast_spends_energy_and_rolls_when_charged():
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(wf.db, "get_equipment", AsyncMock(return_value={})),
        patch.object(wf.db, "get_skills", AsyncMock(return_value={})),
        patch.object(wf.db, "get_structures", AsyncMock(return_value={})),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="shore")),
        patch.object(
            wf.weather_mod, "current_weather", lambda: wf.weather_mod.CONDITIONS[0],
        ),
        patch.object(wf, "roll_catch", fake_roll_catch()),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()) as set_energy,
    ):
        start = await wf.begin_cast(99, 1)

    assert start.ok is True
    assert start.cast.catch is _CATCH
    assert start.energy_current == 8  # 10 settled − CAST_COST (2)
    set_energy.assert_awaited_once()  # the spend was persisted


@pytest.mark.asyncio
async def test_begin_cast_blocks_and_never_spends_when_out_of_energy():
    # 0 energy, just updated → nothing regened yet
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(0, 1000))),
        patch.object(wf.db, "get_structures", AsyncMock(return_value={})),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()) as set_energy,
        patch.object(wf.db, "get_rod_tier", AsyncMock()) as rod,
    ):
        start = await wf.begin_cast(99, 1)

    assert start.ok is False
    assert "energy" in (start.message or "").lower()
    set_energy.assert_not_awaited()  # no spend
    rod.assert_not_awaited()  # bailed before even rolling


@pytest.mark.asyncio
async def test_begin_cast_does_not_charge_on_an_empty_catalog():
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(wf.db, "get_equipment", AsyncMock(return_value={})),
        patch.object(wf.db, "get_skills", AsyncMock(return_value={})),
        patch.object(wf.db, "get_structures", AsyncMock(return_value={})),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="shore")),
        patch.object(
            wf.weather_mod, "current_weather", lambda: wf.weather_mod.CONDITIONS[0],
        ),
        patch.object(wf, "roll_catch", fake_roll_catch(None)),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()) as set_energy,
    ):
        start = await wf.begin_cast(99, 1)

    assert start.ok is False
    set_energy.assert_not_awaited()  # broken catalog → the player isn't charged


@pytest.mark.asyncio
async def test_get_energy_returns_the_settled_value():
    # 5 stored at epoch, now = 3 regen intervals later → 5 + 3 = 8
    now_intervals = 3 * wf.fish_energy.REGEN_SECONDS
    with (
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(5, 0))),
        patch.object(wf.db, "get_structures", AsyncMock(return_value={})),
        patch.object(wf.time, "time", lambda: now_intervals),
    ):
        cur = await wf.get_energy(99, 1)
    assert cur == 8


# ---------------------------------------------------------------------------
# Venue — shore ↔ deepwater toggle + per-cast threading (Q-0175 §5)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_venue_resolves_the_stored_profile():
    from utils.fishing import venue as venue_mod

    with patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="deepwater")):
        profile = await wf.get_venue(99, 1)
    assert profile is venue_mod.DEEPWATER_PROFILE


@pytest.mark.asyncio
async def test_set_venue_normalises_and_persists():
    with patch.object(wf.db, "set_fishing_venue", AsyncMock()) as set_v:
        change = await wf.set_venue(99, 1, "GARBAGE")  # unknown → shore
    assert change.venue == "shore"
    set_v.assert_awaited_once_with(99, 1, "shore")


@pytest.mark.asyncio
async def test_set_venue_deepwater_message_names_the_tradeoff():
    with patch.object(wf.db, "set_fishing_venue", AsyncMock()):
        change = await wf.set_venue(99, 1, "deepwater")
    assert change.venue == "deepwater"
    assert "deepwater" in change.message.lower()


@pytest.mark.asyncio
async def test_toggle_venue_flips_from_the_stored_value():
    with (
        patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="shore")),
        patch.object(
            wf.weather_mod, "current_weather", lambda: wf.weather_mod.CONDITIONS[0],
        ),
        patch.object(wf.db, "set_fishing_venue", AsyncMock()) as set_v,
    ):
        change = await wf.toggle_venue(99, 1)
    assert change.venue == "deepwater"
    set_v.assert_awaited_once_with(99, 1, "deepwater")


@pytest.mark.asyncio
async def test_begin_cast_threads_the_stored_venue_into_the_roll_and_profile():
    from utils.fishing import venue as venue_mod

    rec: dict = {}
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="deepwater")),
        patch.object(
            wf.weather_mod, "current_weather", lambda: wf.weather_mod.CONDITIONS[0],
        ),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(wf.db, "get_equipment", AsyncMock(return_value={})),
        patch.object(wf.db, "get_skills", AsyncMock(return_value={})),
        patch.object(wf.db, "get_structures", AsyncMock(return_value={})),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(wf, "roll_catch", recording_roll_catch(rec)),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()),
    ):
        start = await wf.begin_cast(99, 1)

    assert start.ok is True
    assert rec["venue"] == "deepwater"  # the stored venue gated the roll
    assert (
        start.venue_profile is venue_mod.DEEPWATER_PROFILE
    )  # ...and the view's tuning
    assert start.cast.venue == "deepwater"


# ---------------------------------------------------------------------------
# Weather — the daily date-seeded bias compounds onto the cast (Q-0089 idea)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_begin_cast_compounds_the_days_weather_onto_the_knobs():
    """Weather multiplies the rod×bait bite-speed/rarity and rides on CastStart."""
    from utils.fishing import rods
    from utils.fishing import weather as weather_mod

    storm = next(c for c in weather_mod.CONDITIONS if c.key == "storm")
    rec: dict = {}
    gold = rods.rod_for_tier(3)
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="shore")),
        patch.object(wf.weather_mod, "current_weather", lambda: storm),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=3)),
        patch.object(wf.db, "get_equipment", AsyncMock(return_value={})),
        patch.object(wf.db, "get_skills", AsyncMock(return_value={})),
        patch.object(wf.db, "get_structures", AsyncMock(return_value={})),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(wf, "roll_catch", recording_roll_catch(rec)),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()),
    ):
        start = await wf.begin_cast(99, 1)

    assert start.weather is storm
    # rod-only knobs, each scaled by the storm multiplier (no bait here).
    assert rec["rarity_pull"] == pytest.approx(gold.rarity_pull * storm.rarity_mult)
    assert start.effective_bite_speed == pytest.approx(
        gold.bite_speed * storm.bite_speed_mult,
    )
    assert start.effective_bite_speed != pytest.approx(
        gold.bite_speed,
    )  # weather moved it


# ---------------------------------------------------------------------------
# Fishing gear — the 4th cast knob (Q-0175 / V-14): rod × bait × weather × gear
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_begin_cast_folds_equipped_fishing_gear_into_the_knobs():
    """An equipped fishing charm biases the roll pull + bite speed and flags
    ``fishing_gear_bonus`` — the 4th how-well knob.
    """
    from utils import equipment as eq_mod
    from utils.fishing import gear as fishing_gear
    from utils.fishing import rods

    rec: dict = {}
    starter = rods.rod_for_tier(0)
    full = eq_mod.EffectiveStats(fishing_power=6, bite_luck=3)
    # A master angler charm in the CHARM slot → fishing_power=6, bite_luck=3.
    equipped = {"charm": "master angler charm"}
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="shore")),
        patch.object(
            wf.weather_mod, "current_weather", lambda: wf.weather_mod.CONDITIONS[0],
        ),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(wf.db, "get_equipment", AsyncMock(return_value=equipped)),
        patch.object(wf.db, "get_skills", AsyncMock(return_value={})),
        patch.object(wf.db, "get_structures", AsyncMock(return_value={})),
        patch.object(wf, "roll_catch", recording_roll_catch(rec)),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()),
    ):
        start = await wf.begin_cast(99, 1)

    assert rec["rarity_pull"] == pytest.approx(
        starter.rarity_pull * fishing_gear.fishing_pull_mult(full),
    )
    assert start.effective_bite_speed == pytest.approx(
        starter.bite_speed * fishing_gear.fishing_bite_speed_mult(full),
    )
    assert rec["rarity_pull"] > starter.rarity_pull  # gear actually pulled
    assert start.fishing_gear_bonus is True


@pytest.mark.asyncio
async def test_begin_cast_with_no_fishing_gear_is_byte_identical():
    """No fishing gear ⇒ knobs unchanged + ``fishing_gear_bonus`` False (the
    additive safety property — mining gear must not move the fishing knobs).
    """
    from utils.fishing import rods

    rec: dict = {}
    starter = rods.rod_for_tier(0)
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="shore")),
        patch.object(
            wf.weather_mod, "current_weather", lambda: wf.weather_mod.CONDITIONS[0],
        ),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(
            wf.db,
            "get_equipment",
            AsyncMock(return_value={"tool": "diamond pickaxe"}),
        ),
        patch.object(wf.db, "get_skills", AsyncMock(return_value={})),
        patch.object(wf.db, "get_structures", AsyncMock(return_value={})),
        patch.object(wf, "roll_catch", recording_roll_catch(rec)),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()),
    ):
        start = await wf.begin_cast(99, 1)

    assert rec["rarity_pull"] == pytest.approx(starter.rarity_pull)
    assert start.effective_bite_speed == pytest.approx(starter.bite_speed)
    assert start.fishing_gear_bonus is False


# ---------------------------------------------------------------------------
# Tide Pool — the 5th cast knob (2026-07-01): rod × bait × weather × gear × pool
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_begin_cast_folds_a_built_tide_pool_into_the_pull():
    """A built Tide Pool raises the roll's rarity pull and flags ``tide_pool_bonus``
    — the 5th how-well knob.
    """
    from utils.fishing import rods
    from utils.mining import structures

    rec: dict = {}
    starter = rods.rod_for_tier(0)
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="shore")),
        patch.object(
            wf.weather_mod, "current_weather", lambda: wf.weather_mod.CONDITIONS[0],
        ),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(wf.db, "get_equipment", AsyncMock(return_value={})),
        patch.object(wf.db, "get_skills", AsyncMock(return_value={})),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(
            wf.db,
            "get_structures",
            AsyncMock(return_value={structures.TIDE_POOL: 3}),
        ),
        patch.object(wf, "roll_catch", recording_roll_catch(rec)),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()),
    ):
        start = await wf.begin_cast(99, 1)

    assert rec["rarity_pull"] == pytest.approx(
        starter.rarity_pull * structures.tide_pool_pull_mult(3),
    )
    assert rec["rarity_pull"] > starter.rarity_pull  # the pool actually pulled
    assert start.tide_pool_bonus is True


@pytest.mark.asyncio
async def test_begin_cast_with_no_tide_pool_is_byte_identical():
    """An unbuilt Tide Pool ⇒ ×1.0 ⇒ the pull is unchanged + ``tide_pool_bonus``
    False (the additive-safety property).
    """
    from utils.fishing import rods

    rec: dict = {}
    starter = rods.rod_for_tier(0)
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="shore")),
        patch.object(
            wf.weather_mod, "current_weather", lambda: wf.weather_mod.CONDITIONS[0],
        ),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(wf.db, "get_equipment", AsyncMock(return_value={})),
        patch.object(wf.db, "get_skills", AsyncMock(return_value={})),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(wf.db, "get_structures", AsyncMock(return_value={})),
        patch.object(wf, "roll_catch", recording_roll_catch(rec)),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()),
    ):
        start = await wf.begin_cast(99, 1)

    assert rec["rarity_pull"] == pytest.approx(starter.rarity_pull)
    assert start.tide_pool_bonus is False


# ---------------------------------------------------------------------------
# Dock — the bite-speed structure knob (2026-07-01): the Tide Pool's sibling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_begin_cast_folds_a_built_dock_into_the_bite_speed():
    """A built Dock lowers ``effective_bite_speed`` (faster bite) and flags
    ``dock_bonus`` — without touching the rarity pull.
    """
    from utils.fishing import rods
    from utils.mining import structures

    starter = rods.rod_for_tier(0)
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="shore")),
        patch.object(
            wf.weather_mod, "current_weather", lambda: wf.weather_mod.CONDITIONS[0],
        ),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(wf.db, "get_equipment", AsyncMock(return_value={})),
        patch.object(wf.db, "get_skills", AsyncMock(return_value={})),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(
            wf.db,
            "get_structures",
            AsyncMock(return_value={structures.DOCK: 2}),
        ),
        patch.object(wf, "roll_catch", fake_roll_catch()),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()),
    ):
        start = await wf.begin_cast(99, 1)

    assert start.effective_bite_speed == pytest.approx(
        starter.bite_speed * structures.dock_bite_speed_mult(2),
    )
    assert start.effective_bite_speed < starter.bite_speed  # the dock sped the bite
    assert start.dock_bonus is True


@pytest.mark.asyncio
async def test_begin_cast_with_no_dock_is_byte_identical():
    """An unbuilt Dock ⇒ ×1.0 ⇒ the bite speed is unchanged + ``dock_bonus`` False."""
    from utils.fishing import rods

    starter = rods.rod_for_tier(0)
    with (
        patch.object(wf.time, "time", lambda: 1000),
        patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(10, 1000))),
        patch.object(wf.db, "get_fishing_venue", AsyncMock(return_value="shore")),
        patch.object(
            wf.weather_mod, "current_weather", lambda: wf.weather_mod.CONDITIONS[0],
        ),
        patch.object(wf.db, "get_rod_tier", AsyncMock(return_value=0)),
        patch.object(wf.db, "get_equipment", AsyncMock(return_value={})),
        patch.object(wf.db, "get_skills", AsyncMock(return_value={})),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"fishing": 0})),
        patch.object(wf.db, "get_active_bait", AsyncMock(return_value=("", 0))),
        patch.object(wf.db, "get_structures", AsyncMock(return_value={})),
        patch.object(wf, "roll_catch", fake_roll_catch()),
        patch.object(wf.db, "set_fishing_energy", AsyncMock()),
    ):
        start = await wf.begin_cast(99, 1)

    assert start.effective_bite_speed == pytest.approx(starter.bite_speed)
    assert start.dock_bonus is False


@pytest.mark.asyncio
async def test_get_energy_regens_faster_with_a_built_boathouse():
    """A built Boathouse shortens the regen interval, so the settled gauge is higher
    for the same stored state + elapsed time; unbuilt ⇒ byte-identical.
    """
    from utils.mining import structures

    now = 100  # 100s elapsed: 3 ticks at 30s/tick, 4 at 23s/tick (×0.76 boathouse)

    async def _energy(built):
        with (
            patch.object(wf.time, "time", lambda: now),
            patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(5, 0))),
            patch.object(wf.db, "get_structures", AsyncMock(return_value=built)),
        ):
            return await wf.get_energy(99, 1)

    plain = await _energy({})
    boathoused = await _energy({structures.BOATHOUSE: 2})
    # Faster refill = strictly more energy in the same wall-clock time (30s→23s
    # gives an extra tick over 90s); an unbuilt boathouse matches the base rate.
    assert boathoused > plain


@pytest.mark.asyncio
async def test_begin_cast_out_of_energy_wait_is_shorter_with_a_built_boathouse():
    """The out-of-energy "ready in" wait uses the Boathouse-adjusted regen interval —
    46s (×0.76 ⇒ 23s/energy) vs the base 1m 00s (30s/energy) for two energy.
    """
    from utils.mining import structures

    async def _wait_message(built):
        with (
            patch.object(wf.time, "time", lambda: 0),
            patch.object(wf.db, "get_fishing_energy", AsyncMock(return_value=(0, 0))),
            patch.object(wf.db, "get_structures", AsyncMock(return_value=built)),
        ):
            start = await wf.begin_cast(99, 1)
        assert start.ok is False
        return start.message

    assert "1m 00s" in await _wait_message({})
    assert "46s" in await _wait_message({structures.BOATHOUSE: 2})


@pytest.mark.asyncio
async def test_get_forecast_returns_todays_weather():
    from utils.fishing import weather as weather_mod

    rain = next(c for c in weather_mod.CONDITIONS if c.key == "rain")
    with patch.object(wf.weather_mod, "current_weather", lambda: rain):
        assert wf.get_forecast() is rain
