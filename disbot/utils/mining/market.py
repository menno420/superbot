"""Mining market — pure pricing (sell values + the gear shop).

The *pure* half of the market (RS02 split): what an ore sells for, what
gear costs, and the typed :class:`TradeResult` every mining operation
returns.  No I/O — the money/inventory orchestration lives in
``services/mining_workflow.py`` (one transaction per operation).

Sell prices reuse :func:`utils.mining.items.item_value` so "what an ore
is worth" has a single source of truth; the gear shop is a small,
tunable coin catalogue — the balance knob for the economy loop.
"""

from __future__ import annotations

from dataclasses import dataclass

from utils.mining import items

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
    # Deeper ladders (2026-06-10) — priced well above material sell value so
    # crafting stays the cheaper path and selling-then-buying never profits.
    "gold pickaxe": 140,
    "diamond sword": 180,
    "diamond lantern": 200,
    "diamond armor": 250,
    "diamond pickaxe": 320,
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
]
