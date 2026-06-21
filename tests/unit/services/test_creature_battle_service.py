"""creature_battle_service — the read boundary for creature PvP.

v1 is read-only: load each player's owned-creature pool, build a level-normalized
team, resolve through the pure engine. No writes, no audit (a later slice). These
tests pin: pool resolution skips unknown rows, an empty side yields ``None``, and a
resolved battle returns level-normalized rosters + a real winner.
"""

from __future__ import annotations

import random
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services import creature_battle_service as svc
from services import game_xp_service
from utils.creatures import CREATURES, NORMALIZED_LEVEL


def _names_by_element() -> dict[str, str]:
    """One catalog creature name per element (enough for a full 6-mon team)."""
    picked: dict[str, str] = {}
    for c in CREATURES:
        picked.setdefault(c.element, c.name)
    return picked


_FULL_COLLECTION = {name: 1 for name in _names_by_element().values()}


@pytest.mark.asyncio
async def test_load_pool_resolves_owned_names_and_skips_unknown():
    collection = {**_FULL_COLLECTION, "Definitely Not A Creature": 3}
    with patch.object(
        svc.db,
        "get_creature_collection",
        AsyncMock(return_value=collection),
    ):
        pool = await svc.load_pool(1, 2)
    names = {c.name for c in pool}
    assert "Definitely Not A Creature" not in names
    assert names == set(_FULL_COLLECTION)


@pytest.mark.asyncio
async def test_resolve_pvp_returns_none_when_a_side_has_no_creatures():
    async def _collection(user_id, guild_id):
        return _FULL_COLLECTION if user_id == 1 else {}

    with patch.object(svc.db, "get_creature_collection", side_effect=_collection):
        result = await svc.resolve_pvp(1, 2, 99, rng=random.Random(0))
    assert result is None


@pytest.mark.asyncio
async def test_resolve_pvp_returns_none_when_collection_has_only_unknown_rows():
    with patch.object(
        svc.db,
        "get_creature_collection",
        AsyncMock(return_value={"Ghost Mon": 1}),
    ):
        result = await svc.resolve_pvp(1, 2, 99, rng=random.Random(0))
    assert result is None


@pytest.mark.asyncio
async def test_resolve_pvp_builds_level_normalized_teams_and_picks_a_winner():
    with patch.object(
        svc.db,
        "get_creature_collection",
        AsyncMock(return_value=_FULL_COLLECTION),
    ):
        result = await svc.resolve_pvp(1, 2, 99, rng=random.Random(7))

    assert result is not None
    assert result.outcome.winner in ("a", "b")
    assert result.a_won == (result.outcome.winner == "a")
    assert result.team_a and result.team_b
    # Anti-P2W: every combatant is normalized to the flat PvP level.
    for combatant in (*result.team_a, *result.team_b):
        assert combatant.level == NORMALIZED_LEVEL


@pytest.mark.asyncio
async def test_resolve_pvp_is_deterministic_for_a_fixed_seed():
    with patch.object(
        svc.db,
        "get_creature_collection",
        AsyncMock(return_value=_FULL_COLLECTION),
    ):
        a = await svc.resolve_pvp(1, 2, 99, rng=random.Random(42))
        b = await svc.resolve_pvp(1, 2, 99, rng=random.Random(42))
    assert a is not None and b is not None
    assert a.outcome.winner == b.outcome.winner


# ---------------------------------------------------------------------------
# resolve_and_record_pvp — the audited-write half
# ---------------------------------------------------------------------------


def _award(**kw):
    base = dict(
        guild_id=99,
        user_id=0,
        game=game_xp_service.GAME_CREATURE,
        action="battle_win",
        amount=6,
        game_total=6,
        shared_total=6,
        level=1,
        leveled_up=False,
    )
    base.update(kw)
    return game_xp_service.GameXpAward(**base)


