"""Mining market — the economic faucet + sink (sell ore, buy gear).

This is the cross-domain leg of the mining character platform: raw resources
**sell** for coins (the faucet) and gear is **bought** with coins (the sink),
closing the *mine → sell → upgrade → descend* loop (brainstorm §7.5).

Two halves:

* **Pure pricing** (no I/O): sell prices reuse :func:`utils.mining.items.item_value`
  so "what an ore is worth" has a single source of truth; the gear shop is a
  small, tunable coin catalogue.
* **Orchestration** (``apply_*``): the only place mining touches money.  Coins
  move **exclusively** through the audited :mod:`services.economy_service`
  (``credit``/``debit`` → audit row + balance event); the inventory side stays
  on mining's intentional direct-lane CRUD.  This module is a ``cogs``-layer
  domain module (it may import ``services`` + ``utils``), so both the cog
  commands and the market view call one implementation — no duplicated money
  code.

Failure ordering (two separate stores, no cross-store transaction): each op is
ordered to favour *no exploit* over *no harm* — **sell** removes the ore before
crediting (a mid-op failure can lose ore but never mints free coins); **buy**
debits before granting the item (a failure can cost coins but never grants a
free item).  The window is a single await on the same DB and is acceptable for
best-effort game state (ADR-002).
"""

from __future__ import annotations

from dataclasses import dataclass

from utils.mining import items
from services import economy_service
from utils import db

# Reason tags written to economy_audit_log (filterable money-flow events).
SELL_REASON = "mining:sell_ore"
BUY_REASON = "mining:buy_gear"

# Gear shop — coins to buy each item (the sink).  Priced above the sell value
# of the materials it would take to craft, so selling-then-buying is never free
# arbitrage.  Tunable; this is the balance knob for the economy loop.
GEAR_SHOP: dict[str, int] = {
    "torch": 10,
    "pickaxe": 25,
    "sword": 25,
    "shield": 30,
    "dynamite": 30,
    "lantern": 40,
    "iron sword": 60,
    "iron pickaxe": 60,
    "armor": 70,
    "lucky charm": 80,
}


@dataclass(frozen=True)
class TradeResult:
    """Outcome of a sell/buy attempt — the cog/view renders ``message``."""

    ok: bool
    message: str
    coins_delta: int = 0
    new_balance: int | None = None


def sell_price(name: str) -> int | None:
    """Coins paid per unit when selling *name*, or ``None`` if it can't be sold.

    Only **explicitly catalogued resources** (the ore/wood you mine) are
    sellable — the faucet.  Tools, gear, structures, and *unknown* items are
    never sold back (no buy-low/sell-high arbitrage, and no minting coins from
    junk an unknown-defaults-to-RESOURCE classification would otherwise allow).
    """
    item = items.lookup(name)
    if item is not None and item.kind is items.ItemKind.RESOURCE:
        return item.value
    return None


def sellable_inventory(inventory: dict[str, int]) -> list[tuple[str, int, int]]:
    """``[(name, qty, unit_price)]`` for every sellable resource (qty > 0).

    Ordered by unit price (desc) then name, for a stable display.
    """
    rows = [
        (name, qty, price)
        for name, qty in inventory.items()
        if qty > 0 and (price := sell_price(name)) is not None
    ]
    rows.sort(key=lambda r: (-r[2], r[0]))
    return rows


def total_sale_value(inventory: dict[str, int]) -> int:
    """Total coins a full sell-all of *inventory*'s resources would yield."""
    return sum(qty * price for _, qty, price in sellable_inventory(inventory))


def buy_price(name: str) -> int | None:
    """Coin cost to buy *name* from the gear shop, or ``None`` if not for sale."""
    return GEAR_SHOP.get(name.lower())


def shop_listing() -> list[tuple[str, int]]:
    """``[(item, price)]`` for the gear shop, ordered by price then name."""
    return sorted(GEAR_SHOP.items(), key=lambda kv: (kv[1], kv[0]))


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
