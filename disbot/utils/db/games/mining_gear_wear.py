"""mining_gear_wear CRUD — remaining durability of a player's active gear.

Direct-lane game state: ``docs/ownership.md`` routes mining writes direct via
``utils/db/games/`` (no audited service — see the RC-8A direct-DB ledger).

Wear is keyed by **item name**, not equipment slot, so it survives
unequip/re-equip (slot-keyed durability would reset on re-equip — a
free-repair exploit).  A row exists only while the item is *worn*: absence
means full durability; breaking or repairing the item deletes its row.
``user_id`` is ``TEXT`` to match ``mining_inventory``'s legacy column type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg


async def get_gear_wear(
    user_id: str, guild_id: int, *, conn: asyncpg.Connection | None = None
) -> dict[str, int]:
    """Return ``{item_name: remaining_durability}`` for the user's worn gear.

    Items without a row are at full durability (the caller resolves the max
    via :func:`utils.equipment.max_durability`).
    """
    rows = await pool.fetchall(
        "SELECT item_name, durability FROM mining_gear_wear "
        "WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return {r["item_name"]: r["durability"] for r in rows}


async def set_gear_wear(
    user_id: str,
    guild_id: int,
    item_name: str,
    durability: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Persist *durability* for *item_name* (upsert — one row per item)."""
    await pool.execute(
        """INSERT INTO mining_gear_wear (user_id, guild_id, item_name, durability)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (user_id, guild_id, item_name)
           DO UPDATE SET durability=$4, updated_at=now()""",
        (user_id, guild_id, item_name, durability),
        conn=conn,
    )


async def clear_gear_wear(
    user_id: str,
    guild_id: int,
    item_name: str,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Delete the wear row for *item_name* (item broke or was repaired)."""
    await pool.execute(
        "DELETE FROM mining_gear_wear "
        "WHERE user_id=$1 AND guild_id=$2 AND item_name=$3",
        (user_id, guild_id, item_name),
        conn=conn,
    )
