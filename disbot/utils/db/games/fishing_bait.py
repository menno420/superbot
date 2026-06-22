"""fishing_bait CRUD — the per-(user, guild) loaded bait + remaining charges.

Migration 090. Plain CRUD only; the bait knob values live in
:mod:`utils.fishing.bait` and the purchase/consume policy in
:mod:`services.fishing_workflow`.

Transaction-aware (the Q-0071 / catch-log precedent): the write primitives take
an optional ``conn`` so the purchase workflow can debit coins and load the bait
in ONE workflow-owned transaction. With ``conn`` given a primitive must never
open its own transaction — the caller owns commit/rollback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg

# Upsert the loaded bait + its remaining charges.
_SET_BAIT_SQL = """
    INSERT INTO fishing_bait (user_id, guild_id, bait_key, charges)
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (user_id, guild_id) DO UPDATE SET
        bait_key = $3,
        charges = $4
"""


async def get_active_bait(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> tuple[str, int]:
    """The player's loaded ``(bait_key, charges)`` (``("", 0)`` when none).

    An empty key or non-positive charge count both mean "no bait" — the caller
    (``fishing_workflow``) resolves the key to a :class:`~utils.fishing.bait.Bait`.
    """
    row = await pool.fetchone(
        "SELECT bait_key, charges FROM fishing_bait WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    if row is None:
        return "", 0
    return row["bait_key"], row["charges"]


async def set_active_bait(
    user_id: int,
    guild_id: int,
    bait_key: str,
    charges: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Load *bait_key* with *charges* for the player (insert the row or replace)."""
    await pool.execute(
        _SET_BAIT_SQL,
        (user_id, guild_id, bait_key, charges),
        conn=conn,
    )


async def clear_active_bait(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Drop the player's loaded bait (charges spent) → back to bait-less fishing."""
    await pool.execute(
        _SET_BAIT_SQL,
        (user_id, guild_id, "", 0),
        conn=conn,
    )
