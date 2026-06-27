"""mining_loadout_presets CRUD — named saved gear loadouts per player.

Direct-lane game state (``docs/ownership.md`` routes mining writes direct via
``utils/db/games/``; the RC-8A ledger catalogues this as an accepted-direct
write — the same lane as :mod:`utils.db.games.mining_equipment`).

A *preset* is the set of rows sharing a ``(user_id, guild_id, name)`` — each row
pins one slot's saved item.  ``user_id`` is ``TEXT`` to match
``mining_equipment`` / ``mining_inventory``'s legacy column type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg


async def save_loadout(
    user_id: str,
    guild_id: int,
    name: str,
    slots: dict[str, str],
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Replace the preset *name* with *slots* (``{slot: item_name}``).

    The whole preset is rewritten: any previously-saved slot not present in
    *slots* is dropped, so saving an empty mapping clears the preset.  Caller
    is expected to pass a real connection inside a transaction when atomicity
    across the delete + inserts matters (the workflow does).
    """
    await pool.execute(
        "DELETE FROM mining_loadout_presets "
        "WHERE user_id=$1 AND guild_id=$2 AND name=$3",
        (user_id, guild_id, name),
        conn=conn,
    )
    for slot, item_name in slots.items():
        await pool.execute(
            """INSERT INTO mining_loadout_presets
                   (user_id, guild_id, name, slot, item_name)
               VALUES ($1, $2, $3, $4, $5)""",
            (user_id, guild_id, name, slot, item_name),
            conn=conn,
        )


async def get_loadout(
    user_id: str,
    guild_id: int,
    name: str,
    *,
    conn: asyncpg.Connection | None = None,
) -> dict[str, str]:
    """Return ``{slot: item_name}`` for the saved preset *name* (``{}`` if none)."""
    rows = await pool.fetchall(
        "SELECT slot, item_name FROM mining_loadout_presets "
        "WHERE user_id=$1 AND guild_id=$2 AND name=$3",
        (user_id, guild_id, name),
        conn=conn,
    )
    return {r["slot"]: r["item_name"] for r in rows}


async def list_loadouts(
    user_id: str,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> list[str]:
    """Return the player's saved preset names, alphabetically."""
    rows = await pool.fetchall(
        "SELECT DISTINCT name FROM mining_loadout_presets "
        "WHERE user_id=$1 AND guild_id=$2 ORDER BY name",
        (user_id, guild_id),
        conn=conn,
    )
    return [r["name"] for r in rows]


async def delete_loadout(
    user_id: str,
    guild_id: int,
    name: str,
    *,
    conn: asyncpg.Connection | None = None,
) -> int:
    """Delete the preset *name*; return the number of slot rows removed."""
    rows = await pool.fetchall(
        "DELETE FROM mining_loadout_presets "
        "WHERE user_id=$1 AND guild_id=$2 AND name=$3 RETURNING slot",
        (user_id, guild_id, name),
        conn=conn,
    )
    return len(rows)
