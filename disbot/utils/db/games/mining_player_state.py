"""mining_player_state CRUD — a player's persistent depth/biome position.

Direct-lane game state: ``docs/ownership.md`` routes mining writes direct via
``utils/db/games/`` (no audited service — see the RC-8A direct-DB ledger).  One
row per ``(user_id, guild_id)``; ``user_id`` is ``TEXT`` to match
``mining_inventory``'s legacy column type.  ``depth`` is the integer band index
(0 = Surface); the biome is derived from it (:mod:`utils.mining.world`), never
stored, so depth is the single source of truth for position.

RS02 (Q-0071): write primitives take an optional ``conn`` so the workflow
service can compose them inside one transaction (callers own commit).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg


async def get_depth(
    user_id: str,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> int:
    """Return the player's stored depth (0 = Surface) for a guild."""
    row = await pool.fetchone(
        "SELECT depth FROM mining_player_state WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return row["depth"] if row else 0


async def set_depth(
    user_id: str,
    guild_id: int,
    depth: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Persist the player's *depth* for a guild (upsert — one row per player)."""
    await pool.execute(
        """INSERT INTO mining_player_state (user_id, guild_id, depth)
           VALUES ($1, $2, $3)
           ON CONFLICT (user_id, guild_id)
           DO UPDATE SET depth=$3, updated_at=now()""",
        (user_id, guild_id, depth),
        conn=conn,
    )


async def get_last_broken(
    user_id: str,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> str | None:
    """The last gear item that broke for this player, or None (quick-craft)."""
    row = await pool.fetchone(
        "SELECT last_broken_item FROM mining_player_state "
        "WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return row["last_broken_item"] if row else None


async def set_last_broken(
    user_id: str,
    guild_id: int,
    item_name: str | None,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Record (or clear, with None) the last item that broke (upsert)."""
    await pool.execute(
        """INSERT INTO mining_player_state (user_id, guild_id, last_broken_item)
           VALUES ($1, $2, $3)
           ON CONFLICT (user_id, guild_id)
           DO UPDATE SET last_broken_item=$3, updated_at=now()""",
        (user_id, guild_id, item_name),
        conn=conn,
    )
