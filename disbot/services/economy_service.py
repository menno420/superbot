"""Economy service — the only path through which coin balances mutate.

Addresses CRIT-9 from the platform-hardening plan.  Previously
``economy_cog``, ``blackjack_cog``, ``rps_tournament_cog`` and
``proof_channel_cog`` each mutated ``xp.coins`` directly via
``db.add_coins`` / ``db.set_coins`` — no shared audit trail, no event,
no place to enforce overdraft policy.

Every public function here:

1. Performs the balance write atomically (asyncpg UPDATE with a single
   transaction when more than one row is touched).
2. Inserts an immutable row in ``economy_audit_log`` recording delta,
   actor, and reason.
3. Emits ``EVT_BALANCE_CHANGED`` on the EventBus so subscribers
   (panel-refresh scheduler, future analytics) can react without
   reaching into the DB.

Public API
----------
- ``credit(guild_id, user_id, amount, *, reason, actor_id=None)``
- ``debit(guild_id, user_id, amount, *, reason, actor_id=None,
          allow_overdraft=False)``
- ``transfer(guild_id, from_user, to_user, amount, *, reason,
             actor_id=None)``
- ``bet_and_settle(guild_id, user_id, bet, outcome_delta, *, reason,
                   actor_id=None)``

All amounts are non-negative.  ``debit`` and ``transfer`` raise
:class:`InsufficientFundsError` when the user cannot afford the move
unless ``allow_overdraft=True`` is passed.
"""

from __future__ import annotations

import logging

from core.events import bus
from utils import db

logger = logging.getLogger("bot.economy_service")

# Event name — also listed in core/events_catalogue.KNOWN_EVENTS.
EVT_BALANCE_CHANGED = "economy.balance_changed"


class InsufficientFundsError(RuntimeError):
    """Raised when a debit/transfer would overdraw a user's balance."""


async def credit(
    guild_id: int,
    user_id: int,
    amount: int,
    *,
    reason: str,
    actor_id: int | None = None,
) -> int:
    """Add *amount* coins to *user_id* in *guild_id*; return new balance.

    *amount* must be > 0.  Use :func:`debit` for negative-direction moves.
    """
    if amount <= 0:
        msg = f"credit amount must be positive, got {amount}"
        raise ValueError(msg)
    new_balance = await db.add_coins(user_id, guild_id, amount)
    await _audit(guild_id, user_id, actor_id, amount, new_balance, reason)
    await bus.emit(
        EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=user_id,
        delta=amount,
        new_balance=new_balance,
        reason=reason,
    )
    return new_balance


async def debit(
    guild_id: int,
    user_id: int,
    amount: int,
    *,
    reason: str,
    actor_id: int | None = None,
    allow_overdraft: bool = False,
) -> int:
    """Subtract *amount* coins from *user_id*; return new balance.

    *amount* must be > 0.  Raises :class:`InsufficientFundsError` if the
    balance would go negative unless *allow_overdraft* is true (which
    floors at zero, matching the existing ``db.add_coins`` GREATEST(0, …)
    semantics).
    """
    if amount <= 0:
        msg = f"debit amount must be positive, got {amount}"
        raise ValueError(msg)
    current = await db.get_coins(user_id, guild_id)
    if current < amount and not allow_overdraft:
        raise InsufficientFundsError(
            f"user={user_id} has {current} coins, needs {amount}",
        )
    new_balance = await db.add_coins(user_id, guild_id, -amount)
    await _audit(guild_id, user_id, actor_id, -amount, new_balance, reason)
    await bus.emit(
        EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=user_id,
        delta=-amount,
        new_balance=new_balance,
        reason=reason,
    )
    return new_balance


