"""Fishing loot roll — pure functions (mirrors ``utils/mining/rewards``).

State-in (an explicit ``random.Random`` for seed-determinism in tests),
return-out, no Discord, no DB.  The roll is two-stage: pick a rarity tier by
:data:`utils.fishing.fish.RARITY_ROLL_WEIGHT`, then a uniform species within
that tier, then a uniform weight + coin value inside the species' bands.
"""

from __future__ import annotations

import random

from utils.fishing.fish import (
    RARITY_ROLL_WEIGHT,
    Catch,
    FishSpecies,
    species_by_rarity,
)

# Each +1 of rod bonus nudges the rarity roll: it shifts a slice of the common
# weight toward the rarer tiers, so a better rod catches better fish without
# ever removing commons entirely (additive-safe; bonus 0 == the base table).
_ROD_TIER_SHIFT = 4.0


def _weighted_tier_table(rod_bonus: int) -> dict[str, float]:
    """The rarity-roll weights adjusted for a rod bonus (bonus 0 == base)."""
    if rod_bonus <= 0:
        return dict(RARITY_ROLL_WEIGHT)
    shift = min(RARITY_ROLL_WEIGHT["common"] - 1.0, _ROD_TIER_SHIFT * rod_bonus)
    table = dict(RARITY_ROLL_WEIGHT)
    table["common"] -= shift
    # Spread the freed weight across the four non-common tiers, proportionally.
    rarer = {k: v for k, v in RARITY_ROLL_WEIGHT.items() if k != "common"}
    rarer_total = sum(rarer.values())
    for tier, base in rarer.items():
        table[tier] += shift * (base / rarer_total)
    return table


def roll_catch(rng: random.Random | None = None, *, rod_bonus: int = 0) -> Catch:
    """Roll one catch — a :class:`Catch` (species + weight + coin value).

    *rng* lets tests pin the roll; production passes ``None`` (the module
    ``random``).  *rod_bonus* (0 = bare hands / no rod) biases the rarity tier
    toward rarer fish without ever excluding commons.
    """
    r = rng or random.Random()
    table = _weighted_tier_table(rod_bonus)
    tier = r.choices(list(table.keys()), weights=list(table.values()), k=1)[0]
    pool = species_by_rarity(tier)
    species: FishSpecies = pool[r.randrange(len(pool))]
    weight = round(r.uniform(species.weight_min, species.weight_max), 1)
    value = r.randint(species.value_min, species.value_max)
    return Catch(species=species, weight=weight, value=value)
