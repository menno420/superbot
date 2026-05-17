"""Mining loot tables + explore outcomes — pure functions (S4.1).

Extracted from the pre-decomposition ``cogs/mining_cog.py``.  All
functions are pure: state-in (RNG seed implicit via ``random``),
return-out, no Discord, no DB.  This makes the loot math
independently unit-testable without a mock harness.
"""

from __future__ import annotations

import random

# Mining ore weights — used by both !mine and MiningHubView.mine_btn.
ORE_WEIGHTS: dict[str, float] = {
    "stone": 3,
    "iron": 2,
    "gold": 1,
    "diamond": 0.5,
}


def roll_mine_loot(*, has_pickaxe: bool) -> tuple[str, int]:
    """Return ``(ore_name, amount)`` for one !mine click / Mine button press.

    A pickaxe in the inventory doubles the amount mined.
    """
    found = random.choices(
        list(ORE_WEIGHTS.keys()),
        weights=list(ORE_WEIGHTS.values()),
        k=1,
    )[0]
    bonus = 2 if has_pickaxe else 1
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
