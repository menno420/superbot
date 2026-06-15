"""mining_structures CRUD — a player's built structures (brainstorm §7.5).

One row per ``(user_id, guild_id, structure)`` holding that structure's built
level (absent row = level 0).  ``user_id`` is ``BIGINT`` to match
``player_skills`` / ``game_xp`` (player-progression identity), not
``mining_inventory``'s legacy ``TEXT`` column.

The write primitive ``set_structure_level`` takes an optional ``conn`` so
``services/mining_workflow.py`` can debit coins, consume materials, and raise the
level inside ONE transaction (the ``vault_upgrade`` precedent — neither leg ever
commits alone).  Reads (``get_structures``) stay free for panels.  Like the other
mining write primitives, ``set_structure_level`` is on the RS02 write-boundary
ratchet (``tests/unit/invariants/test_mining_write_boundary.py``) — only the
owning service may call it, never a cog or view.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg

_SET_LEVEL_SQL = """INSERT INTO mining_structures (user_id, guild_id, structure, level)
           VALUES ($1, $2, $3, GREATEST(0, $4))
           ON CONFLICT (user_id, guild_id, structure)
           DO UPDATE SET level = GREATEST(0, $4)"""


async def get_structures(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> dict[str, int]:
    """The player's built structures for a guild — ``{structure: level}``.

    Zero-level rows are filtered out so callers see only built structures; an
    unbuilt player reads as ``{}`` (every structure at level 0).
    """
    rows = await pool.fetchall(
        "SELECT structure, level FROM mining_structures "
        "WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return {r["structure"]: r["level"] for r in rows if r["level"] > 0}


async def set_structure_level(
    user_id: int,
    guild_id: int,
    structure: str,
    level: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Set the *absolute* built level for *structure* (clamped to ``>= 0``).

    Absolute (not a delta) so the service computes the validated target and this
    primitive just persists it; with *conn* given the upsert runs on that
    connection so the caller's transaction owns commit (the build atomicity).
    """
    await pool.execute(
        _SET_LEVEL_SQL,
        (user_id, guild_id, structure, level),
        conn=conn,
    )
