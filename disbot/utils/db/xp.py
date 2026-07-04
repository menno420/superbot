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


def total_xp_for_level(level: int) -> int:
    """Cumulative XP required to *reach* ``level`` — the inverse of
    :func:`level_progress`.

    ``level_progress(total_xp_for_level(L)) == (L, 0, xp_for_level(L))`` for
    every ``L >= 0``: this returns the exact XP total that places a member at
    the *start* of level ``L``.  The bot-to-bot migration seam
    (``services.xp_service.import_level``) uses it to turn a scraped/exported
    "reached level N" into a concrete XP value.
    """
    if level <= 0:
        return 0
    return sum(xp_for_level(k) for k in range(level))


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


async def set_imported_xp(
    user_id: int,
    guild_id: int,
    xp: int,
    level: int,
    now: int,
) -> tuple[int, int, bool]:
    """Raise-only absolute XP set for bot-to-bot migration.

    Upserts an absolute ``(xp, level)`` pair but **never lowers** an existing
    row: the merge keeps whichever total XP is larger, and the stored level
    follows that same total (so xp/level stay consistent).  Returns
    ``(final_xp, final_level, raised)`` where ``raised`` is True when the
    import increased the member's XP.

    Unlike :func:`add_xp` this does **not** touch ``messages`` (an imported
    member has not messaged in this guild) or ``last_xp``/``coins`` on an
    existing row, and it is idempotent — re-running the same import is a
    no-op.  Routed exclusively through ``services.xp_service.import_level``
    (INV-G); the whole operation is a single atomic statement so it is safe
    to fan a batch import across it.
    """
    row = await pool.get().fetchrow(
        """WITH prev AS (
               SELECT xp AS old_xp FROM xp WHERE user_id=$1 AND guild_id=$2
           )
           INSERT INTO xp (user_id, guild_id, xp, level, messages, last_xp)
           VALUES ($1, $2, $3, $4, 0, $5)
           ON CONFLICT (user_id, guild_id) DO UPDATE SET
               xp    = GREATEST(xp.xp, EXCLUDED.xp),
               level = CASE WHEN EXCLUDED.xp > xp.xp
                            THEN EXCLUDED.level ELSE xp.level END
           RETURNING xp AS new_xp, level AS new_level,
                     COALESCE((SELECT old_xp FROM prev), -1) AS old_xp""",
        user_id,
        guild_id,
        xp,
        level,
        now,
    )
    new_xp = int(row["new_xp"])
    new_level = int(row["new_level"])
    old_xp = int(row["old_xp"])
    return new_xp, new_level, new_xp > old_xp


async def delete_xp(user_id: int, guild_id: int) -> None:
    """Remove a user's XP row entirely.

    Wrap through ``services.xp_service.reset`` for new code so
    EVT_XP_RESET fires.
    """
    await pool.execute(
        "DELETE FROM xp WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
    )


async def get_guild_xp_totals(guild_id: int) -> tuple[int, int]:
    """Return ``(total_xp, total_coins)`` summed over the guild's xp rows."""
    row = await pool.fetchone(
        "SELECT COALESCE(SUM(xp), 0) AS total_xp, "
        "COALESCE(SUM(coins), 0) AS total_coins "
        "FROM xp WHERE guild_id=$1",
        (guild_id,),
    )
    if row is None:
        return 0, 0
    return int(row["total_xp"]), int(row["total_coins"])
