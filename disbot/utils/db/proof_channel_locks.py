"""CRUD primitives for ``proof_channel_locks`` (migration 104).

Persists a timed proof-channel prize lock's unlock deadline so a boot-time
reconcile sweep can recover it after a restart / cog reload — see
``cogs/proof_channel_cog.py`` (the write boundary) and the Stage-2 walk bug #8.
Only *timed* locks write here; the plain ``+prize`` lock is intentionally
indefinite. Pure SQL — no business logic.
"""

from __future__ import annotations

from typing import Any

from utils.db import pool


async def upsert_lock(
    *,
    guild_id: int,
    channel_id: int,
    winner_id: int,
    unlock_at: Any,
) -> None:
    """Record (or replace) a channel's active timed-lock deadline."""
    await pool.execute(
        """
        INSERT INTO proof_channel_locks (guild_id, channel_id, winner_id, unlock_at)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (guild_id, channel_id) DO UPDATE
            SET winner_id = EXCLUDED.winner_id,
                unlock_at = EXCLUDED.unlock_at,
                created_at = NOW()
        """,
        (guild_id, channel_id, winner_id, unlock_at),
    )


async def delete_lock(guild_id: int, channel_id: int) -> None:
    """Clear a channel's persisted timed-lock row (called on unlock)."""
    await pool.execute(
        "DELETE FROM proof_channel_locks WHERE guild_id=$1 AND channel_id=$2",
        (guild_id, channel_id),
    )


async def all_locks() -> list[dict[str, Any]]:
    """Every persisted timed lock (the boot reconcile sweep reads all guilds)."""
    return await pool.fetchall(
        "SELECT guild_id, channel_id, winner_id, unlock_at FROM proof_channel_locks",
    )


async def delete_for_guild(guild_id: int) -> int:
    """Drop every persisted timed lock for a departed guild (teardown)."""
    rows = await pool.fetchall(
        "DELETE FROM proof_channel_locks WHERE guild_id=$1 RETURNING channel_id",
        (guild_id,),
    )
    return len(rows)
