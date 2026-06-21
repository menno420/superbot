"""creature_workflow — catch, transaction membership, flee writes nothing.

The Q-0071 contract: on a successful catch the collection-log write + the xp
award run on the SAME workflow-owned connection, and the xp event emits only
after the transaction exits (= commits). A failed catch (the creature flees)
writes nothing and awards no xp.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import creature_workflow as wf
from services import game_xp_service
from utils.creatures import Creature, Encounter


def _txn(sentinel_conn, events):
    @asynccontextmanager
    async def _ctx():
        events.append("txn_enter")
        yield sentinel_conn
        events.append("txn_exit")

    return _ctx


_CREATURE = Creature("Magmaul", "Ember", "Rare", "attacker", "🔥")
_ENCOUNTER = Encounter(creature=_CREATURE)


def _award(*, game_total, leveled_up=False, level=1, amount=4):
    return game_xp_service.GameXpAward(
        guild_id=1,
        user_id=99,
        game=game_xp_service.GAME_CREATURE,
        action="catch",
        amount=amount,
        game_total=game_total,
        shared_total=game_total,
        level=level,
        leveled_up=leveled_up,
    )


# ---------------------------------------------------------------------------
# creature_level_from_xp — the level curve reuse
# ---------------------------------------------------------------------------


def test_zero_xp_is_creature_level_one():
    assert wf.creature_level_from_xp(0) == 1


def test_creature_level_is_monotonic_in_xp():
    levels = [wf.creature_level_from_xp(x) for x in range(0, 5000, 50)]
    assert levels == sorted(levels)


def test_creature_level_is_uncapped():
    # Unlike fishing there is no MAX cap — a huge xp total keeps climbing.
    assert wf.creature_level_from_xp(10_000_000) > 1


# ---------------------------------------------------------------------------
# catch() — the outing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_successful_catch_writes_both_legs_on_one_conn_and_emits_after_commit():
    sentinel_conn = MagicMock(name="conn")
    events: list[str] = []

    async def _record(user_id, guild_id, creature, *, conn=None):
        events.append("record")
        assert conn is sentinel_conn
        assert creature == "Magmaul"

    async def _award_fn(guild_id, user_id, *, game, action, conn=None, depth=0):
        events.append("award")
        assert conn is sentinel_conn
        assert game == game_xp_service.GAME_CREATURE
        assert action == "catch"
        return _award(game_total=10)

    with (
        patch.object(wf, "roll_encounter", lambda rng=None: _ENCOUNTER),
        patch.object(wf, "attempt_catch", lambda creature, level, rng=None: True),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"creature": 5})),
        patch.object(wf.db, "get_creature_collection", AsyncMock(return_value={})),
        patch.object(wf.db, "transaction", _txn(sentinel_conn, events)),
        patch.object(wf.db, "record_creature_catch", AsyncMock(side_effect=_record)),
        patch.object(wf.game_xp_service, "award", AsyncMock(side_effect=_award_fn)),
        patch.object(wf.game_xp_service, "emit_award_events", AsyncMock()) as emit_xp,
    ):
        result = await wf.catch(99, 1)

    for leg in ("record", "award"):
        assert events.index(leg) < events.index("txn_exit")
    emit_xp.assert_awaited_once()
    assert result.caught is True
    assert result.creature is _CREATURE
    assert result.is_new is True  # empty collection before


@pytest.mark.asyncio
async def test_repeat_catch_is_not_a_new_dex_entry():
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    with (
        patch.object(wf, "roll_encounter", lambda rng=None: _ENCOUNTER),
        patch.object(wf, "attempt_catch", lambda creature, level, rng=None: True),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"creature": 5})),
        patch.object(
            wf.db, "get_creature_collection", AsyncMock(return_value={"Magmaul": 2})
        ),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "record_creature_catch", AsyncMock()),
        patch.object(
            wf.game_xp_service, "award", AsyncMock(return_value=_award(game_total=10))
        ),
        patch.object(wf.game_xp_service, "emit_award_events", AsyncMock()),
    ):
        result = await wf.catch(99, 1)

    assert result.caught is True
    assert result.is_new is False


@pytest.mark.asyncio
async def test_a_fled_creature_writes_nothing_and_awards_no_xp():
    with (
        patch.object(wf, "roll_encounter", lambda rng=None: _ENCOUNTER),
        patch.object(wf, "attempt_catch", lambda creature, level, rng=None: False),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"creature": 0})),
        patch.object(wf.db, "record_creature_catch", AsyncMock()) as record,
        patch.object(wf.game_xp_service, "award", AsyncMock()) as award,
    ):
        result = await wf.catch(99, 1)

    assert result.caught is False
    assert result.creature is _CREATURE
    record.assert_not_awaited()
    award.assert_not_awaited()


@pytest.mark.asyncio
async def test_empty_catalog_writes_nothing():
    with (
        patch.object(wf, "roll_encounter", lambda rng=None: None),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={})),
        patch.object(wf.db, "record_creature_catch", AsyncMock()) as record,
    ):
        result = await wf.catch(99, 1)

    assert result.creature is None
    assert result.caught is False
    record.assert_not_awaited()


@pytest.mark.asyncio
async def test_crossing_a_game_level_sets_xp_note():
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    with (
        patch.object(wf, "roll_encounter", lambda rng=None: _ENCOUNTER),
        patch.object(wf, "attempt_catch", lambda creature, level, rng=None: True),
        patch.object(wf.db, "get_game_xp", AsyncMock(return_value={"creature": 50})),
        patch.object(wf.db, "get_creature_collection", AsyncMock(return_value={})),
        patch.object(wf.db, "transaction", _ctx),
        patch.object(wf.db, "record_creature_catch", AsyncMock()),
        patch.object(
            wf.game_xp_service,
            "award",
            AsyncMock(return_value=_award(game_total=10, leveled_up=True, level=2)),
        ),
        patch.object(wf.game_xp_service, "emit_award_events", AsyncMock()),
    ):
        result = await wf.catch(99, 1)

    assert result.leveled_up is True
    assert result.xp_note is not None
