"""player_skills CRUD — a player's allocated skill-tree points (brainstorm §7.4).

One row per ``(user_id, guild_id, branch)``.  ``user_id`` is ``BIGINT`` to match
``game_xp`` (skill points are spent from the shared game-XP level), not
``mining_inventory``'s legacy ``TEXT`` column.

The write primitive ``set_skill_points`` takes an optional ``conn`` so
``services/skill_service.py`` can clear/allocate inside ONE transaction with the
coin debit (respec) — neither leg ever commits alone.  Reads (``get_skills``)
stay free for panels.  Like ``add_game_xp`` and the mining write primitives,
``set_skill_points`` is on the RS02 write-boundary ratchet
(``tests/unit/invariants/test_mining_write_boundary.py``) — only the owning
service may call it, never a cog or view.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg

_SET_POINTS_SQL = """INSERT INTO player_skills (user_id, guild_id, branch, points)
           VALUES ($1, $2, $3, GREATEST(0, $4))
           ON CONFLICT (user_id, guild_id, branch)
           DO UPDATE SET points = GREATEST(0, $4)"""


async def get_skills(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> dict[str, int]:
    """The player's allocated points per branch — ``{branch: points}``.

    Zero-point branches are filtered out so callers see only spent branches; an
    unspent player reads as ``{}`` (which maps to all-zero stats).
    """
    rows = await pool.fetchall(
        "SELECT branch, points FROM player_skills WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return {r["branch"]: r["points"] for r in rows if r["points"] > 0}


async def set_skill_points(
    user_id: int,
    guild_id: int,
    branch: str,
    points: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Set the *absolute* allocated points for *branch* (clamped to ``>= 0``).

    Absolute (not a delta) so the service computes the validated target and this
    primitive just persists it; with *conn* given the upsert runs on that
    connection so the caller's transaction owns commit (the respec atomicity).
    """
    await pool.execute(
        _SET_POINTS_SQL,
        (user_id, guild_id, branch, points),
        conn=conn,
    )
