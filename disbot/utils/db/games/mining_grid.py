"""mining grid CRUD — lateral position, the per-guild world seed, fog of war.

Direct-lane game state (``docs/ownership.md`` routes mining writes direct via
``utils/db/games/``).  The grid Mine model (hub-redesign PR 3, Q-0173):

* **position** — ``(pos_x, pos_y)`` on ``mining_player_state``; ``z`` is the
  existing ``depth`` band, so position is ``(pos_x, pos_y, depth)``.
* **world seed** — one row per guild in ``mining_world``; a guild with no row
  defaults to ``seed = guild_id``, so every guild has a stable shared world with
  no setup (Q-0173: "ONE shared grid per seed").
* **fog of war** — one row per visited ``(z, x, y)`` in ``mining_discovered``;
  reads only ever fetch a small window around the player.

RS02 (Q-0071): the write primitives take an optional ``conn`` so
``services/mining_workflow`` can compose them inside one transaction (callers own
commit).  The writers (:func:`set_position`, :func:`mark_discovered`,
:func:`set_world_seed`) are on the mining write-boundary ratchet
(``tests/unit/invariants/test_mining_write_boundary.py``) — only the workflow
service may call them, never a cog or view.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg


async def get_position(
    user_id: str,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> tuple[int, int]:
    """The player's lateral ``(pos_x, pos_y)`` for a guild (``(0, 0)`` if none)."""
    row = await pool.fetchone(
        "SELECT pos_x, pos_y FROM mining_player_state WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return (row["pos_x"], row["pos_y"]) if row else (0, 0)


async def set_position(
    user_id: str,
    guild_id: int,
    x: int,
    y: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Persist the player's lateral position (upsert — one row per player)."""
    await pool.execute(
        """INSERT INTO mining_player_state (user_id, guild_id, pos_x, pos_y)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (user_id, guild_id)
           DO UPDATE SET pos_x=$3, pos_y=$4, updated_at=now()""",
        (user_id, guild_id, x, y),
        conn=conn,
    )


async def get_world_seed(
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> int:
    """The guild's world seed — its stored override, or ``guild_id`` by default.

    The default makes every guild a stable, shared, shareable world with no
    setup; only an explicit ``!mineworld <seed>`` ever writes a row.
    """
    row = await pool.fetchone(
        "SELECT seed FROM mining_world WHERE guild_id=$1",
        (guild_id,),
        conn=conn,
    )
    return row["seed"] if row else guild_id


async def set_world_seed(
    guild_id: int,
    seed: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Persist a guild's world *seed* (upsert — the owner re-seed)."""
    await pool.execute(
        """INSERT INTO mining_world (guild_id, seed)
           VALUES ($1, $2)
           ON CONFLICT (guild_id)
           DO UPDATE SET seed=$2, updated_at=now()""",
        (guild_id, seed),
        conn=conn,
    )


async def mark_discovered(
    user_id: str,
    guild_id: int,
    z: int,
    x: int,
    y: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Record that the player has visited cell ``(z, x, y)`` (idempotent)."""
    await pool.execute(
        """INSERT INTO mining_discovered (user_id, guild_id, z, x, y)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (user_id, guild_id, z, x, y) DO NOTHING""",
        (user_id, guild_id, z, x, y),
        conn=conn,
    )


async def get_discovered_window(
    user_id: str,
    guild_id: int,
    z: int,
    x_min: int,
    x_max: int,
    y_min: int,
    y_max: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> set[tuple[int, int]]:
    """The visited ``(x, y)`` cells at depth *z* inside the inclusive box.

    Windowed so the map render is O(window) however far the player has roamed.
    """
    rows = await pool.fetchall(
        """SELECT x, y FROM mining_discovered
           WHERE user_id=$1 AND guild_id=$2 AND z=$3
             AND x BETWEEN $4 AND $5 AND y BETWEEN $6 AND $7""",
        (user_id, guild_id, z, x_min, x_max, y_min, y_max),
        conn=conn,
    )
    return {(r["x"], r["y"]) for r in rows}
