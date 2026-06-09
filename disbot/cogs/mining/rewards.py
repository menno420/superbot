"""Mining loot tables + explore outcomes — pure functions (S4.1).

Extracted from the pre-decomposition ``cogs/mining_cog.py``.  All
functions are pure: state-in (RNG seed implicit via ``random``),
return-out, no Discord, no DB.  This makes the loot math
independently unit-testable without a mock harness.
"""

from __future__ import annotations

import random

# Mining ore weights at the Surface (depth 0).  Deeper bands re-weight these
# toward rarer ore via ``ore_weights_for_depth`` — the same four ores at every
# depth, just better odds the deeper you mine.
ORE_WEIGHTS: dict[str, float] = {
    "stone": 3,
    "iron": 2,
    "gold": 1,
    "diamond": 0.5,
}


def ore_weights_for_depth(depth: int) -> dict[str, float]:
    """Ore selection weights for a mining band.

    ``depth`` 0 returns :data:`ORE_WEIGHTS` unchanged (so the Surface roll is
    identical to the pre-depth behaviour); each band deeper shifts the odds away
    from stone and toward iron/gold/diamond — "deeper = richer" — while keeping
    the same four ores so callers never see an unknown drop.
    """
    d = max(0, depth)
    return {
        "stone": max(0.5, ORE_WEIGHTS["stone"] - d),
        "iron": ORE_WEIGHTS["iron"] + 0.5 * d,
        "gold": ORE_WEIGHTS["gold"] + 0.5 * d,
        "diamond": ORE_WEIGHTS["diamond"] + 0.5 * d,
    }


def roll_mine_loot(*, has_pickaxe: bool, depth: int = 0) -> tuple[str, int]:
    """Return ``(ore_name, amount)`` for one !mine click / Mine button press.

    A pickaxe in the inventory doubles the amount mined.  *depth* (the player's
    band, 0 = Surface) re-weights the ore table toward rarer finds the deeper the
    player has descended; it defaults to 0 so existing surface callers and their
    tests are unaffected.
    """
    weights = ore_weights_for_depth(depth)
    found = random.choices(
        list(weights.keys()),
        weights=list(weights.values()),
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
