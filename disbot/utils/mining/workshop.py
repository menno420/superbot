"""Mining workshop — pure durability/repair/craft helpers (RS02 split).

The *pure* half of the brainstorm §7.5 durability keystone: repair
pricing (derived from the market's ``GEAR_SHOP`` so one knob tunes both
sinks), durability bars, craftable-gear listings, and the wear plan
(which equipped slots wear on which action).  No I/O — the multi-write
orchestration (wear ticks, repair, craft, quick-craft) lives in
``services/mining_workflow.py``, the audited mining write boundary.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from utils import equipment
from utils.mining import market

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
ACTION_DUEL = "duel"
WEAR_PLAN: dict[str, tuple[tuple[str, bool], ...]] = {
    # Each entry pairs a slot with its underground-only flag.
    ACTION_MINE: ((equipment.TOOL, False), (equipment.LIGHT, True)),
    ACTION_EXPLORE: ((equipment.LIGHT, True), (equipment.CHARM, False)),
    # Q-0054: combat gear joins the craft→break→repair loop — a PvP duel
    # ticks each fighter's equipped combat pieces once (never
    # underground-gated).  All six set slots wear (V-16 set-piece model).
    ACTION_DUEL: tuple((slot, False) for slot in equipment.SET_SLOTS),
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


__all__ = [
    "REPAIR_REASON",
    "REPAIR_RATE",
    "LOW_DURABILITY_WARN",
    "ACTION_MINE",
    "ACTION_EXPLORE",
    "ACTION_DUEL",
    "WEAR_PLAN",
    "WearReport",
    "CraftableGear",
    "repair_base",
    "repair_cost",
    "durability_bar",
    "gear_recipes",
    "craftable_gear",
    "describe_materials",
]
