"""The creature catalog — 36 original creatures (creature-game v1, Q-0187).

The runtime side of the [creature-game plan](docs/planning/creature-game-design-and-sim-2026-06-20.md):
**original** creatures (no Pokémon IP), 6 per element across four rarities, served
from a committed JSON (``disbot/data/creatures/creatures.json``) "like the BTD6 /
fish data" so adding a creature is a **data row, not code**. The full roster was
validated PLAYABLE by ``tools/game_sim/creature_battle_sim.py`` before it
graduated here (the balance-before-build gate).

**Rarity drives both encounter frequency and catch difficulty** — Common is the
most common spawn and the easiest to catch; Epic is the rarest and the hardest.
Battle stats are deliberately NOT modelled here: catch + collection is the v1
runtime slice, and the PvP engine (where stats derive) is a later
substantial-runtime slice. A creature here carries only name / element /
rarity / archetype / emoji.

Pure + stdlib-only (no Discord, no DB); :mod:`utils.creatures.encounters` does the
rarity-weighted wild roll and :mod:`services.creature_workflow` owns the writes.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger("bot.creatures")

#: Rarity tiers, easiest/most-common → hardest/rarest (the catalog spread).
RARITY_ORDER: tuple[str, ...] = ("Common", "Uncommon", "Rare", "Epic")

#: Relative spawn frequency per rarity — Common dominates wild encounters, an
#: Epic sighting is a treat (mirrors the fishing inverse-size weighting intent).
RARITY_ENCOUNTER_WEIGHT: dict[str, float] = {
    "Common": 100.0,
    "Uncommon": 45.0,
    "Rare": 18.0,
    "Epic": 6.0,
}

#: Base catch chance per rarity (before the small player-level bonus). Rarer is
#: harder to catch — the plan's "catch chance = rarity base × a level bonus".
RARITY_CATCH_BASE: dict[str, float] = {
    "Common": 0.90,
    "Uncommon": 0.65,
    "Rare": 0.40,
    "Epic": 0.20,
}

_FALLBACK_EMOJI = "🐾"

_DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "creatures",
    "creatures.json",
)


@dataclass(frozen=True)
class Creature:
    """One catchable creature — a static catalog row (no battle stats in v1)."""

    name: str
    element: str
    rarity: str
    archetype: str
    emoji: str

    @property
    def encounter_weight(self) -> float:
        """How often this creature shows up in the wild (rarity-driven)."""
        return RARITY_ENCOUNTER_WEIGHT.get(self.rarity, 1.0)

    @property
    def catch_base(self) -> float:
        """The rarity's base catch chance (before the player-level bonus)."""
        return RARITY_CATCH_BASE.get(self.rarity, 0.5)


def _load_creatures() -> tuple[Creature, ...]:
    """Load the committed creature catalog (fail-safe → empty tuple)."""
    try:
        with open(_DATA_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            return ()
        element_emoji = raw.get("element_emoji", {})
        rows = raw.get("creatures", [])
        creatures: list[Creature] = []
        for r in rows:
            if not isinstance(r, dict) or not {"name", "element", "rarity"} <= r.keys():
                continue
            element = str(r["element"]).strip()
            creatures.append(
                Creature(
                    name=str(r["name"]).strip(),
                    element=element,
                    rarity=str(r["rarity"]).strip(),
                    archetype=str(r.get("archetype", "balanced")).strip(),
                    emoji=str(element_emoji.get(element, _FALLBACK_EMOJI)),
                ),
            )
        # Stable order: by rarity tier then name, so renders are deterministic.
        rarity_index = {r: i for i, r in enumerate(RARITY_ORDER)}
        creatures.sort(
            key=lambda c: (rarity_index.get(c.rarity, len(RARITY_ORDER)), c.name),
        )
        return tuple(creatures)
    except (OSError, ValueError, KeyError, TypeError):
        logger.exception("creatures: failed to load %s", _DATA_FILE)
        return ()


#: The full catalog, sorted by rarity tier then name.
CREATURES: tuple[Creature, ...] = _load_creatures()

#: Distinct elements present in the catalog, in first-seen order.
ELEMENTS: tuple[str, ...] = tuple(dict.fromkeys(c.element for c in CREATURES))

# Catalog lookups are case-insensitive on the creature's canonical name.
_BY_NAME: dict[str, Creature] = {c.name.lower(): c for c in CREATURES}


def creature_by_name(name: str) -> Creature | None:
    """Look up a creature by name (case-insensitive; ``None`` if unknown)."""
    return _BY_NAME.get(name.strip().lower())


def creature_names() -> list[str]:
    """Every canonical creature name in the current catalog (for allow-lists)."""
    return [c.name for c in CREATURES]
