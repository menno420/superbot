"""Creature PvP battle service — the read boundary between a player's collection
and the pure battle engine (creature-game v1).

The runtime side of the [creature-game plan](docs/planning/creature-game-design-and-sim-2026-06-20.md)
§4 *Battle*: load each player's owned-creature pool from the collection-log, build a
**level-normalized** 6-mon team (one of each element at :data:`NORMALIZED_LEVEL`), and
resolve the match through the pure engine (:mod:`utils.creatures.battle`).

This is the thin ``services/`` seam the plan called for. Two entry points:

- :func:`resolve_pvp` — the pure **read** path: read collections, compute a winner.
  No writes; used where a result should not be persisted (and by the engine tests).
- :func:`resolve_and_record_pvp` — the **audited-write** half (the plan's deferred
  result-recording slice): resolve, then in ONE :func:`db.transaction` record both
  fighters' win/loss tally and award the winner's :data:`GAME_CREATURE` xp; the
  game-xp events emit **after** commit. Mirrors :mod:`services.creature_workflow`
  (the Q-0071 transaction contract). Like catch/fishing, a routine game-progression
  write is **not** ``emit_audit_action``-audited — audit is the moderation / settings
  / governance seam, not per-battle XP; the battle math stays pure in
  :mod:`utils.creatures.battle`.

The anti-P2W rule (Q-0039 / plan §3): PvP normalizes every creature to a flat level,
so **collection breadth, type matchups, and the engine's move policies** decide the
outcome — not who has ground more levels. The win xp here is **prestige only** (it
feeds the shared game-level / leaderboards), never PvP power.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from services import game_xp_service
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


@dataclass(frozen=True)
class RecordedPvp:
    """A resolved-and-recorded PvP battle: the result plus the persisted tallies.

    ``winner_id`` / ``loser_id`` are the Discord user ids (not the team labels);
    ``winner_record`` / ``loser_record`` are each side's ``(wins, losses)`` **after**
    this battle was recorded, so the renderer can show the updated standing.
    ``xp_note`` is the winner's inline level-up notice, set only when the win
    crossed a shared game level.
    """

    result: PvpResult
    winner_id: int
    loser_id: int
    winner_record: tuple[int, int]
    loser_record: tuple[int, int]
    xp_note: str | None = None


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


async def resolve_and_record_pvp(
    challenger_id: int,
    opponent_id: int,
    guild_id: int,
    *,
    rng: random.Random | None = None,
) -> RecordedPvp | None:
    """Resolve a PvP battle **and persist the outcome** (the audited-write half).

    Returns ``None`` when either player has no usable team (the caller surfaces a
    "go !catch some first" nudge — nothing is written). Otherwise:

    1. resolve via :func:`resolve_pvp` (level-normalized, anti-P2W),
    2. in ONE :func:`db.transaction`: record both fighters' win/loss tally and
       award the winner's :data:`GAME_CREATURE` battle-win xp,
    3. read each side's updated record (same conn),
    4. emit the game-xp events **after** commit.

    The win xp is prestige only (PvP is level-normalized), so recording a result
    can never make a player's PvP teams stronger.
    """
    result = await resolve_pvp(challenger_id, opponent_id, guild_id, rng=rng)
    if result is None:
        return None

    if result.a_won:
        winner_id, loser_id = challenger_id, opponent_id
    else:
        winner_id, loser_id = opponent_id, challenger_id

    async with db.transaction() as conn:
        await db.record_battle_outcome(winner_id, loser_id, guild_id, conn=conn)
        award = await game_xp_service.award(
            guild_id,
            winner_id,
            game=game_xp_service.GAME_CREATURE,
            action="battle_win",
            conn=conn,
        )
        winner_record = await db.get_battle_record(winner_id, guild_id, conn=conn)
        loser_record = await db.get_battle_record(loser_id, guild_id, conn=conn)

    if award is not None:
        await game_xp_service.emit_award_events(award)

    return RecordedPvp(
        result=result,
        winner_id=winner_id,
        loser_id=loser_id,
        winner_record=winner_record,
        loser_record=loser_record,
        xp_note=award.note if award is not None and award.leveled_up else None,
    )
