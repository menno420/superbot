"""Creature PvP battle service — the read boundary between a player's collection
and the pure battle engine (creature-game v1).

The runtime side of the [creature-game plan](docs/planning/creature-game-design-and-sim-2026-06-20.md)
§4 *Battle*: load each player's owned-creature pool from the collection-log, build a
**level-normalized** 6-mon team (one of each element at :data:`NORMALIZED_LEVEL`), and
resolve the match through the pure engine (:mod:`utils.creatures.battle`).

This is the thin ``services/`` seam the plan called for. **v1 is read-only** — a PvP
battle reads collections and computes a winner; it does **not** persist a result or
award xp yet (the audited-write half is a later slice), so there is no
``db.transaction()`` / ``emit_audit_action`` here. The moment a battle records a
result, this is where that transaction will live (the math stays in
:mod:`utils.creatures.battle`).

The anti-P2W rule (Q-0039 / plan §3): PvP normalizes every creature to a flat level,
so **collection breadth, type matchups, and the engine's move policies** decide the
outcome — not who has ground more levels.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from utils import db
from utils.creatures import (
    NORMALIZED_LEVEL,
    BattleOutcome,
    Combatant,
    Creature,
    creature_by_name,
    resolve_battle,
    standard_team,
)


@dataclass(frozen=True)
class PvpResult:
    """The resolved PvP battle: the outcome plus each side's starting roster.

    ``team_a`` / ``team_b`` are snapshotted **before** resolution (the engine
    mutates combatant HP in place), so renderers can list the rosters as they
    entered the field.
    """

    outcome: BattleOutcome
    team_a: tuple[Combatant, ...]
    team_b: tuple[Combatant, ...]

    @property
    def a_won(self) -> bool:
        return self.outcome.a_won


async def load_pool(user_id: int, guild_id: int) -> list[Creature]:
    """The catalog creatures a player currently owns (their battle pool).

    Reads the collection-log and resolves each owned name against the live
    catalog; rows for a creature no longer in the catalog (a superseded roster,
    the fishing reconciliation lesson) are simply skipped.
    """
    collection = await db.get_creature_collection(user_id, guild_id)
    pool: list[Creature] = []
    for name in collection:
        creature = creature_by_name(name)
        if creature is not None:
            pool.append(creature)
    return pool


def build_normalized_team(
    pool: list[Creature],
    rng: random.Random,
) -> list[Combatant]:
    """A level-normalized 'one of each element' team drawn from *pool*.

    Thin wrapper over :func:`utils.creatures.standard_team` pinned to
    :data:`NORMALIZED_LEVEL` so callers can't accidentally seed a raw-level
    (pay-to-win) PvP team.
    """
    return standard_team(pool, rng, level=NORMALIZED_LEVEL)


async def resolve_pvp(
    challenger_id: int,
    opponent_id: int,
    guild_id: int,
    *,
    rng: random.Random | None = None,
) -> PvpResult | None:
    """Resolve a creature PvP battle between two players.

    Returns ``None`` when either player has no usable team (an empty collection
    or one with no catalog-known creatures) — the caller surfaces a "go !catch
    some first" nudge. Both teams are built at :data:`NORMALIZED_LEVEL`.
    """
    rng = rng if rng is not None else random.Random()
    pool_a = await load_pool(challenger_id, guild_id)
    pool_b = await load_pool(opponent_id, guild_id)

    team_a = build_normalized_team(pool_a, rng)
    team_b = build_normalized_team(pool_b, rng)
    if not team_a or not team_b:
        return None

    # Snapshot the rosters before resolve_battle mutates combatant HP in place.
    roster_a = tuple(team_a)
    roster_b = tuple(team_b)
    outcome = resolve_battle(team_a, team_b, rng=rng)
    return PvpResult(outcome=outcome, team_a=roster_a, team_b=roster_b)
