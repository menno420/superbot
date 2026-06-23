"""fishing_venue CRUD — the per-(user, guild) current fishing venue.

Migration 094. Plain CRUD only; the venue keys + the per-venue tuning live in
:mod:`utils.fishing.venue` and the set-sail / dock policy in
:mod:`services.fishing_workflow`.

Transaction-aware (the Q-0071 / fishing-rod precedent): the write primitive takes
an optional ``conn`` so a future workflow could compose the venue write with
other writes on one connection. With ``conn`` given a primitive must never open
its own transaction — the caller owns commit/rollback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg

#: The stored venue for a player with no row yet (see migration 094).
_DEFAULT_VENUE = "shore"

# Upsert the current venue: insert the first row, or flip it to the new venue.
_SET_VENUE_SQL = """
    INSERT INTO fishing_venue (user_id, guild_id, venue)
    VALUES ($1, $2, $3)
    ON CONFLICT (user_id, guild_id) DO UPDATE SET venue = $3
"""


async def get_fishing_venue(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> str:
    """The player's current venue (``'shore'`` when no row exists yet)."""
    row = await pool.fetchone(
        "SELECT venue FROM fishing_venue WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return row["venue"] if row else _DEFAULT_VENUE


async def set_fishing_venue(
    user_id: int,
    guild_id: int,
    venue: str,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Set the player's current venue (insert the row or flip it)."""
    await pool.execute(_SET_VENUE_SQL, (user_id, guild_id, venue), conn=conn)
