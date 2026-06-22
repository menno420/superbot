"""Karma table CRUD: per-user reputation totals + append-only audit log.

Karma mutations are deliberately kept low-level here — see
:mod:`services.karma_service` for the audited public path (the only
allowed caller of :func:`credit_karma` / :func:`insert_karma_audit`,
enforced by INV-K).  The audit log doubles as the anti-abuse source of
truth: :func:`recent_grant_count` and :func:`grants_given_since` answer
the cooldown and daily-cap questions without a separate cooldown table,
mirroring how :mod:`services.economy_flow_service` reads
``economy_audit_log``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    from datetime import datetime

    import asyncpg


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


async def get_karma(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> dict:
    """Return the karma row for *user_id* or an all-zeros synthesised dict.

    A missing row synthesises ``karma_points=received_count=given_count=0``
    (and ``last_received=None``) so callers never branch on ``None`` —
    mirrors ``utils.db.xp.get_xp``.
    """
    row = await pool.fetchone(
        "SELECT karma_points, received_count, given_count, last_received "
        "FROM karma WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    if row is None:
        return {
            "karma_points": 0,
            "received_count": 0,
            "given_count": 0,
            "last_received": None,
        }
    return dict(row)


async def top_karma(
    guild_id: int,
    limit: int = 10,
    *,
    conn: asyncpg.Connection | None = None,
) -> list[dict]:
    """Return up to *limit* members ranked by karma, highest first.

    Oldest ``last_received`` breaks ties so equal totals rank
    deterministically (matches ``idx_karma_guild_points``).
    """
    rows = await pool.fetchall(
        "SELECT user_id, karma_points FROM karma "
        "WHERE guild_id=$1 AND karma_points > 0 "
        "ORDER BY karma_points DESC, last_received ASC "
        "LIMIT $2",
        (guild_id, limit),
        conn=conn,
    )
    return [dict(r) for r in rows]


async def karma_rank(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> int | None:
    """Return the 1-based rank of *user_id* on the karma board, or ``None``.

    ``None`` when the member has no karma row or a non-positive total
    (they are not on the board).
    """
    row = await pool.fetchone(
        """SELECT rank FROM (
               SELECT user_id,
                      ROW_NUMBER() OVER (
                          ORDER BY karma_points DESC, last_received ASC
                      ) AS rank
               FROM karma
               WHERE guild_id=$1 AND karma_points > 0
           ) ranked
           WHERE user_id=$2""",
        (guild_id, user_id),
        conn=conn,
    )
    return int(row["rank"]) if row else None


# ---------------------------------------------------------------------------
# Anti-abuse reads (over the audit log)
# ---------------------------------------------------------------------------


async def recent_grant_count(
    guild_id: int,
    from_user: int,
    to_user: int,
    since: datetime,
    *,
    conn: asyncpg.Connection | None = None,
) -> int:
    """Count grants from *from_user* to *to_user* at/after *since*.

    Backs the per-(giver -> receiver) cooldown: a non-zero count means
    the giver already thanked this recipient within the window.
    """
    row = await pool.fetchone(
        "SELECT COUNT(*)::bigint AS n FROM karma_audit_log "
        "WHERE guild_id=$1 AND from_user=$2 AND to_user=$3 "
        "AND occurred_at >= $4",
        (guild_id, from_user, to_user, since),
        conn=conn,
    )
    return int(row["n"]) if row else 0


async def grants_given_since(
    guild_id: int,
    from_user: int,
    since: datetime,
    *,
    conn: asyncpg.Connection | None = None,
) -> int:
    """Count total grants made by *from_user* at/after *since*.

    Backs the per-giver daily cap (call with the start of the giver's
    rolling day window).
    """
    row = await pool.fetchone(
        "SELECT COUNT(*)::bigint AS n FROM karma_audit_log "
        "WHERE guild_id=$1 AND from_user=$2 AND occurred_at >= $3",
        (guild_id, from_user, since),
        conn=conn,
    )
    return int(row["n"]) if row else 0


# ---------------------------------------------------------------------------
# Write primitives — wrap via services.karma_service for audited writes.
# ---------------------------------------------------------------------------


async def credit_karma(
    to_user: int,
    guild_id: int,
    amount: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> int:
    """Add *amount* karma to *to_user* and return the new total.

    Upsert + ``RETURNING`` in one statement (no read-then-write race).
    Bumps ``received_count`` and stamps ``last_received=NOW()`` on every
    grant; the total floors at zero (``GREATEST(0, …)``) so a future
    downvote can never drive it negative.
    """
    row = await pool.fetchone(
        """INSERT INTO karma
               (user_id, guild_id, karma_points, received_count, last_received)
           VALUES ($1, $2, GREATEST(0, $3), 1, NOW())
           ON CONFLICT (user_id, guild_id) DO UPDATE SET
               karma_points   = GREATEST(0, karma.karma_points + $3),
               received_count = karma.received_count + 1,
               last_received  = NOW()
           RETURNING karma_points""",
        (to_user, guild_id, amount),
        conn=conn,
    )
    return row["karma_points"] if row else 0


async def increment_given(
    from_user: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Bump *from_user*'s lifetime ``given_count`` by one (upsert)."""
    await pool.execute(
        """INSERT INTO karma (user_id, guild_id, given_count)
           VALUES ($1, $2, 1)
           ON CONFLICT (user_id, guild_id) DO UPDATE SET
               given_count = karma.given_count + 1""",
        (from_user, guild_id),
        conn=conn,
    )


async def insert_karma_audit(
    guild_id: int,
    from_user: int,
    to_user: int,
    delta: int,
    source: str,
    reason: str | None,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Append one immutable row to ``karma_audit_log``."""
    await pool.execute(
        """INSERT INTO karma_audit_log
             (guild_id, from_user, to_user, delta, source, reason)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        (guild_id, from_user, to_user, delta, source, reason),
        conn=conn,
    )
