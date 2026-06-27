"""Fishing gear → cast knobs (Q-0175 / V-14 "matching gear → better fishing").

The pure converter that turns the equipped character's :class:`~utils.equipment.
EffectiveStats` into the fishing cast's **4th** how-well knob, beside the rod, the
bait, and the day's weather.  Two stats feed two multipliers:

* ``fishing_power`` → a **rarity-pull** multiplier (≥ 1): like a rod's
  ``rarity_pull``, it biases the catch toward the big end of the *same* unlocked
  band — never a new band (that stays the fishing-level axis).
* ``bite_luck`` → a **bite-speed** multiplier (≤ 1 = faster): like a rod's
  ``bite_speed``, it quickens the bite wait.

Both are **bounded** and **default-preserving**: with no fishing gear equipped
(``fishing_power == bite_luck == 0``) every multiplier is exactly ``1.0``, so a
cast is byte-identical to the pre-gear behaviour.  The full ladder of three
charms tops out well below a rod tier on its own, so fishing gear is an
*optimisation*, never a gate (the starter still fishes fine).

Pure + stdlib-only (no Discord, no DB).  :mod:`services.fishing_workflow` reads
these and compounds them into the cast; the numbers are sim-pinned in
``docs/planning/fishing-gear-numbers-2026-06-27.md`` and
``tests/unit/utils/test_fishing_gear.py``.
"""

from __future__ import annotations

from dataclasses import dataclass

from utils.equipment import EffectiveStats

#: Per-point rarity-pull added by ``fishing_power`` (the full ladder's
#: ``fishing_power=6`` → ×1.24, a touch under a Silver rod's 1.25 pull).
PULL_PER_FISHING_POWER = 0.04
#: Per-point bite-wait reduction from ``bite_luck`` (``bite_luck=3`` → ×0.91).
BITE_SPEED_PER_BITE_LUCK = 0.03

#: Hard caps so gear can never dominate the rod×bait×weather stack even if a
#: future item or stacking path pushes the stats far past the charm ladder.
MAX_GEAR_PULL = 1.40  # ceiling on the rarity-pull multiplier
MIN_GEAR_BITE_SPEED = 0.75  # floor on the bite-speed multiplier (faster)


def fishing_pull_mult(stats: EffectiveStats) -> float:
    """Rarity-pull multiplier (≥ 1.0) contributed by ``stats.fishing_power``.

    ``1.0`` when no fishing gear is equipped (``fishing_power <= 0``); rises
    ``PULL_PER_FISHING_POWER`` per point, capped at :data:`MAX_GEAR_PULL`.
    """
    power = max(0, stats.fishing_power)
    return min(1.0 + PULL_PER_FISHING_POWER * power, MAX_GEAR_PULL)


def fishing_bite_speed_mult(stats: EffectiveStats) -> float:
    """Bite-speed multiplier (≤ 1.0 = faster) contributed by ``stats.bite_luck``.

    ``1.0`` when no fishing gear is equipped (``bite_luck <= 0``); falls
    ``BITE_SPEED_PER_BITE_LUCK`` per point, floored at :data:`MIN_GEAR_BITE_SPEED`.
    """
    luck = max(0, stats.bite_luck)
    return max(1.0 - BITE_SPEED_PER_BITE_LUCK * luck, MIN_GEAR_BITE_SPEED)


def has_fishing_bonus(stats: EffectiveStats) -> bool:
    """Whether *stats* carry any fishing gear contribution (for cast-panel copy)."""
    return stats.fishing_power > 0 or stats.bite_luck > 0


