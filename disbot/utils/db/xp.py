"""XP table CRUD + level math.

Atomic ``add_xp`` is the primary mutation primitive — wrap it through
``services.xp_service.award`` for new code so EVT_XP_AWARDED /
EVT_LEVEL_UP fire and audit attribution is recorded.  Direct callers
still exist (e.g. xp_cog.on_message) and the function remains supported
as the implementation hook.
"""

from __future__ import annotations

from utils.db import pool


def xp_for_level(level: int) -> int:
    return 5 * (level**2) + 50 * level + 100


def level_progress(total_xp: int) -> tuple[int, int, int]:
    level = 0
    remaining = total_xp
    while True:
        needed = xp_for_level(level)
        if remaining < needed:
            return level, remaining, needed
        remaining -= needed
        level += 1


async def get_xp(user_id: int, guild_id: int) -> dict:
    row = await pool.fetchone(
        "SELECT * FROM xp WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
    )
    return row or {
        "user_id": user_id,
        "guild_id": guild_id,
        "xp": 0,
        "level": 0,
        "messages": 0,
        "last_xp": 0,
        "coins": 0,
    }


async def add_xp(
    user_id: int,
    guild_id: int,
    amount: int,
    now: int,
) -> tuple[int, int, bool]:
    """Atomic XP increment.

    The upsert + RETURNING avoids the read-modify-write race that
    concurrent on_message handlers would otherwise hit.  Level is
    re-derived from the returned total and monotonically advanced (the
    second UPDATE only fires when the new level is higher, preventing
    regression under any race).
    """
    row = await pool.get().fetchrow(
        """INSERT INTO xp (user_id, guild_id, xp, level, messages, last_xp)
           VALUES ($1, $2, $3, 0, 1, $4)
           ON CONFLICT (user_id, guild_id) DO UPDATE SET
               xp       = xp.xp + $3,
               messages = xp.messages + 1,
               last_xp  = $4
           RETURNING xp, level""",
        user_id,
        guild_id,
        amount,
        now,
    )
    new_xp = row["xp"]
    old_level = row["level"]
    new_level, _, _ = level_progress(new_xp)
    leveled_up = new_level > old_level
    if leveled_up:
        await pool.execute(
            "UPDATE xp SET level=$3 WHERE user_id=$1 AND guild_id=$2 AND level < $3",
            (user_id, guild_id, new_level),
        )
    return new_xp, new_level, leveled_up


async def delete_xp(user_id: int, guild_id: int) -> None:
    """Remove a user's XP row entirely.

    Wrap through ``services.xp_service.reset`` for new code so
    EVT_XP_RESET fires.
    """
    await pool.execute(
        "DELETE FROM xp WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
    )
