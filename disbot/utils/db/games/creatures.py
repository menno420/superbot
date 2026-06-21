"""creature_collection_log CRUD — the per-(user, guild, creature) collection.

Migration 077. Plain CRUD only; the encounter/catch math + level/reward policy
live in :mod:`services.creature_workflow` and :mod:`utils.creatures`.

Transaction-aware (the Q-0071 / fishing precedent): the write primitive takes an
optional ``conn`` so :mod:`services.creature_workflow` commits the log row and the
xp award in ONE workflow-owned transaction. With ``conn`` given a primitive must
never open its own transaction — the caller owns commit/rollback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg

# Upsert one catch: insert the first catch of a creature, or bump the tally —
# count += 1 and last_caught = now(). first_caught is preserved (INSERT-only).
_RECORD_CATCH_SQL = """
    INSERT INTO creature_collection_log (user_id, guild_id, creature, count)
    VALUES ($1, $2, $3, 1)
    ON CONFLICT (user_id, guild_id, creature) DO UPDATE SET
        count       = creature_collection_log.count + 1,
        last_caught = now()
"""


async def record_creature_catch(
    user_id: int,
    guild_id: int,
    creature: str,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Record one catch of *creature* for the player (insert or bump the tally)."""
    await pool.execute(_RECORD_CATCH_SQL, (user_id, guild_id, creature), conn=conn)


async def get_creature_collection(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> dict[str, int]:
    """The player's collection: ``{creature: count}``."""
    rows = await pool.fetchall(
        "SELECT creature, count FROM creature_collection_log "
        "WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return {r["creature"]: r["count"] for r in rows}


async def top_collectors(
    guild_id: int,
    known_creatures: list[str],
    *,
    limit: int = 10,
) -> list[tuple[int, int, int]]:
    """``[(user_id, total_caught, unique_creatures)]`` for *guild_id*, top by catches.

    Only counts rows whose creature is in *known_creatures* (the current catalog)
    so legacy rows from a superseded roster never inflate the totals (the fishing
    Q-0175 reconciliation precedent).
    """
    if not known_creatures:
        return []
    rows = await pool.fetchall(
        "SELECT user_id, SUM(count) AS caught, COUNT(*) AS creatures "
        "FROM creature_collection_log "
        "WHERE guild_id=$1 AND creature = ANY($2::text[]) "
        "GROUP BY user_id ORDER BY caught DESC LIMIT $3",
        (guild_id, known_creatures, limit),
    )
    return [(r["user_id"], r["caught"], r["creatures"]) for r in rows]