# ---------------------------------------------------------------------------
# Charm crafting — turn caught fish into the CHARM-slot fishing charms, the
# gameplay-native earn path beside the coin shop (S1 acquisition-depth follow-up
# to #1504; mirrors the catch→bait loop in :mod:`utils.fishing.bait`).
# ---------------------------------------------------------------------------
#
# The three fishing charms (``fishing charm`` / ``anglers charm`` /
# ``master angler charm``) are permanent CHARM-slot gear sold for coins in the
# mining gear shop (``utils/mining/market.GEAR_SHOP``).  Coins-only left them
# with a single source; this ladder gives a dedicated fisher a way to **earn**
# them by fishing — exactly as starter mining gear (pickaxe/torch/lantern) is
# both buyable AND craftable.  A recipe consumes ``fish_count`` caught fish whose
# ``size_rank`` is ``≤ max_size_rank`` (smallest-first, reusing the bait loop's
# spend planner) and yields **one** charm into the mining inventory.
#
# The fish path is deliberately the *slow* path — charms want many more fish than
# a bait pack, and the cost climbs steeply up the ladder — so the coin shop stays
# the fast alternative and neither path is free arbitrage (fish a charm consumes
# are worth far less sold than the charm's shop price).


@dataclass(frozen=True)
class CharmRecipe:
    """A fish → charm recipe: consume *fish_count* eligible fish, yield one charm.

    Only fish whose ``size_rank`` is ``≤ max_size_rank`` count as ingredients
    (the smallest are spent first), so crafting drains the common catches a
    fisher accumulates rather than the trophies.  *charm* is the equipment item
    name produced (the mining-inventory key / :data:`utils.equipment` gear name).
    """

    charm: str  # the equipment item name produced (mining-inventory key)
    fish_count: int  # number of eligible fish consumed per craft
    max_size_rank: int  # only fish with size_rank ≤ this are eligible ingredients


#: The charm craft shelf, keyed by charm name.  Costs climb up the ladder and the
#: better charms accept larger fish (so the top charm can absorb a deep haul).
#: Monotonic, and far pricier in fish than the bait shelf — a charm is permanent
#: gear, not a consumable pack.  Numbers sim-pinned in
#: ``docs/planning/fishing-charm-craft-numbers-2026-06-27.md``.
CHARM_RECIPES: dict[str, CharmRecipe] = {
    "fishing charm": CharmRecipe("fishing charm", fish_count=8, max_size_rank=8),
    "anglers charm": CharmRecipe("anglers charm", fish_count=12, max_size_rank=14),
    "master angler charm": CharmRecipe(
        "master angler charm",
        fish_count=18,
        max_size_rank=21,
    ),
}

#: Craftable charm names, in ladder order.
CRAFTABLE_CHARM_NAMES: tuple[str, ...] = tuple(CHARM_RECIPES)


def charm_recipe(name: str | None) -> CharmRecipe | None:
    """The :class:`CharmRecipe` for *name*, or ``None`` if that charm isn't craftable."""
    if not name:
        return None
    return CHARM_RECIPES.get(name.strip().lower())


def charm_recipe_text(recipe: CharmRecipe) -> str:
    """A short human label of a recipe's cost, e.g. ``8 fish (size ≤ 8)``."""
    return f"{recipe.fish_count} fish (size ≤ {recipe.max_size_rank})"


def craftable_charm_for(text: str | None) -> str | None:
    """Resolve typed *text* to a **craftable** charm name (case-insensitive).

    Matches the charm's stored equipment name (``fishing charm``); returns
    ``None`` for empty input or a non-craftable charm — so ``!craftcharm fishing
    charm`` works but a typo / unknown charm does not resolve.
    """
    if not text:
        return None
    needle = text.strip().lower()
    return needle if needle in CHARM_RECIPES else None


__all__ = [
    "PULL_PER_FISHING_POWER",
    "BITE_SPEED_PER_BITE_LUCK",
    "MAX_GEAR_PULL",
    "MIN_GEAR_BITE_SPEED",
    "fishing_pull_mult",
    "fishing_bite_speed_mult",
    "has_fishing_bonus",
    "CharmRecipe",
    "CHARM_RECIPES",
    "CRAFTABLE_CHARM_NAMES",
    "charm_recipe",
    "charm_recipe_text",
    "craftable_charm_for",
]
