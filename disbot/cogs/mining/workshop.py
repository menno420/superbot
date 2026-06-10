"""Mining workshop — durability, repair, crafting (the recurring sink).

The brainstorm §7.5 keystone: gear **wears out** as it is used and is brought
back by **re-crafting** (an ore sink) or **repairing** (a coin sink), closing
the *mine → sell/craft → repair → descend* economy loop.  Decision 6.1 #8:
flat crafting + quick-craft-last-broken; stations come later.

Two halves, mirroring :mod:`cogs.mining.market`:

* **Pure helpers** (no I/O): repair pricing (derived from the market's
  ``GEAR_SHOP`` so one knob tunes both), durability bars, craftable-gear
  listings, and the wear plan (which equipped slots wear on which action).
* **Orchestration** (``apply_*``): the wear tick (break → consume the item
  from inventory + clear its slot + remember it for quick-craft), repair
  (coins move **exclusively** through the audited
  :mod:`services.economy_service`), and crafting (one shared implementation
  for ``!build``, the Build modal, the Workshop panel, and quick-craft —
  materials + product move in ONE transaction via
  ``db.apply_inventory_deltas``, closing the old half-consumed-recipe gap).

Durability state is keyed by item *name* (``mining_gear_wear``), not slot, so
unequip/re-equip never resets it (that would be a free-repair exploit).  A
wear row exists only while an item is worn: breaking or repairing deletes it.

Failure ordering (repair): coins are debited **before** the wear row clears —
a mid-op failure can cost coins but never grants a free repair (mirrors the
market's no-exploit-over-no-harm ordering; acceptable for best-effort game
state, ADR-002).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from cogs.mining import market
from utils.mining.recipes import load_recipes
from services import economy_service
from utils import db, equipment

# Reason tag written to economy_audit_log (filterable money-flow events).
REPAIR_REASON = "mining:repair_gear"

# Repair pricing: a full repair costs this fraction of the item's GEAR_SHOP
# price (rounded up, min 1 🪙), scaled by how worn the item is.  One knob —
# retuning the shop retunes repairs with it.
REPAIR_RATE = 0.5

# Warn the player when remaining durability drops to this or below.
LOW_DURABILITY_WARN = 5

# Wear plan — which equipped slots wear 1 durability per action.  A slot
# marked underground-only wears only when the player is below the surface
# (depth > 0): your light burns down in the mine, not in daylight.
ACTION_MINE = "mine"
ACTION_EXPLORE = "explore"
_WEAR_PLAN: dict[str, tuple[tuple[str, bool], ...]] = {
    # Each entry pairs a slot with its underground-only flag.
    ACTION_MINE: ((equipment.TOOL, False), (equipment.LIGHT, True)),
    ACTION_EXPLORE: ((equipment.LIGHT, True), (equipment.CHARM, False)),
}


@dataclass(frozen=True)
class WearReport:
    """Outcome of one wear tick — call sites append ``notes`` to their embed."""

    broke: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class CraftableGear:
    """One gear recipe the Workshop can show (and maybe craft right now)."""

    name: str
    materials: dict[str, int] = field(default_factory=dict)
    craftable: bool = False


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def repair_base(name: str) -> int | None:
    """Coins for a full 0→max repair of *name*, or None if not repairable.

    Derived from the market's gear-shop price so a repaired item is always
    cheaper than a new one, and one catalogue tunes both sinks.
    """
    price = market.buy_price(name)
    if price is None:
        return None
    return max(1, math.ceil(price * REPAIR_RATE))


def repair_cost(name: str, remaining: int) -> int | None:
    """Coins to repair *name* from *remaining* back to max, or None.

    Proportional to the missing durability (min 1 🪙) — topping up a barely
    worn tool is cheap; rescuing a nearly broken one approaches the full base.
    """
    maximum = equipment.max_durability(name)
    base = repair_base(name)
    if maximum is None or base is None:
        return None
    missing = max(0, maximum - remaining)
    if missing == 0:
        return None
    return max(1, math.ceil(base * missing / maximum))


def durability_bar(remaining: int, maximum: int) -> str:
    """A 5-segment ``▰▰▰▱▱ 23/60`` bar for embeds (pure, no Discord)."""
    if maximum <= 0:
        return f"{remaining}/{maximum}"
    filled = math.ceil(remaining / maximum * 5)
    filled = max(0, min(5, filled))
    return f"{'▰' * filled}{'▱' * (5 - filled)} {remaining}/{maximum}"


def gear_recipes(recipes: dict[str, dict[str, int]]) -> list[CraftableGear]:
    """The equippable subset of *recipes*, unfiltered (for "all recipes")."""
    return [
        CraftableGear(name, dict(mats))
        for name, mats in sorted(recipes.items())
        if equipment.is_equippable(name)
    ]


def craftable_gear(
    recipes: dict[str, dict[str, int]],
    inventory: dict[str, int],
) -> list[CraftableGear]:
    """Equippable recipes annotated with whether *inventory* can craft them now."""
    return [
        CraftableGear(
            g.name,
            g.materials,
            craftable=all(
                inventory.get(mat, 0) >= qty for mat, qty in g.materials.items()
            ),
        )
        for g in gear_recipes(recipes)
    ]


def describe_materials(materials: dict[str, int]) -> str:
    """``"3× iron, 2× wood"`` — one rendering for recipe lines everywhere."""
    return ", ".join(f"{qty}× {mat}" for mat, qty in sorted(materials.items()))


# ---------------------------------------------------------------------------
# Orchestration — wear (the sink's tick)
# ---------------------------------------------------------------------------


async def apply_wear(
    user_id: int,
    guild_id: int,
    *,
    action: str,
    depth: int,
    equipped: dict[str, str],
) -> WearReport:
    """Tick 1 durability off each equipped item *action* uses; break at 0.

    Breaking consumes one unit from the inventory (the actual sink), clears
    the equipment slot, deletes the wear row, and records the item as
    ``last_broken_item`` so quick-craft can offer it back.
    """
    plan = _WEAR_PLAN.get(action, ())
    suid = str(user_id)
    candidates = [
        (slot, item)
        for slot, underground_only in plan
        if (item := equipped.get(slot))
        and (not underground_only or depth > 0)
        and equipment.max_durability(item) is not None
    ]
    if not candidates:
        return WearReport()

    wear = await db.get_gear_wear(suid, guild_id)
    broke: list[str] = []
    notes: list[str] = []
    for slot, item in candidates:
        maximum = equipment.max_durability(item)
        if maximum is None:  # filtered above; guard keeps the type narrow
            continue
        remaining = wear.get(item, maximum) - 1
        if remaining <= 0:
            await db.clear_gear_wear(suid, guild_id, item)
            await db.update_mining_item(suid, guild_id, item, -1)
            await db.unequip_slot(suid, guild_id, slot)
            await db.set_last_broken(suid, guild_id, item)
            broke.append(item)
            notes.append(
                f"💥 Your **{item}** broke! Re-craft or repair gear at the "
                f"🔧 Workshop.",
            )
        else:
            await db.set_gear_wear(suid, guild_id, item, remaining)
            if remaining <= LOW_DURABILITY_WARN:
                notes.append(
                    f"⚠️ Your **{item}** is nearly worn out "
                    f"({remaining}/{maximum}) — repair it at the 🔧 Workshop.",
                )
    return WearReport(broke=tuple(broke), notes=tuple(notes))


# ---------------------------------------------------------------------------
# Orchestration — repair (coin sink, audited) / craft (ore sink)
# ---------------------------------------------------------------------------


async def apply_repair(
    user_id: int,
    guild_id: int,
    item: str,
) -> market.TradeResult:
    """Repair *item* to full durability for coins.  See module failure note."""
    item = item.strip().lower()
    suid = str(user_id)
    if equipment.max_durability(item) is None:
        return market.TradeResult(False, f"**{item}** doesn't wear out.")
    inventory = await db.get_mining_inventory(suid, guild_id)
    if inventory.get(item, 0) < 1:
        return market.TradeResult(False, f"You don't own a **{item}** to repair.")
    wear = await db.get_gear_wear(suid, guild_id)
    if item not in wear:
        return market.TradeResult(
            False,
            f"Your **{item}** is already at full durability.",
        )
    cost = repair_cost(item, wear[item])
    if cost is None:
        return market.TradeResult(False, f"**{item}** can't be repaired here.")
    try:
        new_balance = await economy_service.debit(
            guild_id,
            user_id,
            cost,
            reason=REPAIR_REASON,
            actor_id=user_id,
        )
    except economy_service.InsufficientFundsError:
        balance = await db.get_coins(user_id, guild_id)
        return market.TradeResult(
            False,
            f"Repairing **{item}** costs **{cost}** 🪙 — you only have "
            f"**{balance}** 🪙.",
        )
    await db.clear_gear_wear(suid, guild_id, item)
    return market.TradeResult(
        True,
        f"Repaired **{item}** to full durability for **{cost}** 🪙. "
        f"Balance: **{new_balance}** 🪙.",
        -cost,
        new_balance,
    )


async def apply_craft(
    user_id: int,
    guild_id: int,
    item: str,
) -> market.TradeResult:
    """Craft *item* from its recipe — materials + product in one transaction."""
    item = item.strip().lower()
    suid = str(user_id)
    recipe = load_recipes().get(item)
    if not recipe:
        hint = (
            " You can buy one at the 🛒 Market instead."
            if market.buy_price(item) is not None
            else " Use `!buildlist` to see available recipes."
        )
        return market.TradeResult(False, f"No recipe for **{item}**.{hint}")
    inventory = await db.get_mining_inventory(suid, guild_id)
    for mat, qty in recipe.items():
        if inventory.get(mat, 0) < qty:
            return market.TradeResult(
                False,
                f"You don't have enough **{mat}** to craft **{item}** "
                f"(needs {describe_materials(recipe)}).",
            )
    deltas = {mat: -qty for mat, qty in recipe.items()}
    deltas[item] = deltas.get(item, 0) + 1
    await db.apply_inventory_deltas(suid, guild_id, deltas)
    return market.TradeResult(True, f"Crafted **{item}**!")


async def apply_quick_craft(user_id: int, guild_id: int) -> market.TradeResult:
    """Re-craft the last item that broke; auto-equip it if its slot is free."""
    suid = str(user_id)
    last = await db.get_last_broken(suid, guild_id)
    if not last:
        return market.TradeResult(
            False,
            "Nothing has broken recently — craft or repair gear below.",
        )
    result = await apply_craft(user_id, guild_id, last)
    if not result.ok:
        return result
    message = result.message
    slot = equipment.slot_for(last)
    if slot is not None:
        equipped = await db.get_equipment(suid, guild_id)
        if slot not in equipped:
            await db.equip_item(suid, guild_id, slot, last)
            message = f"Crafted **{last}** and equipped it in the **{slot}** slot!"
    await db.set_last_broken(suid, guild_id, None)
    return market.TradeResult(True, message)


__all__ = [
    "REPAIR_REASON",
    "REPAIR_RATE",
    "LOW_DURABILITY_WARN",
    "ACTION_MINE",
    "ACTION_EXPLORE",
    "WearReport",
    "CraftableGear",
    "repair_base",
    "repair_cost",
    "durability_bar",
    "gear_recipes",
    "craftable_gear",
    "describe_materials",
    "apply_wear",
    "apply_repair",
    "apply_craft",
    "apply_quick_craft",
]
