"""creature_battle_service — the read boundary for creature PvP.

v1 is read-only: load each player's owned-creature pool, build a level-normalized
team, resolve through the pure engine. No writes, no audit (a later slice). These
tests pin: pool resolution skips unknown rows, an empty side yields ``None``, and a
resolved battle returns level-normalized rosters + a real winner.
"""

from __future__ import annotations

import random
from unittest.mock import AsyncMock, patch

import pytest

from services import creature_battle_service as svc
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
