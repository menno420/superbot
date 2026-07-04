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
VAULT_UPGRADE_REASON = "mining:vault_upgrade"
FORGE_BUILD_REASON = "mining:forge_build"
HOME_BUILD_REASON = "mining:home_build"
CAMPFIRE_BUILD_REASON = "mining:campfire_build"
TIDE_POOL_BUILD_REASON = "mining:tide_pool_build"
DOCK_BUILD_REASON = "mining:dock_build"
BOATHOUSE_BUILD_REASON = "mining:boathouse_build"
FISHERY_BUILD_REASON = "mining:fishery_build"


def structure_build_reason(structure: str) -> str:
    """The economy-audit reason tag for building *structure* (the money-flow tag).

    Derived generically as ``mining:{structure}_build`` — exactly what every named
    ``*_BUILD_REASON`` constant above already spells.  ``build_structure`` uses this
    instead of a hand-maintained ``{structure: reason}`` map so a newly-registered
    structure can **never** crash the build path for want of a map entry (the
    ``boathouse`` ``KeyError`` that shipped in #1605 — BUG-0031).
    """
    return f"mining:{structure.strip().lower()}_build"


# Gear shop — coins to buy each item (the sink).  Priced ~5-6× the sell value
# of the materials it would take to craft, so crafting stays the cheaper path
# and selling-then-buying is never free arbitrage.  Tunable; this is the
# balance knob for the economy loop — repair pricing derives from it too
# (workshop.repair_base), so EVERY wearing item must have a row here.
GEAR_SHOP: dict[str, int] = {
    "torch": 10,
    "pickaxe": 25,
    "sword": 25,
    "shield": 30,
    "dynamite": 30,
    "lantern": 40,
    "iron pickaxe": 60,
    "lucky charm": 80,
    # Fishing charms (Q-0175 / V-14) — the CHARM-slot fishing ladder; coins
    # only (no recipe), priced above the lucky charm and monotonic up the ladder.
    "fishing charm": 90,
    "anglers charm": 220,
    "master angler charm": 420,
    # Food / boosters — refill mining energy (utils/mining/energy.py). A coin
    # sink that lets an active player dig past the passive regen rate; priced
    # well above their flavour value so they stay a convenience, not arbitrage.
    "ration": 20,
    "energy drink": 40,
    # Deeper ladders (2026-06-10) — priced well above material sell value so
    # crafting stays the cheaper path and selling-then-buying never profits.
    "gold pickaxe": 140,
    "diamond lantern": 200,
    "diamond pickaxe": 320,
    # The V-16 combat-set families (Q-0092) — monotonic per family; the
    # per-tier ladder tracks each tier's ore value (bronze 2 / iron 3 /
    # silver 4 / gold 6 / diamond 12).  Numbers rationale:
    # docs/planning/gear-set-numbers-2026-06-11.md.
    "bronze sword": 30,
    "iron sword": 60,
    "silver sword": 75,
    "gold sword": 95,
    "diamond sword": 180,
    "bronze shield": 40,
    "iron shield": 65,
    "silver shield": 85,
    "gold shield": 110,
    "diamond shield": 200,
    "bronze helmet": 35,
    "iron helmet": 55,
    "silver helmet": 75,
    "gold helmet": 105,
    "diamond helmet": 190,
    "bronze chestplate": 55,
    "iron chestplate": 85,
    "silver chestplate": 115,
    "gold chestplate": 160,
    "diamond chestplate": 280,
    "bronze leggings": 45,
    "iron leggings": 70,
    "silver leggings": 95,
    "gold leggings": 135,
    "diamond leggings": 240,
    "bronze boots": 25,
    "iron boots": 40,
    "silver boots": 55,
    "gold boots": 75,
    "diamond boots": 130,
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


def shop_sections() -> list[tuple[str, list[tuple[str, int]]]]:
    """The shop listing grouped for display: ``[(section_label, rows)]``.

    The set-piece catalogue outgrew one flat list (41 items vs Discord's
    25-option select cap and the 1024-char field cap), so the market panel
    renders one field + one buy-select per section.  Grouping is derived from
    the equipment slot — never a hand-kept name list.
    """
    from utils import equipment  # local import keeps module deps one-way

    weapon_slots = {equipment.WEAPON, equipment.SHIELD}
    armor_slots = {
        equipment.HELMET,
        equipment.CHESTPLATE,
        equipment.LEGGINGS,
        equipment.BOOTS,
    }
    sections: dict[str, list[tuple[str, int]]] = {
        "⚔️ Weapons & shields": [],
        "🛡️ Armor": [],
        "🧰 Tools & supplies": [],
    }
    for name, price in shop_listing():
        slot = equipment.slot_for(name)
        if slot in weapon_slots:
            sections["⚔️ Weapons & shields"].append((name, price))
        elif slot in armor_slots:
            sections["🛡️ Armor"].append((name, price))
        else:
            sections["🧰 Tools & supplies"].append((name, price))
    return [(label, rows) for label, rows in sections.items() if rows]


__all__ = [
    "TradeResult",
    "GEAR_SHOP",
    "SELL_REASON",
    "BUY_REASON",
    "VAULT_UPGRADE_REASON",
    "FORGE_BUILD_REASON",
    "HOME_BUILD_REASON",
    "CAMPFIRE_BUILD_REASON",
    "TIDE_POOL_BUILD_REASON",
    "DOCK_BUILD_REASON",
    "BOATHOUSE_BUILD_REASON",
    "FISHERY_BUILD_REASON",
    "structure_build_reason",
    "sell_price",
    "sellable_inventory",
    "total_sale_value",
    "buy_price",
    "shop_listing",
    "shop_sections",
]
