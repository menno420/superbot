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


def mine_multiplier(
    equipped: dict[str, str],
    inventory: dict[str, int],
) -> int:
    """The mine-amount multiplier from the player's tool.

    An **equipped** tool wins and scales with its ``mining_power`` using the
    exploration engine's formula (``1 + power // 2``): pickaxe ×2 (the legacy
    bonus), iron pickaxe ×3 — equipping the better tool finally pays.  With no
    tool equipped, a pickaxe sitting in the inventory keeps the legacy ×2 so
    pre-equipment players lose nothing (and take no durability wear either).
    """
    tool = equipped.get(equipment.TOOL)
    if tool:
        return 1 + equipment.compute_stats({equipment.TOOL: tool}).mining_power // 2
    return 2 if inventory.get("pickaxe", 0) > 0 else 1


def roll_mine_loot(
    *,
    has_pickaxe: bool,
    depth: int = 0,
    multiplier: int | None = None,
) -> tuple[str, int]:
    """Return ``(ore_name, amount)`` for one !mine click / Mine button press.

    A pickaxe in the inventory doubles the amount mined.  *depth* (the player's
    band, 0 = Surface) re-weights the ore table toward rarer finds the deeper the
    player has descended; it defaults to 0 so existing surface callers and their
    tests are unaffected.  *multiplier* (from :func:`mine_multiplier`) overrides
    the binary pickaxe bonus when the caller is equipment-aware.
    """
    weights = ore_weights_for_depth(depth)
    found = random.choices(
        list(weights.keys()),
        weights=list(weights.values()),
        k=1,
    )[0]
    bonus = multiplier if multiplier is not None else (2 if has_pickaxe else 1)
    amount = random.randint(1, 3) * bonus
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
