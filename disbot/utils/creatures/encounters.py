"""Wild encounters + the catch roll — pure (creature-game v1).

The catch mechanic from the [plan](docs/planning/creature-game-design-and-sim-2026-06-20.md)
§2: a wild encounter spawns a creature (weighted by rarity — Common common, Epic
rare), and the catch succeeds with ``rarity base × a small player-level bonus``
(rarer = harder). Unlike fishing there is **no level gate** — every rarity can be
encountered from level 1; the player's level only nudges the catch odds. Raw level
matters for PvE/collection prestige (and, later, level-normalized PvP).

State-in (an explicit ``random.Random`` for seed-determinism in tests),
return-out; no Discord, no DB.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from utils.creatures.creature import CREATURES, Creature

#: Per-level catch-chance bonus and its cap — keeps a high-level player from
#: trivially catching Epics while still rewarding investment (the plan's
#: "small player-level bonus").
CATCH_BONUS_PER_LEVEL = 0.02
MAX_CATCH_BONUS = 0.20
#: A catch is never a sure thing, even for a Common at high level — there is
#: always a chance the creature flees (keeps the catch loop a real action).
MAX_CATCH_CHANCE = 0.95


@dataclass(frozen=True)
class Encounter:
    """One wild encounter — the creature that appeared (catch not yet rolled)."""

    creature: Creature


def roll_encounter(rng: random.Random | None = None) -> Encounter | None:
    """Spawn one wild creature, weighted by rarity (``None`` if catalog empty).

    Common creatures dominate; an Epic sighting is rare — the rarity encounter
    weights make the wild feel populated by ordinary creatures with the
    occasional prize.
    """
    if not CREATURES:
        return None
    r = rng or random.Random()
    weights = [c.encounter_weight for c in CREATURES]
    creature: Creature = r.choices(CREATURES, weights=weights, k=1)[0]
    return Encounter(creature=creature)


def catch_chance(creature: Creature, level: int) -> float:
    """The probability of catching *creature* at player *level* (0.0–``MAX``).

    ``rarity base + level bonus``, capped: rarer creatures start lower, and the
    per-level bonus is small and bounded so level helps but never guarantees.
    """
    bonus = min(MAX_CATCH_BONUS, max(0, level) * CATCH_BONUS_PER_LEVEL)
    return min(MAX_CATCH_CHANCE, creature.catch_base + bonus)


def attempt_catch(
    creature: Creature,
    level: int,
    rng: random.Random | None = None,
) -> bool:
    """Roll whether the player catches *creature* at *level* (True = caught)."""
    r = rng or random.Random()
    return r.random() < catch_chance(creature, level)
