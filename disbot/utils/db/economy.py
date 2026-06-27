"""Economy table CRUD: coins, daily/work tracking, job progress.

Coin mutations are deliberately kept low-level here — see
:mod:`services.economy_service` for the audited public path.  Direct
callers that pre-date the service layer still exist and the primitives
remain supported.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    from datetime import date, datetime

    import asyncpg

# ---------------------------------------------------------------------------
# Coin primitives — wrap via services.economy_service for audited writes.
# ---------------------------------------------------------------------------


async def get_coins(
    user_id: int,
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> int:
    row = await pool.fetchone(
        "SELECT coins FROM xp WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
        conn=conn,
    )
    return row["coins"] if row else 0


async def try_debit_coins(
    user_id: int,
    guild_id: int,
    amount: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> int | None:
    """Conditionally subtract *amount* coins; ``None`` when unaffordable.

    The conditional UPDATE (``coins >= $3``) decides affordability and
    writes in one statement, eliminating the read-then-write race of the
    legacy ``get_coins`` + ``add_coins`` pair.  A user with no ``xp`` row
    matches nothing and is treated as having 0 coins.  Transaction-aware
    (Q-0071): pass *conn* to join a workflow-owned transaction.
    """
    row = await pool.fetchone(
        """UPDATE xp SET coins = xp.coins - $3
           WHERE user_id=$1 AND guild_id=$2 AND coins >= $3
           RETURNING coins""",
        (user_id, guild_id, amount),
        conn=conn,
    )
    return row["coins"] if row else None


async def credit_coins(
    user_id: int,
    guild_id: int,
    amount: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> int:
    """Add *amount* coins and return the new balance in one statement.

    Transaction-aware (Q-0071) sibling of :func:`add_coins` — same upsert
    semantics (`GREATEST(0, …)` floor) plus ``RETURNING`` so callers
    inside a workflow transaction never need a follow-up read.
    """
    row = await pool.fetchone(
        """INSERT INTO xp (user_id, guild_id, coins) VALUES ($1, $2, GREATEST(0, $3))
           ON CONFLICT (user_id, guild_id) DO UPDATE SET
               coins=GREATEST(0, xp.coins + $3)
           RETURNING coins""",
        (user_id, guild_id, amount),
        conn=conn,
    )
    return row["coins"] if row else 0


async def insert_economy_audit(
    guild_id: int,
    user_id: int,
    actor_id: int | None,
    delta: int,
    new_balance: int,
    reason: str,
    *,
    conn: asyncpg.Connection | None = None,
) -> None:
    """Append one row to ``economy_audit_log`` (transaction-aware)."""
    await pool.execute(
        """INSERT INTO economy_audit_log
             (guild_id, user_id, actor_id, delta, new_balance, reason)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        (guild_id, user_id, actor_id, delta, new_balance, reason),
        conn=conn,
    )


async def economy_flow_by_reason(
    guild_id: int,
    *,
    since: datetime | None = None,
    conn: asyncpg.Connection | None = None,
) -> list[tuple[str, int, int]]:
    """Per-reason ``(reason, net_delta, movement_count)`` over the audit log.

    Pure read — aggregates ``economy_audit_log`` for one guild into one row
    per ``reason`` (the summed signed delta and the number of movements).
    A positive net is a faucet (net mint), a negative net a sink (net drain);
    the caller classifies by sign. ``since`` filters by the row timestamp
    (``occurred_at``); omit it for the all-time view. Rows with a NULL reason
    are folded under the literal ``"(unspecified)"`` so they are never dropped.
    """
    if since is None:
        rows = await pool.fetchall(
            """SELECT COALESCE(reason, '(unspecified)') AS reason,
                      SUM(delta)::bigint AS net,
                      COUNT(*)::bigint   AS n
               FROM economy_audit_log
               WHERE guild_id=$1
               GROUP BY COALESCE(reason, '(unspecified)')
               ORDER BY net DESC""",
            (guild_id,),
            conn=conn,
        )
    else:
        rows = await pool.fetchall(
            """SELECT COALESCE(reason, '(unspecified)') AS reason,
                      SUM(delta)::bigint AS net,
                      COUNT(*)::bigint   AS n
               FROM economy_audit_log
               WHERE guild_id=$1 AND occurred_at >= $2
               GROUP BY COALESCE(reason, '(unspecified)')
               ORDER BY net DESC""",
            (guild_id, since),
            conn=conn,
        )
    return [(r["reason"], int(r["net"]), int(r["n"])) for r in rows]


async def economy_flow_daily(
    guild_id: int,
    *,
    since: datetime | None = None,
    conn: asyncpg.Connection | None = None,
) -> list[tuple[date, int, int, int, int]]:
    """Per-UTC-day ``(day, minted, drained, net, movements)`` over the audit log.

    Pure read — the time-series sibling of :func:`economy_flow_by_reason`.
    Aggregates ``economy_audit_log`` for one guild into one row per calendar day
    (UTC, so a day boundary is deterministic regardless of the server timezone):
    coins minted (sum of positive deltas), coins drained (sum of negative deltas
    as a positive magnitude), net (signed), and the movement count. ``since``
    filters by ``occurred_at``; omit for all recorded days. Rows are ordered
    **oldest-first** so the caller reads them left-to-right as a trend.
    """
    if since is None:
        rows = await pool.fetchall(
            """SELECT (occurred_at AT TIME ZONE 'UTC')::date              AS day,
                      COALESCE(SUM(delta) FILTER (WHERE delta > 0), 0)::bigint  AS minted,
                      COALESCE(SUM(-delta) FILTER (WHERE delta < 0), 0)::bigint AS drained,
                      SUM(delta)::bigint                                  AS net,
                      COUNT(*)::bigint                                    AS n
               FROM economy_audit_log
               WHERE guild_id=$1
               GROUP BY day
               ORDER BY day ASC""",
            (guild_id,),
            conn=conn,
        )
    else:
        rows = await pool.fetchall(
            """SELECT (occurred_at AT TIME ZONE 'UTC')::date              AS day,
                      COALESCE(SUM(delta) FILTER (WHERE delta > 0), 0)::bigint  AS minted,
                      COALESCE(SUM(-delta) FILTER (WHERE delta < 0), 0)::bigint AS drained,
                      SUM(delta)::bigint                                  AS net,
                      COUNT(*)::bigint                                    AS n
               FROM economy_audit_log
               WHERE guild_id=$1 AND occurred_at >= $2
               GROUP BY day
               ORDER BY day ASC""",
            (guild_id, since),
            conn=conn,
        )
    return [
        (r["day"], int(r["minted"]), int(r["drained"]), int(r["net"]), int(r["n"]))
        for r in rows
    ]