@pytest.mark.asyncio
async def test_resolve_and_record_writes_both_legs_on_one_conn_and_emits_after():
    sentinel_conn = MagicMock(name="conn")
    events: list[str] = []

    @asynccontextmanager
    async def _txn():
        events.append("txn_enter")
        yield sentinel_conn
        events.append("txn_exit")

    async def _record(winner_id, loser_id, guild_id, *, conn=None):
        events.append("record")
        assert conn is sentinel_conn

    async def _award_fn(guild_id, user_id, *, game, action, conn=None, depth=0):
        events.append("award")
        assert conn is sentinel_conn
        assert action == "battle_win"
        return _award(user_id=user_id)

    # A distinct sentinel record per player, so the assertion can check the
    # service routed each id's record to the right slot (winner is engine-decided).
    _records = {1: (3, 1), 2: (0, 2)}

    async def _get_record(user_id, guild_id, *, conn=None):
        return _records[user_id]

    with (
        patch.object(
            svc.db,
            "get_creature_collection",
            AsyncMock(return_value=_FULL_COLLECTION),
        ),
        patch.object(svc.db, "transaction", _txn),
        patch.object(svc.db, "record_battle_outcome", AsyncMock(side_effect=_record)),
        patch.object(svc.db, "get_battle_record", AsyncMock(side_effect=_get_record)),
        patch.object(svc.game_xp_service, "award", AsyncMock(side_effect=_award_fn)),
        patch.object(svc.game_xp_service, "emit_award_events", AsyncMock()) as emit_xp,
    ):
        recorded = await svc.resolve_and_record_pvp(1, 2, 99, rng=random.Random(7))

    assert recorded is not None
    # Both writes happened inside the transaction; the xp event after it.
    for leg in ("record", "award"):
        assert events.index(leg) < events.index("txn_exit")
    emit_xp.assert_awaited_once()
    # Winner is whoever the engine picked; their record/loser's record came back.
    assert recorded.winner_id in (1, 2)
    assert recorded.loser_id in (1, 2)
    assert recorded.winner_id != recorded.loser_id
    assert recorded.winner_record == _records[recorded.winner_id]
    assert recorded.loser_record == _records[recorded.loser_id]


@pytest.mark.asyncio
async def test_resolve_and_record_returns_none_and_writes_nothing_without_a_team():
    async def _collection(user_id, guild_id):
        return _FULL_COLLECTION if user_id == 1 else {}

    with (
        patch.object(svc.db, "get_creature_collection", side_effect=_collection),
        patch.object(svc.db, "record_battle_outcome", AsyncMock()) as record,
        patch.object(svc.game_xp_service, "award", AsyncMock()) as award,
    ):
        recorded = await svc.resolve_and_record_pvp(1, 2, 99, rng=random.Random(0))

    assert recorded is None
    record.assert_not_awaited()
    award.assert_not_awaited()


@pytest.mark.asyncio
async def test_resolve_and_record_carries_levelup_note_only_when_crossed():
    with (
        patch.object(
            svc.db,
            "get_creature_collection",
            AsyncMock(return_value=_FULL_COLLECTION),
        ),
        patch.object(svc.db, "transaction", _passthrough_txn()),
        patch.object(svc.db, "record_battle_outcome", AsyncMock()),
        patch.object(svc.db, "get_battle_record", AsyncMock(return_value=(1, 0))),
        patch.object(
            svc.game_xp_service,
            "award",
            AsyncMock(return_value=_award(leveled_up=True, level=3)),
        ),
        patch.object(svc.game_xp_service, "emit_award_events", AsyncMock()),
    ):
        recorded = await svc.resolve_and_record_pvp(1, 2, 99, rng=random.Random(7))

    assert recorded is not None
    assert recorded.xp_note is not None
    assert "Level 3" in recorded.xp_note


def _passthrough_txn():
    @asynccontextmanager
    async def _txn():
        yield MagicMock(name="conn")

    return _txn
