"""Treasury service — the audited write boundary for the server-owned coin pool.

The bot's economy is otherwise entirely *individual* (per-user ``xp.coins``).
The treasury is the collective layer that sits in the gap between the **economy**
(where coins come from) and **governance** (who may spend them):

* **contribute** — any member donates their own coins into the guild pool (a coin
  sink). Debits the user, credits the treasury.
* **disburse** — a server manager grants coins from the pool to a member (a
  governance-gated faucet). Debits the treasury, credits the user.

Mirrors the game workflows (RS02 / Q-0071): every coin-moving op runs the
treasury-row write + the user coin leg inside ONE ``db.transaction()`` connection
via the conn-aware ``utils/db`` and ``economy_service.*_in_txn`` primitives; the
EventBus emission happens **after** commit. The per-user coin legs are audited by
``economy_service`` (``economy_audit_log`` is the money trail), exactly as the
farm/fishing/mining sinks are — the treasury row is the domain-inventory leg.

Authority note: this service performs **no permission check** — that is the
caller's responsibility (the cog gates ``disburse`` on ``manage_guild`` and the
view re-checks at callback time). The service only enforces value/affordability
invariants, so a missing gate can never silently mint coins.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from core.events import bus
from services import economy_service
from utils import db

logger = logging.getLogger("bot.treasury_service")

#: Audit/event reason tags (mirrors "<domain>:<action>").
CONTRIBUTE_REASON = "treasury:contribute"
DISBURSE_REASON = "treasury:disburse"


class _TreasuryUnderfundedError(Exception):
    """Internal: the pool can't cover a disburse. Carries the available balance.

    Raised inside the transaction (before the user is credited) so the context
    exits with nothing committed; the public :func:`disburse` catches it and
    returns a failure result. Never escapes this module.
    """

    def __init__(self, available: int) -> None:
        super().__init__(f"treasury underfunded: has {available}")
        self.available = available


async def get_balance(guild_id: int) -> int:
    """The guild's current treasury balance (read-only)."""
    return await db.get_treasury(guild_id)


@dataclass(frozen=True)
class TreasuryResult:
    """The outcome of a contribute/disburse — flag, message, and balances."""

    success: bool
    message: str
    treasury_balance: int | None = None
    user_balance: int | None = None


async def contribute(guild_id: int, user_id: int, amount: int) -> TreasuryResult:
    """Donate *amount* of the user's coins into the guild treasury.

    Debits the user (the debit audits itself via ``debit_in_txn``) and credits
    the pool inside ONE transaction; insufficient funds rolls everything back.
    The balance-changed event emits after commit.
    """
    if amount <= 0:
        msg = f"contribute amount must be positive, got {amount}"
        raise ValueError(msg)
    now = int(time.time())
    try:
        async with db.transaction() as conn:
            user_balance = await economy_service.debit_in_txn(
                conn,
                guild_id,
                user_id,
                amount,
                reason=CONTRIBUTE_REASON,
                actor_id=user_id,
            )
            treasury_balance = await db.credit_treasury(
                guild_id,
                amount,
                now,
                conn=conn,
            )
    except economy_service.InsufficientFundsError:
        balance = await db.get_coins(user_id, guild_id)
        return TreasuryResult(
            False,
            f"🏛️ Contributing **{amount}** 🪙 is more than your **{balance}** 🪙.",
        )

    await bus.emit(
        economy_service.EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=user_id,
        delta=-amount,
        new_balance=user_balance,
        reason=CONTRIBUTE_REASON,
    )
    return TreasuryResult(
        True,
        f"🏛️ Contributed **{amount}** 🪙 to the treasury — it now holds "
        f"**{treasury_balance}** 🪙. Your balance: **{user_balance}** 🪙.",
        treasury_balance=treasury_balance,
        user_balance=user_balance,
    )


async def disburse(
    guild_id: int,
    actor_id: int,
    target_id: int,
    amount: int,
) -> TreasuryResult:
    """Grant *amount* from the treasury to *target_id* (a governance action).

    Authority is the caller's responsibility — this only moves coins. Debits the
    pool (conditional: never overdraws) and credits the target inside ONE
    transaction; an underfunded pool writes nothing and returns a failure. The
    balance-changed event emits after commit. ``actor_id`` is recorded on the
    target's audit row so the grant stays attributable to the manager who ran it.
    """
    if amount <= 0:
        msg = f"disburse amount must be positive, got {amount}"
        raise ValueError(msg)
    now = int(time.time())
    try:
        async with db.transaction() as conn:
            new_treasury = await db.try_debit_treasury(
                guild_id,
                amount,
                now,
                conn=conn,
            )
            if new_treasury is None:
                raise _TreasuryUnderfundedError(
                    await db.get_treasury(guild_id, conn=conn),
                )
            user_balance = await economy_service.credit_in_txn(
                conn,
                guild_id,
                target_id,
                amount,
                reason=DISBURSE_REASON,
                actor_id=actor_id,
            )
    except _TreasuryUnderfundedError as exc:
        return TreasuryResult(
            False,
            f"🏛️ The treasury only holds **{exc.available}** 🪙 — "
            f"not enough to disburse **{amount}** 🪙.",
            treasury_balance=exc.available,
        )

    await bus.emit(
        economy_service.EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=target_id,
        delta=amount,
        new_balance=user_balance,
        reason=DISBURSE_REASON,
    )
    return TreasuryResult(
        True,
        f"🏛️ Disbursed **{amount}** 🪙 from the treasury — it now holds "
        f"**{new_treasury}** 🪙.",
        treasury_balance=new_treasury,
        user_balance=user_balance,
    )
