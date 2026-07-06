"""mining_equipment CRUD — which item a player has equipped per slot.

Direct-lane game state: ``docs/ownership.md`` routes mining writes direct via
``utils/db/games/`` (no audited service — see the RC-8A direct-DB ledger).  One
row per ``(user_id, guild_id, slot)``.  ``user_id`` is ``TEXT`` to match
``mining_inventory``'s legacy column type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg


async def get_equipment(
    user_id: str,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> dict[str, str]:
    """Return ``{slot: item_name}`` for the user's equipped gear in a guild."""
    rows = await pool.fetchall(
        "SELECT slot, item_name FROM mining_equipment WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return {r["slot"]: r["item_name"] for r in rows}


async def equip_item(
    user_id: str,
    guild_id: int,
    slot: str,
    item_name: str,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Equip *item_name* into *slot* (upsert — one item per slot)."""
    await pool.execute(
        """INSERT INTO mining_equipment (user_id, guild_id, slot, item_name)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (user_id, guild_id, slot)
           DO UPDATE SET item_name=$4, equipped_at=now()""",
        (user_id, guild_id, slot, item_name),
        conn=conn,
    )


async def unequip_slot(
    user_id: str,
    guild_id: int,
    slot: str,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Clear *slot* for the user in a guild."""
    await pool.execute(
        "DELETE FROM mining_equipment WHERE user_id=$1 AND guild_id=$2 AND slot=$3",
        (user_id, guild_id, slot),
        conn=conn,
    )
