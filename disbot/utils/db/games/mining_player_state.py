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


async def get_max_depth(
    user_id: str,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> int:
    """The deepest band this player has ever reached (0 = never left Surface)."""
    row = await pool.fetchone(
        "SELECT max_depth FROM mining_player_state WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return row["max_depth"] if row else 0


async def get_vault_level(
    user_id: str,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> int:
    """The player's vault-capacity tier (0 = the v1 base capacity)."""
    row = await pool.fetchone(
        "SELECT vault_level FROM mining_player_state WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return row["vault_level"] if row else 0


async def set_vault_level(
    user_id: str,
    guild_id: int,
    level: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Persist the player's *vault_level* for a guild (upsert; clamped >= 0).

    With *conn* given the upsert runs on that connection so the vault-upgrade
    coin debit and this level raise commit in one transaction (the workflow
    owns commit — RS02/Q-0071).
    """
    await pool.execute(
        """INSERT INTO mining_player_state (user_id, guild_id, vault_level)
           VALUES ($1, $2, GREATEST(0, $3))
           ON CONFLICT (user_id, guild_id)
           DO UPDATE SET vault_level=GREATEST(0, $3), updated_at=now()""",
        (user_id, guild_id, level),
        conn=conn,
    )


async def record_depth(
    user_id: str,
    guild_id: int,
    depth: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> bool:
    """Raise ``max_depth`` to *depth* if it beats the record; True on a record.

    One conditional upsert decides and writes together (no read-then-write
    race): a fresh row at depth ≥ 1 and a beaten record both return a row;
    an unbeaten record updates nothing and returns none.
    """
    row = await pool.fetchone(
        """INSERT INTO mining_player_state (user_id, guild_id, max_depth)
           VALUES ($1, $2, GREATEST(0, $3))
           ON CONFLICT (user_id, guild_id) DO UPDATE
             SET max_depth = $3, updated_at = now()
             WHERE mining_player_state.max_depth < $3
           RETURNING max_depth""",
        (user_id, guild_id, depth),
        conn=conn,
    )
    return row is not None
