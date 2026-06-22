"""fishing_workflow — level-gated catch, transaction membership, no coins.

The Q-0071 contract: the catch-log write + the xp award run on the SAME
workflow-owned connection, and the xp event emits only after the transaction
exits (= commits). v1 pays no coins (owner Q-0175 — fish value is deferred).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import fishing_workflow as wf
from services import game_xp_service
from utils.fishing import MAX_LEVEL
from utils.fishing.fish import Catch, FishSpecies


def _txn(sentinel_conn, events):
    @asynccontextmanager
    async def _ctx():
        events.append("txn_enter")
        yield sentinel_conn
        events.append("txn_exit")

    return _ctx


_CATCH = Catch(species=FishSpecies("trout", 8, "🐠"))


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

    async def _record(user_id, guild_id, species, *, conn=None):
        events.append("record")
        assert conn is sentinel_conn
        assert species == "trout"

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
        patch.object(wf, "roll_catch", lambda level, rng=None: _CATCH),
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
    # v1 pays no coins → the workflow never touches the economy seam.
    assert not hasattr(wf, "economy_service")
    assert result.catch is _CATCH


@pytest.mark.asyncio
async def test_crossing_a_fishing_level_flags_unlocked_bigger():
    sentinel_conn = MagicMock(name="conn")

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    # Pre-read xp 50 → level 1; post-award game_total huge → MAX_LEVEL.
    with (
        patch.object(wf, "roll_catch", lambda level, rng=None: _CATCH),
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
    seen_levels: list[int] = []

    @asynccontextmanager
    async def _ctx():
        yield sentinel_conn

    def _roll(level, rng=None):
        seen_levels.append(level)
        return _CATCH

    with (
        patch.object(wf, "roll_catch", _roll),
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

    assert seen_levels == [1]  # 0 xp → level 1


@pytest.mark.asyncio
async def test_empty_catalog_writes_nothing():
    with (
        patch.object(wf, "roll_catch", lambda level, rng=None: None),
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
        patch.object(wf, "roll_catch", lambda level, rng=None: _CATCH),
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
async def test_commit_catch_on_empty_cast_writes_nothing():
    cast = wf.Cast(catch=None, level_before=2)
    with patch.object(wf.db, "record_catch", AsyncMock()) as record:
        result = await wf.commit_catch(99, 1, cast)

    assert result.catch is None
    assert result.fishing_level == 2
    record.assert_not_awaited()
