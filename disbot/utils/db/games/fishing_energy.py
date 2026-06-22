"""fishing_energy CRUD — the per-(user, guild) cast-energy bar.

Migration 088. Plain CRUD only; the regen math + the cast cost live in
:mod:`utils.fishing.energy` and the spend policy in
:mod:`services.fishing_workflow`.

Transaction-aware (the Q-0071 / catch-log precedent): the write primitive takes
an optional ``conn`` so the cast workflow can compose the energy spend with other
writes on one connection. With ``conn`` given a primitive must never open its own
transaction — the caller owns commit/rollback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg

# Upsert the stored energy + its settle timestamp.
_SET_ENERGY_SQL = """
    INSERT INTO fishing_energy (user_id, guild_id, energy, energy_updated_at)
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (user_id, guild_id) DO UPDATE SET
        energy = $3,
        energy_updated_at = $4
"""

#: Defaults for a player with no row yet — a full bar (see migration 088).
_DEFAULT_ENERGY = 20


async def get_fishing_energy(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> tuple[int, int]:
    """The player's stored ``(energy, energy_updated_at)`` (full bar @ 0 if no row).

    The stored value is *unsettled* — the caller applies passive regen via
    :func:`utils.fishing.energy.settle` against the current time.
    """
    row = await pool.fetchone(
        "SELECT energy, energy_updated_at FROM fishing_energy "
        "WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    if row is None:
        return _DEFAULT_ENERGY, 0
    return row["energy"], row["energy_updated_at"]


async def set_fishing_energy(
    user_id: int,
    guild_id: int,
    energy: int,
    energy_updated_at: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Store the settled-and-spent ``(energy, energy_updated_at)`` for the player."""
    await pool.execute(
        _SET_ENERGY_SQL,
        (user_id, guild_id, energy, energy_updated_at),
        conn=conn,
    )
