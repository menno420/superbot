"""mining_inventory CRUD (replaces the original mining_data.json file)."""

from __future__ import annotations

from utils.db import pool


async def get_mining_inventory(user_id: str) -> dict[str, int]:
    rows = await pool.fetchall(
        "SELECT item_name, quantity FROM mining_inventory WHERE user_id=$1",
        (user_id,),
    )
    return {r["item_name"]: r["quantity"] for r in rows}


async def update_mining_item(
    user_id: str,
    item_name: str,
    delta: int,
) -> None:
    """Add or subtract *delta* of *item_name* for *user_id*. Clamps to 0."""
    await pool.execute(
        """INSERT INTO mining_inventory (user_id, item_name, quantity)
           VALUES ($1, $2, GREATEST(0, $3))
           ON CONFLICT (user_id, item_name)
           DO UPDATE SET quantity=GREATEST(0, mining_inventory.quantity + $3)""",
        (user_id, item_name, delta),
    )


async def set_mining_inventory(
    user_id: str,
    inventory: dict[str, int],
) -> None:
    """Overwrite the entire inventory for a user (admin reset)."""
    p = pool.get()
    async with p.acquire() as conn:
        await conn.execute(
            "DELETE FROM mining_inventory WHERE user_id=$1",
            user_id,
        )
        if inventory:
            await conn.executemany(
                "INSERT INTO mining_inventory (user_id, item_name, quantity) "
                "VALUES ($1, $2, $3)",
                [(user_id, k, v) for k, v in inventory.items() if v > 0],
            )


async def get_all_mining_totals() -> list[tuple[str, int]]:
    """Return [(user_id, total_items)] sorted descending — for leaderboard."""
    rows = await pool.fetchall(
        "SELECT user_id, SUM(quantity) AS total FROM mining_inventory "
        "GROUP BY user_id ORDER BY total DESC LIMIT 10",
    )
    return [(r["user_id"], r["total"]) for r in rows]
