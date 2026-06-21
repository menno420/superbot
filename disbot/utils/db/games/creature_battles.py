"""creature_battle_record CRUD — the per-(user, guild) PvP win/loss tally.

Migration 082. Plain CRUD only; the level-normalized battle math is pure
(:mod:`utils.creatures.battle`) and the result-recording policy lives in
:mod:`services.creature_battle_service`.

Transaction-aware (the Q-0071 / fishing precedent): the write primitive takes an
optional ``conn`` so :mod:`services.creature_battle_service` commits both fighters'
records and the winner's xp award in ONE workflow-owned transaction. With ``conn``
given a primitive must never open its own transaction — the caller owns
commit/rollback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg

# Bump one side of a battle: insert the player's first record (with the win or
# loss already counted), or increment the running tally and stamp last_battle.
# $3/$4 are the (win, loss) deltas for this row — (1, 0) for the winner,
# (0, 1) for the loser — so the same primitive records both sides.
_RECORD_OUTCOME_SQL = """
    INSERT INTO creature_battle_record (user_id, guild_id, wins, losses)
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (user_id, guild_id) DO UPDATE SET
        wins        = creature_battle_record.wins + $3,
        losses      = creature_battle_record.losses + $4,
        last_battle = now()
"""


async def record_battle_outcome(
    winner_id: int,
    loser_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Record one resolved PvP battle: winner +1 win, loser +1 loss.

    Two upserts on the same connection so the pair commits atomically with the
    winner's xp award (the caller's transaction).
    """
    await pool.execute(_RECORD_OUTCOME_SQL, (winner_id, guild_id, 1, 0), conn=conn)
    await pool.execute(_RECORD_OUTCOME_SQL, (loser_id, guild_id, 0, 1), conn=conn)


async def get_battle_record(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> tuple[int, int]:
    """The player's ``(wins, losses)`` — ``(0, 0)`` when they've never battled."""
    row = await pool.fetchone(
        "SELECT wins, losses FROM creature_battle_record "
        "WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    if row is None:
        return (0, 0)
    return (row["wins"], row["losses"])


async def top_battlers(
    guild_id: int,
    *,
    limit: int = 10,
) -> list[tuple[int, int, int]]:
    """``[(user_id, wins, losses)]`` for *guild_id*, most wins first.

    Ties on wins break on fewer losses (the cleaner record ranks higher), then on
    ``user_id`` so the order is deterministic. Only players with at least one win
    appear — a pure-loss record isn't a leaderboard entry.
    """
    rows = await pool.fetchall(
        "SELECT user_id, wins, losses FROM creature_battle_record "
        "WHERE guild_id=$1 AND wins > 0 "
        "ORDER BY wins DESC, losses ASC, user_id ASC LIMIT $2",
        (guild_id, limit),
    )
    return [(r["user_id"], r["wins"], r["losses"]) for r in rows]
