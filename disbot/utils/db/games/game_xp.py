"""game_xp CRUD — the shared cross-game progression track (migration 064).

One row per ``(user_id, guild_id, game)``: per-game XP attribution and the
per-game daily-soft-cap counter.  The player's **shared level** derives from
``SUM(xp)`` through the chat-XP curve (``utils.db.xp.level_progress``) —
there is deliberately no stored level column.  Award policy (amounts, the
soft cap, level events) lives in :mod:`services.game_xp_service`; this
module is plain CRUD.

Transaction-aware (Q-0071): write/read primitives take an optional ``conn``
so :mod:`services.mining_workflow` can commit an XP award atomically with
the action that earned it.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg


async def get_game_xp_row(
    user_id: int,
    guild_id: int,
    game: str,
    *,
    conn: asyncpg.Connection | None = None,
) -> dict:
    """``{xp, day, day_xp}`` for one game row (zeros when absent)."""
    row = await pool.fetchone(
        "SELECT xp, day, day_xp FROM game_xp "
        "WHERE user_id=$1 AND guild_id=$2 AND game=$3",
        (user_id, guild_id, game),
        conn=conn,
    )
    return dict(row) if row else {"xp": 0, "day": None, "day_xp": 0}


async def add_game_xp(
    user_id: int,
    guild_id: int,
    game: str,
    amount: int,
    *,
    day: datetime.date,
    conn: asyncpg.Connection | None = None,
) -> int:
    """Add *amount* XP to one game row; return the row's new total.

    One upsert with day-rollover: ``day_xp`` accumulates while ``day``
    matches and restarts at *amount* on a new day.
    """
    # $4 feeds both xp (BIGINT) and day_xp (INTEGER) — the explicit casts
    # keep asyncpg's parameter-type deduction unambiguous.
    row = await pool.fetchone(
        """INSERT INTO game_xp (user_id, guild_id, game, xp, day, day_xp)
           VALUES ($1, $2, $3, $4::bigint, $5, $4::int)
           ON CONFLICT (user_id, guild_id, game) DO UPDATE SET
               xp = game_xp.xp + $4::bigint,
               day_xp = CASE WHEN game_xp.day = $5
                             THEN game_xp.day_xp + $4::int ELSE $4::int END,
               day = $5,
               updated_at = now()
           RETURNING xp""",
        (user_id, guild_id, game, amount, day),
        conn=conn,
    )
    return row["xp"] if row else amount


async def get_game_xp(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> dict[str, int]:
    """``{game: xp}`` for every game the user has earned XP in."""
    rows = await pool.fetchall(
        "SELECT game, xp FROM game_xp WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return {r["game"]: r["xp"] for r in rows}


async def get_total_xp(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> int:
    """The shared progression total: ``SUM(xp)`` across all games."""
    row = await pool.fetchone(
        "SELECT COALESCE(SUM(xp), 0) AS total FROM game_xp "
        "WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return int(row["total"]) if row else 0


async def top_total_xp(guild_id: int, limit: int = 10) -> list[tuple[int, int]]:
    """``[(user_id, total_xp)]`` for the guild, highest first."""
    rows = await pool.fetchall(
        "SELECT user_id, SUM(xp) AS total FROM game_xp "
        "WHERE guild_id=$1 GROUP BY user_id ORDER BY total DESC LIMIT $2",
        (guild_id, limit),
    )
    return [(r["user_id"], int(r["total"])) for r in rows]


async def top_game_xp(
    guild_id: int,
    game: str,
    limit: int = 10,
) -> list[tuple[int, int]]:
    """``[(user_id, xp)]`` for one game in the guild, highest first."""
    rows = await pool.fetchall(
        "SELECT user_id, xp FROM game_xp "
        "WHERE guild_id=$1 AND game=$2 ORDER BY xp DESC LIMIT $3",
        (guild_id, game, limit),
    )
    return [(r["user_id"], r["xp"]) for r in rows]