async def add_coins(user_id: int, guild_id: int, amount: int) -> int:
    await pool.execute(
        """INSERT INTO xp (user_id, guild_id, coins) VALUES ($1, $2, GREATEST(0, $3))
           ON CONFLICT (user_id, guild_id) DO UPDATE SET
               coins=GREATEST(0, xp.coins + $3)""",
        (user_id, guild_id, amount),
    )
    return await get_coins(user_id, guild_id)


async def set_coins(user_id: int, guild_id: int, amount: int) -> None:
    await pool.execute(
        """INSERT INTO xp (user_id, guild_id, coins) VALUES ($1, $2, GREATEST(0, $3))
           ON CONFLICT (user_id, guild_id) DO UPDATE
             SET coins=GREATEST(0, EXCLUDED.coins)""",
        (user_id, guild_id, amount),
    )


# ---------------------------------------------------------------------------
# Economy table (daily/work tracking)
# ---------------------------------------------------------------------------


async def ensure_and_get_economy(user_id: int, guild_id: int) -> dict:
    """Ensure the ``economy`` row exists, then return it.

    NOT a pure read — the name says so: a missing row is INSERTed
    (with column defaults) before the SELECT, so calling this for a
    user who has never used the economy creates their row. Renamed
    from ``get_economy`` (2026-06-10), whose name hid the write.
    """
    await pool.execute(
        "INSERT INTO economy (user_id, guild_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
        (user_id, guild_id),
    )
    row = await pool.fetchone(
        "SELECT * FROM economy WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
    )
    return dict(row)


async def claim_daily_if_ready(
    user_id: int,
    guild_id: int,
    now: int,
    cooldown_seconds: int,
) -> bool:
    """Atomically claim daily reward.

    Updates last_daily only when the cooldown has elapsed.  Returns
    True if the claim succeeded, False if the user is still on
    cooldown.  Using a conditional UPDATE eliminates the
    read-then-write race that allowed concurrent !daily invocations to
    both succeed.
    """
    result = await pool.get().execute(
        """UPDATE economy SET last_daily=$3
           WHERE user_id=$1 AND guild_id=$2
             AND ($3 - last_daily) >= $4""",
        user_id,
        guild_id,
        now,
        cooldown_seconds,
    )
    return result == "UPDATE 1"


async def set_last_worked(user_id: int, guild_id: int, ts: int) -> None:
    """Record the user's most recent successful work.

    Replaces the kwargs+f-string ``set_economy`` (PR R2): one explicit
    update statement, no dynamic SQL identifier interpolation.
    """
    await pool.execute(
        "UPDATE economy SET last_worked=$1 WHERE user_id=$2 AND guild_id=$3",
        (ts, user_id, guild_id),
    )


async def set_daily_claim(
    user_id: int,
    guild_id: int,
    last_daily: int,
    daily_streak: int,
    daily_count: int,
) -> None:
    """Record a daily-claim completion atomically.

    The three columns (``last_daily``, ``daily_streak``, ``daily_count``)
    are always written together — this single statement preserves the
    atomicity the previous ``set_economy`` provided, without the
    dynamic-SQL pattern.
    """
    await pool.execute(
        "UPDATE economy "
        "   SET last_daily=$1, daily_streak=$2, daily_count=$3 "
        " WHERE user_id=$4 AND guild_id=$5",
        (last_daily, daily_streak, daily_count, user_id, guild_id),
    )


# ---------------------------------------------------------------------------
# Job progress
# ---------------------------------------------------------------------------


async def get_job_times(user_id: int, guild_id: int, job_name: str) -> int:
    row = await pool.fetchone(
        "SELECT times_worked FROM job_progress "
        "WHERE user_id=$1 AND guild_id=$2 AND job_name=$3",
        (user_id, guild_id, job_name),
    )
    return row["times_worked"] if row else 0


async def increment_job(user_id: int, guild_id: int, job_name: str) -> int:
    """Atomically increment the times_worked counter and return the new value.

    Single INSERT ... ON CONFLICT DO UPDATE ... RETURNING avoids the
    read-after-write race between the upsert and a separate SELECT.
    """
    row = await pool.fetchone(
        """INSERT INTO job_progress (user_id, guild_id, job_name, times_worked)
           VALUES ($1, $2, $3, 1)
           ON CONFLICT (user_id, guild_id, job_name)
           DO UPDATE SET times_worked = job_progress.times_worked + 1
           RETURNING times_worked""",
        (user_id, guild_id, job_name),
    )
    return row["times_worked"] if row else 1
