"""Creatures — pure domain for the creature catch/collection game (v1).

The runtime side of ``docs/planning/creature-game-design-and-sim-2026-06-20.md``
(Q-0186/Q-0187): **original** creatures (no Pokémon IP), 6 per element across four
rarities, served from a committed JSON catalog and validated PLAYABLE by the
Monte-Carlo battle sim before graduating here. v1 ships the **catch + collection**
half — wild encounters, a rarity-weighted catch roll, and a collection "dex";
leveling reuses the shared ``game_xp`` track. The level-normalized PvP battle
engine is a later ``needs-hermes-review`` slice.

stdlib-only, state-in/return-out, no Discord and no DB. The catalog
(:mod:`utils.creatures.creature`) and the encounter/catch roll
(:mod:`utils.creatures.encounters`) are independently unit-testable; the audited
writes live in ``services/creature_workflow.py``.
"""

from __future__ import annotations

from utils.creatures.creature import (
    CREATURES,
    ELEMENTS,
    RARITY_CATCH_BASE,
    RARITY_ENCOUNTER_WEIGHT,
    RARITY_ORDER,
    Creature,
    creature_by_name,
    creature_names,
)
from utils.creatures.encounters import (
    Encounter,
    attempt_catch,
    catch_chance,
    roll_encounter,
)

__all__ = [
    "CREATURES",
    "ELEMENTS",
    "RARITY_CATCH_BASE",
    "RARITY_ENCOUNTER_WEIGHT",
    "RARITY_ORDER",
    "Creature",
    "Encounter",
    "attempt_catch",
    "catch_chance",
    "creature_by_name",
    "creature_names",
    "roll_encounter",
]
