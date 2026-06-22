"""guild_treasury CRUD — the per-guild server-owned coin pool (migration 092).

The collective counterpart to per-user coins (:mod:`utils.db.economy`): one row
per guild holding the shared balance. Plain CRUD only; the audited
contribute/disburse policy lives in :mod:`services.treasury_service`, and the
per-user coin legs route through :mod:`services.economy_service`.

Transaction-aware (the Q-0071 precedent): the write primitives take an optional
``conn`` so the treasury service can compose the pool-balance leg with the user
coin leg on ONE connection. With ``conn`` given a primitive must never open its
own transaction — the caller owns commit/rollback.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from utils.db import pool

if TYPE_CHECKING:
    import asyncpg


async def get_treasury(
    guild_id: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> int:
    """The guild's stored treasury balance (0 when no row exists yet)."""
    row = await pool.fetchone(
        "SELECT balance FROM guild_treasury WHERE guild_id=$1",
        (guild_id,),
        conn=conn,
    )
    return row["balance"] if row else 0


async def credit_treasury(
    guild_id: int,
    amount: int,
    updated_at: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> int:
    """Add *amount* to the pool and return the new balance in one statement.

    Upsert with a ``GREATEST(0, …)`` floor (mirrors :func:`utils.db.economy.
    credit_coins`) so a fresh guild's first contribution creates the row.
    Transaction-aware (Q-0071): pass *conn* to join a workflow transaction.
    """
    row = await pool.fetchone(
        """INSERT INTO guild_treasury (guild_id, balance, updated_at)
             VALUES ($1, GREATEST(0, $2), $3)
           ON CONFLICT (guild_id) DO UPDATE SET
               balance = GREATEST(0, guild_treasury.balance + $2),
               updated_at = $3
           RETURNING balance""",
        (guild_id, amount, updated_at),
        conn=conn,
    )
    return row["balance"] if row else 0


async def try_debit_treasury(
    guild_id: int,
    amount: int,
    updated_at: int,
    *,
    conn: asyncpg.Connection | None = None,
) -> int | None:
    """Conditionally subtract *amount* from the pool; ``None`` when underfunded.

    The conditional UPDATE (``balance >= $2``) decides sufficiency and writes in
    one statement — no read-then-write race, and a guild with no row (or too
    small a balance) matches nothing and yields ``None`` without writing.
    Mirrors :func:`utils.db.economy.try_debit_coins`. Transaction-aware (Q-0071).
    """
    row = await pool.fetchone(
        """UPDATE guild_treasury
             SET balance = guild_treasury.balance - $2,
                 updated_at = $3
           WHERE guild_id=$1 AND balance >= $2
           RETURNING balance""",
        (guild_id, amount, updated_at),
        conn=conn,
    )
    return row["balance"] if row else None
