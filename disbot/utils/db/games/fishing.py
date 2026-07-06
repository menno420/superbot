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
# best_weight keeps the heaviest catch of this species (the trophy record):
# GREATEST against the incoming weight so it only ever grows. The CTE captures
# the row's PRIOR best before the upsert so the caller can tell whether this
# catch set a new personal best (prev_best is NULL on the very first catch).
_RECORD_CATCH_SQL = """
    WITH prev AS (
        SELECT best_weight
        FROM fishing_catch_log
        WHERE user_id = $1 AND guild_id = $2 AND species = $3
    )
    INSERT INTO fishing_catch_log (user_id, guild_id, species, count, best_weight)
    VALUES ($1, $2, $3, 1, $4)
    ON CONFLICT (user_id, guild_id, species) DO UPDATE SET
        count       = fishing_catch_log.count + 1,
        last_caught = now(),
        best_weight = GREATEST(fishing_catch_log.best_weight, EXCLUDED.best_weight)
    RETURNING (SELECT best_weight FROM prev) AS prev_best
"""


async def record_catch(
    user_id: int,
    guild_id: int,
    species: str,
    weight: float = 0.0,
    *,
    conn: asyncpg.Connection | None = None,
) -> float | None:
    """Record one catch of *species* (insert or bump the tally) + its weight.

    Returns the species' **prior** best weight (``None`` on the first ever
    catch), so the caller can detect a new personal best: it is one when the
    prior best is ``None`` or strictly less than *weight*.
    """
    row = await pool.fetchone(
        _RECORD_CATCH_SQL,
        (user_id, guild_id, species, weight),
        conn=conn,
    )
    return row["prev_best"] if row else None


async def get_fishing_log(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> dict[str, int]:
    """The player's catch log: ``{species: count}``."""
    rows = await pool.fetchall(
        "SELECT species, count FROM fishing_catch_log WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return {r["species"]: r["count"] for r in rows}


async def get_fishing_records(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> dict[str, float]:
    """The player's trophy records: ``{species: best_weight}`` (heaviest caught).

    Only species with a recorded best (> 0) appear, so a freshly-migrated row
    that has not been re-caught since the weightless era is simply absent.
    """
    rows = await pool.fetchall(
        "SELECT species, best_weight FROM fishing_catch_log "
        "WHERE user_id=$1 AND guild_id=$2 AND best_weight > 0",
        (user_id, guild_id),
        conn=conn,
    )
    return {r["species"]: r["best_weight"] for r in rows}


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


async def top_trophies(
    guild_id: int,
    known_species: list[str],
    *,
    limit: int = 10,
) -> list[tuple[int, str, float]]:
    """``[(user_id, species, best_weight)]`` — the guild's heaviest catches.

    A "biggest fish" hall of fame: the single heaviest catch rows server-wide,
    ordered by weight, so a trophy lunker competes against everyone (the catch
    log's per-(user, species) ``best_weight`` is each angler's record for that
    fish). An angler can appear more than once for different species. Filtered to
    the current catalog (like :func:`top_fishers`) so legacy rows never show, and
    to ``best_weight > 0`` so pre-trophy-era rows (migration 095) are skipped.
    """
    if not known_species:
        return []
    rows = await pool.fetchall(
        "SELECT user_id, species, best_weight FROM fishing_catch_log "
        "WHERE guild_id=$1 AND species = ANY($2::text[]) AND best_weight > 0 "
        "ORDER BY best_weight DESC LIMIT $3",
        (guild_id, known_species, limit),
    )
    return [(r["user_id"], r["species"], r["best_weight"]) for r in rows]