async def transfer(
    guild_id: int,
    from_user: int,
    to_user: int,
    amount: int,
    *,
    reason: str,
    actor_id: int | None = None,
) -> tuple[int, int]:
    """Move *amount* coins from one user to another atomically.

    Returns ``(new_from_balance, new_to_balance)``.  Raises
    :class:`InsufficientFundsError` if *from_user* cannot afford it.

    The two writes run inside one asyncpg transaction so an
    intermediate failure cannot leave the source debited without
    crediting the destination.
    """
    if amount <= 0:
        msg = f"transfer amount must be positive, got {amount}"
        raise ValueError(msg)
    if from_user == to_user:
        msg = "transfer from_user and to_user must differ"
        raise ValueError(msg)
    pool = db.get()
    async with pool.acquire() as conn, conn.transaction():
        row = await conn.fetchrow(
            "SELECT coins FROM xp WHERE user_id=$1 AND guild_id=$2",
            from_user,
            guild_id,
        )
        current = row["coins"] if row else 0
        if current < amount:
            raise InsufficientFundsError(
                f"user={from_user} has {current} coins, needs {amount}",
            )
        from_row = await conn.fetchrow(
            """INSERT INTO xp (user_id, guild_id, coins) VALUES ($1, $2, 0)
               ON CONFLICT (user_id, guild_id) DO UPDATE
                 SET coins = GREATEST(0, xp.coins - $3)
               RETURNING coins""",
            from_user,
            guild_id,
            amount,
        )
        to_row = await conn.fetchrow(
            """INSERT INTO xp (user_id, guild_id, coins)
                 VALUES ($1, $2, GREATEST(0, $3))
               ON CONFLICT (user_id, guild_id) DO UPDATE
                 SET coins = GREATEST(0, xp.coins + $3)
               RETURNING coins""",
            to_user,
            guild_id,
            amount,
        )
        new_from = from_row["coins"]
        new_to = to_row["coins"]
        await conn.execute(
            """INSERT INTO economy_audit_log
                 (guild_id, user_id, actor_id, delta, new_balance, reason)
               VALUES ($1, $2, $3, $4, $5, $6),
                      ($1, $7, $3, $8, $9, $6)""",
            guild_id,
            from_user,
            actor_id,
            -amount,
            new_from,
            reason,
            to_user,
            amount,
            new_to,
        )

    # Emit outside the transaction — subscribers should not block commit.
    await bus.emit(
        EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=from_user,
        delta=-amount,
        new_balance=new_from,
        reason=reason,
    )
    await bus.emit(
        EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=to_user,
        delta=amount,
        new_balance=new_to,
        reason=reason,
    )
    return new_from, new_to


async def bet_and_settle(
    guild_id: int,
    user_id: int,
    bet: int,
    outcome_delta: int,
    *,
    reason: str,
    actor_id: int | None = None,
) -> int:
    """Place a bet and apply an outcome delta in a single audit-logged op.

    *bet* is the wagered amount (non-negative).  *outcome_delta* is the
    net change after settlement (positive = win, including the original
    stake; negative = loss).  The audit row records the net delta with
    the supplied reason so analytics can recover both stake and result
    from the row history if needed.

    Returns the new balance.  Raises :class:`InsufficientFundsError` if
    the user cannot afford the bet.
    """
    if bet < 0:
        msg = f"bet must be >= 0, got {bet}"
        raise ValueError(msg)
    current = await db.get_coins(user_id, guild_id)
    if current < bet:
        raise InsufficientFundsError(
            f"user={user_id} has {current} coins, needs {bet}",
        )
    new_balance = await db.add_coins(user_id, guild_id, outcome_delta)
    await _audit(guild_id, user_id, actor_id, outcome_delta, new_balance, reason)
    await bus.emit(
        EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=user_id,
        delta=outcome_delta,
        new_balance=new_balance,
        reason=reason,
    )
    return new_balance


async def refund(
    guild_id: int,
    user_id: int,
    amount: int,
    *,
    reason: str,
    actor_id: int | None = None,
) -> int:
    """Return *amount* coins to *user_id* — alias for :func:`credit`.

    Distinct entry point so audit-log readers can filter on
    ``reason LIKE '%:refund:%'`` to recover money-flow events caused
    by graceful shutdowns or interrupted games (e.g. blackjack hand
    cancelled by restart).

    The audit row's reason field captures the original transaction
    context so refunds remain attributable.
    """
    return await credit(
        guild_id=guild_id,
        user_id=user_id,
        amount=amount,
        reason=reason,
        actor_id=actor_id,
    )


async def _audit(
    guild_id: int,
    user_id: int,
    actor_id: int | None,
    delta: int,
    new_balance: int,
    reason: str,
) -> None:
    """Append a row to economy_audit_log."""
    await db.execute(
        """INSERT INTO economy_audit_log
             (guild_id, user_id, actor_id, delta, new_balance, reason)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        (guild_id, user_id, actor_id, delta, new_balance, reason),
    )
