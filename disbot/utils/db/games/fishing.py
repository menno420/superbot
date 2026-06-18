"""fishing_catch_log CRUD — the per-(user, guild, species) collection log.

Migration 075.  Plain CRUD only; the catch math + reward policy live in
:mod:`services.fishing_workflow` and :mod:`utils.fishing`.

Transaction-aware (the Q-0071 / mining precedent): the write primitive takes an
optional ``conn`` so :mod:`services.fishing_workflow` commits the log row, the
coin credit, and the XP award in ONE workflow-owned transaction.  With ``conn``
given a primitive must never open its own transaction — the caller owns
commit/rollback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg

# Upsert one catch: insert the first catch of a species, or bump the tally —
# count += 1, total_value += value, best_weight = max(existing, this weight),
# last_caught = now().  first_caught is preserved (set only on INSERT).
_RECORD_CATCH_SQL = """
    INSERT INTO fishing_catch_log
        (user_id, guild_id, species, count, best_weight, total_value)
    VALUES ($1, $2, $3, 1, $4, $5)
    ON CONFLICT (user_id, guild_id, species) DO UPDATE SET
        count        = fishing_catch_log.count + 1,
        best_weight  = GREATEST(fishing_catch_log.best_weight, EXCLUDED.best_weight),
        total_value  = fishing_catch_log.total_value + EXCLUDED.total_value,
        last_caught  = now()
"""


async def record_catch(
    user_id: int,
    guild_id: int,
    species: str,
    weight: float,
    value: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Record one catch of *species* (weight kg, *value* coins) for the player."""
    await pool.execute(
        _RECORD_CATCH_SQL,
        (user_id, guild_id, species, weight, value),
        conn=conn,
    )


async def get_fishing_log(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> dict[str, dict]:
    """The player's catch log: ``{species: {count, best_weight, total_value}}``."""
    rows = await pool.fetchall(
        "SELECT species, count, best_weight, total_value "
        "FROM fishing_catch_log WHERE user_id=$1 AND guild_id=$2 "
        "ORDER BY total_value DESC",
        (user_id, guild_id),
        conn=conn,
    )
    return {
        r["species"]: {
            "count": r["count"],
            "best_weight": r["best_weight"],
            "total_value": r["total_value"],
        }
        for r in rows
    }


async def top_fishers(guild_id: int, *, limit: int = 10) -> list[tuple[int, int, int]]:
    """``[(user_id, total_caught, total_value)]`` for *guild_id*, top by value."""
    rows = await pool.fetchall(
        "SELECT user_id, SUM(count) AS caught, SUM(total_value) AS value "
        "FROM fishing_catch_log WHERE guild_id=$1 "
        "GROUP BY user_id ORDER BY value DESC LIMIT $2",
        (guild_id, limit),
    )
    return [(r["user_id"], r["caught"], r["value"]) for r in rows]
