"""Creatures — pure domain for the creature catch/collection game (v1).

The runtime side of ``docs/planning/creature-game-design-and-sim-2026-06-20.md``
(Q-0186/Q-0187): **original** creatures (no Pokémon IP), 6 per element across four
rarities, served from a committed JSON catalog and validated PLAYABLE by the
Monte-Carlo battle sim before graduating here. v1 ships the **catch + collection**
half — wild encounters, a rarity-weighted catch roll, and a collection "dex";
leveling reuses the shared ``game_xp`` track. The level-normalized PvP battle
engine (:mod:`utils.creatures.battle`) is the foundation for the later
substantial-runtime cog/views slice.

stdlib-only, state-in/return-out, no Discord and no DB. The catalog
(:mod:`utils.creatures.creature`), the encounter/catch roll
(:mod:`utils.creatures.encounters`), and the battle engine
(:mod:`utils.creatures.battle`) are independently unit-testable; the audited
writes live in ``services/creature_workflow.py``.
"""

from __future__ import annotations

from utils.creatures.battle import (
    ELEMENT_CYCLE,
    NORMALIZED_LEVEL,
    BattleEvent,
    BattleOutcome,
    BattleStats,
    Combatant,
    Move,
    build_team,
    derive_stats,
    effectiveness,
    fresh_team,
    moves_for,
    resolve_battle,
    standard_team,
)
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
    "ELEMENT_CYCLE",
    "NORMALIZED_LEVEL",
    "RARITY_CATCH_BASE",
    "RARITY_ENCOUNTER_WEIGHT",
    "RARITY_ORDER",
    "BattleEvent",
    "BattleOutcome",
    "BattleStats",
    "Combatant",
    "Creature",
    "Encounter",
    "Move",
    "attempt_catch",
    "build_team",
    "catch_chance",
    "creature_by_name",
    "creature_names",
    "derive_stats",
    "effectiveness",
    "fresh_team",
    "moves_for",
    "resolve_battle",
    "roll_encounter",
    "standard_team",
]
