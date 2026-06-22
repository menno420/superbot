"""fishing_rod CRUD — the per-(user, guild) owned rod tier.

Migration 087. Plain CRUD only; the rod knob values + the purchase policy live in
:mod:`utils.fishing.rods` and :mod:`services.fishing_workflow`.

Transaction-aware (the Q-0071 / catch-log precedent): the write primitive takes
an optional ``conn`` so the purchase workflow debits coins and bumps the tier in
ONE workflow-owned transaction. With ``conn`` given a primitive must never open
its own transaction — the caller owns commit/rollback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg

# Upsert the owned rod tier: insert the first row, or raise it to the new tier.
_SET_ROD_TIER_SQL = """
    INSERT INTO fishing_rod (user_id, guild_id, tier)
    VALUES ($1, $2, $3)
    ON CONFLICT (user_id, guild_id) DO UPDATE SET tier = $3
"""


async def get_rod_tier(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> int:
    """The player's owned rod tier (0 = starter when no row exists yet)."""
    row = await pool.fetchone(
        "SELECT tier FROM fishing_rod WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return row["tier"] if row else 0


async def set_rod_tier(
    user_id: int,
    guild_id: int,
    tier: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Set the player's owned rod tier (insert the row or raise it)."""
    await pool.execute(_SET_ROD_TIER_SQL, (user_id, guild_id, tier), conn=conn)
