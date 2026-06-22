"""chicken_farm CRUD — the per-(user, guild) idle-farm row.

Migration 090. Plain CRUD only; the egg-accrual + pricing math lives in
:mod:`utils.farm.farm` and the audited collect/buy/upgrade policy in
:mod:`services.farm_workflow`.

Transaction-aware (the Q-0071 precedent): the write primitive takes an optional
``conn`` so the farm workflow can compose the row update with the coin leg on one
connection. With ``conn`` given a primitive must never open its own transaction —
the caller owns commit/rollback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg

#: Defaults for a player with no row yet — one free starter hen, empty base coop
#: (kept in lockstep with migration 090's column defaults and
#: ``utils.farm.STARTER_CHICKENS``).
_DEFAULT_CHICKENS = 1
_DEFAULT_EGGS = 0
_DEFAULT_EGGS_UPDATED_AT = 0
_DEFAULT_COOP_LEVEL = 0

_SET_FARM_SQL = """
    INSERT INTO chicken_farm
        (user_id, guild_id, chickens, eggs, eggs_updated_at, coop_level)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (user_id, guild_id) DO UPDATE SET
        chickens = $3,
        eggs = $4,
        eggs_updated_at = $5,
        coop_level = $6
"""


async def get_chicken_farm(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> tuple[int, int, int, int]:
    """The player's stored ``(chickens, eggs, eggs_updated_at, coop_level)``.

    Returns the starter defaults (one hen, empty base coop) when no row exists.
    The stored ``eggs`` is *unsettled* — the caller applies passive accrual via
    :func:`utils.farm.settle` against the current time.
    """
    row = await pool.fetchone(
        "SELECT chickens, eggs, eggs_updated_at, coop_level "
        "FROM chicken_farm WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    if row is None:
        return (
            _DEFAULT_CHICKENS,
            _DEFAULT_EGGS,
            _DEFAULT_EGGS_UPDATED_AT,
            _DEFAULT_COOP_LEVEL,
        )
    return (
        row["chickens"],
        row["eggs"],
        row["eggs_updated_at"],
        row["coop_level"],
    )


async def set_chicken_farm(
    user_id: int,
    guild_id: int,
    chickens: int,
    eggs: int,
    eggs_updated_at: int,
    coop_level: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Upsert the full farm row for the player (settled-and-spent state)."""
    await pool.execute(
        _SET_FARM_SQL,
        (user_id, guild_id, chickens, eggs, eggs_updated_at, coop_level),
        conn=conn,
    )
