"""Inventory CRUD (per-guild user-owned items)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg


async def get_inventory(user_id: int, guild_id: int) -> dict[str, int]:
    rows = await pool.fetchall(
        "SELECT item_name, quantity FROM inventory WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
    )
    return {r["item_name"]: r["quantity"] for r in rows}


async def add_item(
    user_id: int,
    guild_id: int,
    item_name: str,
    quantity: int = 1,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    await pool.execute(
        """INSERT INTO inventory (user_id, guild_id, item_name, quantity)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (user_id, guild_id, item_name)
           DO UPDATE SET quantity=inventory.quantity + $4""",
        (user_id, guild_id, item_name, quantity),
        conn=conn,
    )


async def try_grant_unique_item(
    user_id: int,
    guild_id: int,
    item_name: str,
    *,
    conn: asyncpg.Connection | None = None,
) -> bool:
    """Grant one unit of *item_name* iff the user does not already own it.

    One conditional upsert decides ownership and writes atomically — the
    decision can't go stale between a ``has_item`` check and the grant,
    which closes the double-click double-charge race in shop purchases.
    "Owned" means quantity > 0 (matching :func:`has_item`); a stale
    zero-quantity row is granted through rather than blocking forever.
    Returns True when the grant happened, False when already owned.
    Transaction-aware (Q-0071): pass *conn* to join a workflow transaction.
    """
    row = await pool.fetchone(
        """INSERT INTO inventory (user_id, guild_id, item_name, quantity)
           VALUES ($1, $2, $3, 1)
           ON CONFLICT (user_id, guild_id, item_name)
           DO UPDATE SET quantity = inventory.quantity + 1
             WHERE inventory.quantity <= 0
           RETURNING item_name""",
        (user_id, guild_id, item_name),
        conn=conn,
    )
    return row is not None


async def has_item(
    user_id: int,
    guild_id: int,
    item_name: str,
    *,
    conn: asyncpg.Connection | None = None,
) -> bool:
    row = await pool.fetchone(
        "SELECT quantity FROM inventory "
        "WHERE user_id=$1 AND guild_id=$2 AND item_name=$3",
        (user_id, guild_id, item_name),
        conn=conn,
    )
    return bool(row and row["quantity"] > 0)
