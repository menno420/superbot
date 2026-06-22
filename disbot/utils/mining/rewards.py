"""Mining loot tables + explore outcomes — pure functions (S4.1).

Extracted from the pre-decomposition ``cogs/mining_cog.py``.  All
functions are pure: state-in (RNG seed implicit via ``random``),
return-out, no Discord, no DB.  This makes the loot math
independently unit-testable without a mock harness.
"""

from __future__ import annotations

import random

from utils import equipment

# Mining ore weights at the Surface (depth 0).  Deeper bands re-weight these
# toward rarer ore via ``ore_weights_for_depth`` — the same six ores at every
# depth, just better odds the deeper you mine.  Surface weights descend in
# 0.5 steps by sell value (stone 1 < bronze 2 < iron 3 < silver 4 < gold 6 <
# diamond 12) — commonness is the inverse of worth.  Bronze + silver joined
# with the V-16 gear sets (Q-0092) so every gear tier has its ore.
ORE_WEIGHTS: dict[str, float] = {
    "stone": 3,
    "bronze": 2.5,
    "iron": 2,
    "silver": 1.5,
    "gold": 1,
    "diamond": 0.5,
}


def ore_weights_for_depth(depth: int) -> dict[str, float]:
    """Ore selection weights for a mining band.

    ``depth`` 0 returns :data:`ORE_WEIGHTS` unchanged (so the Surface roll is
    identical to the pre-depth behaviour); each band deeper shifts the odds
    away from stone — and, at half that rate, away from bronze (the shallow
    Bronze-Age metal) — and toward the precious ores — "deeper = richer" —
    while keeping the same six ores so callers never see an unknown drop.
    """
    d = max(0, depth)
    return {
        "stone": max(0.5, ORE_WEIGHTS["stone"] - d),
        "bronze": max(0.5, ORE_WEIGHTS["bronze"] - 0.5 * d),
        "iron": ORE_WEIGHTS["iron"] + 0.5 * d,
        "silver": ORE_WEIGHTS["silver"] + 0.5 * d,
        "gold": ORE_WEIGHTS["gold"] + 0.5 * d,
        "diamond": ORE_WEIGHTS["diamond"] + 0.5 * d,
    }


# Per-point gain of an equipped tool's ``mining_power`` on the mine multiplier.
# Rebalanced 2026-06-22: the old ``1 + power // 2`` ran the curve away to ×5 at
# diamond (powers 0/2/4/6/8 → ×1/2/3/4/5), letting a geared veteran out-earn a
# fresh player ~8×. A gentle linear gain flattens it to ×1/1.13/1.25/1.38/1.5,
# keeping the geared/fresh gap playable for everyone. Sim-pinned:
# docs/planning/mining-economy-balance-2026-06-22.md.
TOOL_POWER_GAIN = 0.0625

# Legacy inventory-pickaxe bonus (no tool equipped) — matched to the new
# pickaxe-tier multiplier so the two paths agree and the curve stays flat.
LEGACY_PICKAXE_MULT = 1.0 + 2 * TOOL_POWER_GAIN


def mine_multiplier(
    equipped: dict[str, str],
    inventory: dict[str, int],
) -> float:
    """The mine-amount multiplier from the player's tool.

    An **equipped** tool wins and scales with its ``mining_power`` via a gentle
    linear gain (``1 + power * TOOL_POWER_GAIN``): pickaxe ×1.13, iron ×1.25,
    diamond ×1.5 — a better tool still pays, but the curve no longer runs away
    (the 2026-06-22 rebalance).  With no tool equipped, a pickaxe in the
    inventory keeps the matched legacy bonus so pre-equipment players lose
    nothing (and take no durability wear either).
    """
    tool = equipped.get(equipment.TOOL)
    if tool:
        power = equipment.compute_stats({equipment.TOOL: tool}).mining_power
        return 1.0 + power * TOOL_POWER_GAIN
    return LEGACY_PICKAXE_MULT if inventory.get("pickaxe", 0) > 0 else 1.0


# Base ore per dig before tool/cell multipliers. Rebalanced 2026-06-22 from
# 1-3 → 1-2 (cut the raw faucet magnitude). Sim-pinned:
# docs/planning/mining-economy-balance-2026-06-22.md.
BASE_ROLL_MAX = 2


def roll_mine_loot(
    *,
    has_pickaxe: bool,
    depth: int = 0,
    multiplier: float | None = None,
) -> tuple[str, int]:
    """Return ``(ore_name, amount)`` for one dig.

    The base roll is ``randint(1, BASE_ROLL_MAX)``.  *depth* (the player's band,
    0 = Surface) re-weights the ore table toward rarer finds the deeper the
    player has descended.  *multiplier* (from :func:`mine_multiplier`) is the
    tool bonus; a fractional multiplier is rounded into a whole ore count
    (never below 1).  With no equipment-aware multiplier, a pickaxe in the
    inventory applies the legacy bonus.
    """
    weights = ore_weights_for_depth(depth)
    found = random.choices(
        list(weights.keys()),
        weights=list(weights.values()),
        k=1,
    )[0]
    bonus = (
        multiplier
        if multiplier is not None
        else (LEGACY_PICKAXE_MULT if has_pickaxe else 1.0)
    )
    amount = max(1, round(random.randint(1, BASE_ROLL_MAX) * bonus))
    return found, amount


def roll_harvest_amount(*, has_axe: bool) -> int:
    """Return the wood amount harvested by one !chop / Harvest button press."""
    multiplier = 2 if has_axe else 1
    return random.randint(1, 3) * multiplier


# Explore outcomes — each entry is (description, item_or_None, delta).
EXPLORE_OUTCOMES: list[tuple[str, str | None, int]] = [
    ("found 1 gold in an abandoned camp!", "gold", 1),
    ("stumbled upon a hidden diamond vein and got 1 diamond!", "diamond", 1),
    ("was attacked by monsters and lost 2 stone...", "stone", -2),
    ("found a secret chest with 3 wood!", "wood", 3),
    ("got lost and found nothing...", None, 0),
]


def roll_explore_outcome() -> tuple[str, str | None, int]:
    """Return one (description, item_or_None, delta) tuple for !explore."""
    return random.choice(EXPLORE_OUTCOMES)
