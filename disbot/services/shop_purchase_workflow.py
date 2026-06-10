"""Shop purchase workflow — coins + inventory in ONE transaction (Q-0071).

FIND-RS01: both shop-panel callbacks previously debited coins and granted
the item as two separately-committed legs *from the view* — a mid-flight
failure could charge without granting, and the ``has_item``/``get_coins``
pre-checks were racy (double-click → double charge).  This bounded
workflow owns the purchase end-to-end:

1. One ``db.transaction()`` wraps the unique-item grant and the audited
   debit, so both legs commit or roll back together.
2. The grant runs first (conditional upsert — authoritative ownership
   check); an unaffordable debit then raises and rolls the grant back.
3. ``EVT_BALANCE_CHANGED`` is emitted **after commit**, never inside the
   transaction (the ``economy_service.transfer`` precedent).

Views render copy from the returned :class:`PurchaseResult` flags and
must not write coins or inventory themselves (AST-enforced by
``tests/unit/invariants/test_no_view_level_purchase_writes.py``).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from core.events import bus
from services import economy_service
from utils import db

logger = logging.getLogger("bot.shop_purchase_workflow")


@dataclass(frozen=True)
class PurchaseResult:
    """Outcome of one purchase attempt (exactly one flag pattern is set)."""

    ok: bool
    already_owned: bool = False
    insufficient: bool = False
    price: int = 0
    new_balance: int | None = None
    #: Current balance, populated on the *insufficient* path for error copy.
    balance: int | None = None


async def purchase_unique_item(
    guild_id: int,
    user_id: int,
    item_name: str,
    price: int,
    *,
    actor_id: int | None = None,
) -> PurchaseResult:
    """Buy one unit of a unique (own-at-most-one) shop item atomically.

    Returns a :class:`PurchaseResult`; never partially commits.  *price*
    must be positive (the catalogue is caller-side — services cannot
    import the cog-layer ``SHOP_ITEMS``).
    """
    if price <= 0:
        msg = f"price must be positive, got {price}"
        raise ValueError(msg)
    reason = f"shop:{item_name}"
    try:
        async with db.transaction() as conn:
            granted = await db.try_grant_unique_item(
                user_id,
                guild_id,
                item_name,
                conn=conn,
            )
            if not granted:
                # Nothing written — exiting commits an empty transaction.
                return PurchaseResult(ok=False, already_owned=True, price=price)
            new_balance = await economy_service.debit_in_txn(
                conn,
                guild_id,
                user_id,
                price,
                reason=reason,
                actor_id=actor_id,
            )
    except economy_service.InsufficientFundsError:
        balance = await db.get_coins(user_id, guild_id)
        return PurchaseResult(
            ok=False,
            insufficient=True,
            price=price,
            balance=balance,
        )
    await bus.emit(
        economy_service.EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=user_id,
        delta=-price,
        new_balance=new_balance,
        reason=reason,
    )
    return PurchaseResult(ok=True, price=price, new_balance=new_balance)
