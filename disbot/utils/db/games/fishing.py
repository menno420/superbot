"""fishing_catch_log CRUD — the per-(user, guild, species) collection log.

Migration 075. Plain CRUD only; the catch math + level/reward policy live in
:mod:`services.fishing_workflow` and :mod:`utils.fishing`.

Transaction-aware (the Q-0071 / mining precedent): the write primitive takes an
optional ``conn`` so :mod:`services.fishing_workflow` commits the log row and the
xp award in ONE workflow-owned transaction. With ``conn`` given a primitive must
never open its own transaction — the caller owns commit/rollback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg

# Upsert one catch: insert the first catch of a species, or bump the tally —
# count += 1 and last_caught = now(). first_caught is preserved (INSERT-only).
_RECORD_CATCH_SQL = """
    INSERT INTO fishing_catch_log (user_id, guild_id, species, count)
    VALUES ($1, $2, $3, 1)
    ON CONFLICT (user_id, guild_id, species) DO UPDATE SET
        count       = fishing_catch_log.count + 1,
        last_caught = now()
"""


async def record_catch(
    user_id: int,
    guild_id: int,
    species: str,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Record one catch of *species* for the player (insert or bump the tally)."""
    await pool.execute(_RECORD_CATCH_SQL, (user_id, guild_id, species), conn=conn)


async def get_fishing_log(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> dict[str, int]:
    """The player's catch log: ``{species: count}``."""
    rows = await pool.fetchall(
        "SELECT species, count FROM fishing_catch_log "
        "WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return {r["species"]: r["count"] for r in rows}


async def top_fishers(
    guild_id: int,
    known_species: list[str],
    *,
    limit: int = 10,
) -> list[tuple[int, int, int]]:
    """``[(user_id, total_caught, unique_species)]`` for *guild_id*, top by catches.

    Only counts rows whose species is in *known_species* (the current catalog) so
    legacy rows from a superseded catalog never inflate the totals (Q-0175
    reconciliation: the interim design's `golden koi`/`ancient leviathan` etc.).
    """
    if not known_species:
        return []
    rows = await pool.fetchall(
        "SELECT user_id, SUM(count) AS caught, COUNT(*) AS species "
        "FROM fishing_catch_log WHERE guild_id=$1 AND species = ANY($2::text[]) "
        "GROUP BY user_id ORDER BY caught DESC LIMIT $3",
        (guild_id, known_species, limit),
    )
    return [(r["user_id"], r["caught"], r["species"]) for r in rows]
