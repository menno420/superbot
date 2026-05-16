"""Inventory CRUD (per-guild user-owned items)."""

from __future__ import annotations

from utils.db import pool


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
) -> None:
    await pool.execute(
        """INSERT INTO inventory (user_id, guild_id, item_name, quantity)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (user_id, guild_id, item_name)
           DO UPDATE SET quantity=inventory.quantity + $4""",
        (user_id, guild_id, item_name, quantity),
    )


async def has_item(user_id: int, guild_id: int, item_name: str) -> bool:
    row = await pool.fetchone(
        "SELECT quantity FROM inventory "
        "WHERE user_id=$1 AND guild_id=$2 AND item_name=$3",
        (user_id, guild_id, item_name),
    )
    return bool(row and row["quantity"] > 0)
