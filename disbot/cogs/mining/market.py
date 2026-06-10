"""Mining market orchestration — sell ore / buy gear (RS02 stage-2 candidate).

The pure pricing half (``TradeResult``, ``GEAR_SHOP``, sell/buy prices,
reason tags) relocated to :mod:`utils.mining.market`; this module re-exports
those names for its existing callers and keeps only the **orchestration**
(``apply_*``) — the only place mining touches money — until RS02 stage 2
converges it into ``services/mining_workflow.py`` with one transaction per
operation (Q-0071), as the workshop ops already did.

Failure ordering (two separate stores, no cross-store transaction yet): each
op is ordered to favour *no exploit* over *no harm* — **sell** removes the ore
before crediting (a mid-op failure can lose ore but never mints free coins);
**buy** debits before granting the item (a failure can cost coins but never
grants a free item).  The window is a single await on the same DB and is
acceptable for best-effort game state (ADR-002) until stage 2 closes it.
"""

from __future__ import annotations

from services import economy_service
from utils import db
from utils.mining.market import (  # noqa: F401 — re-exported for callers
    BUY_REASON,
    GEAR_SHOP,
    SELL_REASON,
    TradeResult,
    buy_price,
    sell_price,
    sellable_inventory,
    shop_listing,
    total_sale_value,
)


async def apply_sell(user_id: int, guild_id: int, item: str, qty: int) -> TradeResult:
    """Sell *qty* of *item* (a resource) for coins.  See module failure note."""
    item = item.strip().lower()
    price = sell_price(item)
    if price is None:
        return TradeResult(
            False,
            f"You can't sell **{item}** — only raw resources sell.",
        )
    if qty <= 0:
        return TradeResult(False, "Amount to sell must be a positive number.")
    inventory = await db.get_mining_inventory(str(user_id), guild_id)
    have = inventory.get(item, 0)
    if have < qty:
        return TradeResult(False, f"You only have **{have}× {item}** to sell.")
    coins = price * qty
    await db.update_mining_item(str(user_id), guild_id, item, -qty)
    new_balance = await economy_service.credit(
        guild_id,
        user_id,
        coins,
        reason=SELL_REASON,
        actor_id=user_id,
    )
    return TradeResult(
        True,
        f"Sold **{qty}× {item}** for **{coins}** 🪙. Balance: **{new_balance}** 🪙.",
        coins,
        new_balance,
    )


async def apply_sell_all(user_id: int, guild_id: int) -> TradeResult:
    """Sell every sellable resource in one credit.  See module failure note."""
    inventory = await db.get_mining_inventory(str(user_id), guild_id)
    sellables = sellable_inventory(inventory)
    if not sellables:
        return TradeResult(False, "You have no resources to sell — go mine some!")
    total = sum(qty * price for _, qty, price in sellables)
    for name, qty, _ in sellables:
        await db.update_mining_item(str(user_id), guild_id, name, -qty)
    new_balance = await economy_service.credit(
        guild_id,
        user_id,
        total,
        reason=SELL_REASON,
        actor_id=user_id,
    )
    sold = ", ".join(f"{qty}× {name}" for name, qty, _ in sellables)
    return TradeResult(
        True,
        f"Sold {sold} for **{total}** 🪙. Balance: **{new_balance}** 🪙.",
        total,
        new_balance,
    )


async def apply_buy(user_id: int, guild_id: int, item: str) -> TradeResult:
    """Buy one *item* from the gear shop for coins.  See module failure note."""
    item = item.strip().lower()
    price = buy_price(item)
    if price is None:
        return TradeResult(
            False,
            f"**{item}** isn't for sale. Check `!market` for stock.",
        )
    try:
        new_balance = await economy_service.debit(
            guild_id,
            user_id,
            price,
            reason=BUY_REASON,
            actor_id=user_id,
        )
    except economy_service.InsufficientFundsError:
        balance = await db.get_coins(user_id, guild_id)
        return TradeResult(
            False,
            f"**{item}** costs **{price}** 🪙 — you only have **{balance}** 🪙.",
        )
    await db.update_mining_item(str(user_id), guild_id, item, 1)
    return TradeResult(
        True,
        f"Bought **{item}** for **{price}** 🪙. Balance: **{new_balance}** 🪙. "
        f"Use `!equip {item}` to wear it.",
        -price,
        new_balance,
    )


__all__ = [
    "TradeResult",
    "GEAR_SHOP",
    "SELL_REASON",
    "BUY_REASON",
    "sell_price",
    "sellable_inventory",
    "total_sale_value",
    "buy_price",
    "shop_listing",
    "apply_sell",
    "apply_sell_all",
    "apply_buy",
]
