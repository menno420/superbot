"""mining_inventory CRUD.

PR M3 — every public function now requires ``guild_id``.  The audit
flagged this module as the only multi-tenancy-violating CRUD in the
codebase: migration 002 added the column, migration 017 widened the
primary key to ``(user_id, guild_id, item_name)``, and this PR flips
the read/write path to use that column.

Existing rows live at ``guild_id = 0`` and are preserved as
pre-2026-stabilization legacy inventory (Mfix-A from the stabilization
plan).  New writes go to the real guild_id.

``user_id`` retains its legacy ``TEXT`` type from the pre-DB JSON era;
converting it to BIGINT is a separate concern flagged by the audit and
explicitly NOT bundled into this PR.
"""

from __future__ import annotations

from utils.db import pool


async def get_mining_inventory(user_id: str, guild_id: int) -> dict[str, int]:
    rows = await pool.fetchall(
        "SELECT item_name, quantity FROM mining_inventory "
        "WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
    )
    return {r["item_name"]: r["quantity"] for r in rows}


async def update_mining_item(
    user_id: str,
    guild_id: int,
    item_name: str,
    delta: int,
) -> None:
    """Add or subtract *delta* of *item_name* for *(user_id, guild_id)*.

    Clamps to 0 on both INSERT and UPDATE; the new primary key
    ``(user_id, guild_id, item_name)`` makes the upsert per-guild.
    """
    await pool.execute(
        """INSERT INTO mining_inventory (user_id, guild_id, item_name, quantity)
           VALUES ($1, $2, $3, GREATEST(0, $4))
           ON CONFLICT (user_id, guild_id, item_name)
           DO UPDATE SET quantity = GREATEST(0, mining_inventory.quantity + $4)""",
        (user_id, guild_id, item_name, delta),
    )


async def set_mining_inventory(
    user_id: str,
    guild_id: int,
    inventory: dict[str, int],
) -> None:
    """Overwrite the entire inventory for *(user_id, guild_id)*.

    PR M3: scoped to a single guild.  Previously the DELETE swept every
    guild's inventory for the user — a real "cross-guild wipe bomb"
    triggered by the ``!reset_inventory`` admin command.
    """
    p = pool.get()
    async with p.acquire() as conn:
        await conn.execute(
            "DELETE FROM mining_inventory WHERE user_id=$1 AND guild_id=$2",
            user_id,
            guild_id,
        )
        if inventory:
            await conn.executemany(
                "INSERT INTO mining_inventory "
                "(user_id, guild_id, item_name, quantity) "
                "VALUES ($1, $2, $3, $4)",
                [(user_id, guild_id, k, v) for k, v in inventory.items() if v > 0],
            )


async def get_all_mining_totals(guild_id: int) -> list[tuple[str, int]]:
    """Return [(user_id, total_items)] for *guild_id*, top 10 by total.

    PR M3: the previous unscoped variant summed across every guild's
    inventory and surfaced cross-guild users on per-guild leaderboards.
    """
    rows = await pool.fetchall(
        "SELECT user_id, SUM(quantity) AS total FROM mining_inventory "
        "WHERE guild_id=$1 "
        "GROUP BY user_id ORDER BY total DESC LIMIT 10",
        (guild_id,),
    )
    return [(r["user_id"], r["total"]) for r in rows]
