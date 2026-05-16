"""Economy table CRUD: coins, daily/work tracking, job progress.

Coin mutations are deliberately kept low-level here — see
:mod:`services.economy_service` for the audited public path.  Direct
callers that pre-date the service layer still exist and the primitives
remain supported.
"""

from __future__ import annotations

from utils.db import pool

# ---------------------------------------------------------------------------
# Coin primitives — wrap via services.economy_service for audited writes.
# ---------------------------------------------------------------------------


async def get_coins(user_id: int, guild_id: int) -> int:
    row = await pool.fetchone(
        "SELECT coins FROM xp WHERE user_id=$1 AND guild_id=$2",
        (user_id, guild_id),
    )
    return row["coins"] if row else 0


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


async def get_economy(user_id: int, guild_id: int) -> dict:
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


async def set_economy(user_id: int, guild_id: int, **kwargs) -> None:
    allowed = {"last_daily", "daily_streak", "daily_count", "last_worked"}
    cols = {k: v for k, v in kwargs.items() if k in allowed}
    if not cols:
        return
    keys = list(cols)
    sets = ", ".join(f"{k}=${i + 1}" for i, k in enumerate(keys))
    n = len(keys)
    await pool.execute(
        f"UPDATE economy SET {sets} WHERE user_id=${n + 1} AND guild_id=${n + 2}",
        (*cols.values(), user_id, guild_id),
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
