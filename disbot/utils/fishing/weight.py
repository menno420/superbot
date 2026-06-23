"""Per-catch weight roll — pure, the basis of the trophy-records goal.

The owner design lists **"trophy records per species (biggest caught)"** as a
cheap long-tail retention goal layered on the existing catch-log
(``docs/planning/fishing-minigame-design-2026-06-22.md`` §"Other ideas"). For a
"biggest caught" record to mean anything each individual catch needs its own
weight — otherwise every catch of a species is identical and there is nothing to
beat.

So every catch rolls a weight here: a species *nominal* weight that grows with
its ``size_rank`` (bigger fish are heavier), times a per-catch random factor so
two catches of the same species differ and a lucky heavy one becomes a personal
best worth chasing. Bounded, deterministic with an explicit ``random.Random``
(seed-stable in tests), no Discord and no DB — :mod:`utils.fishing.rewards`
calls it as part of the roll and :mod:`services.fishing_workflow` records the
heaviest.
"""

from __future__ import annotations

import random

from utils.fishing.fish import FishSpecies

#: Weight curve — ``nominal_kg = _BASE * size_rank ** _EXP``. Tuned so the
#: smallest fish (#1) is a few hundred grams and the largest (#21) is a
#: trophy-grade haul, with a smooth ramp between (see ``test_fishing_weight``).
_BASE = 0.18
_EXP = 1.65

#: Per-catch spread around the nominal — a catch weighs ``nominal × U(LO, HI)``,
#: so any species can occasionally produce a personal-best lunker.
_SPREAD_LO = 0.65
_SPREAD_HI = 1.55


def nominal_weight(species: FishSpecies) -> float:
    """The species' average weight in kg (grows with ``size_rank``).

    The midpoint a catch varies around — bigger-ranked fish are heavier. Pure
    function of the static catalog, so it is stable across catches.
    """
    return round(_BASE * (species.size_rank**_EXP), 2)


def roll_weight(species: FishSpecies, rng: random.Random | None = None) -> float:
    """Roll one catch's individual weight in kg (≥ 0.01).

    The species :func:`nominal_weight` times a bounded random factor, so repeat
    catches of the same fish differ and the heaviest becomes the trophy record.
    Deterministic for a given ``rng`` (tests pass a seeded ``random.Random``).
    """
    r = rng or random.Random()
    factor = r.uniform(_SPREAD_LO, _SPREAD_HI)
    return max(0.01, round(nominal_weight(species) * factor, 2))
