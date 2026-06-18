"""The fishing species catalog — 21 size-ranked fish (owner design Q-0175).

The owner's Phase-1 spec (``docs/planning/fishing-open-world-expansion-plan-2026-06-18.md``):
**21 fish ranked by size** (``size_rank`` 1 = smallest … 21 = largest), served
from a committed JSON (``disbot/data/fishing/fish.json``) "like the BTD6 / gear
data".  **7 fishing levels, 3 fish per level:** the starting rod catches the 3
smallest (level 1); each level up unlocks **+3** bigger fish, so level 7 reaches
all 21 (``3 × 7 = 21``).  Value/flavour are deliberately deferred (an open
owner question) — a fish carries only a name, a size rank, and an emoji here.

Pure + stdlib-only (no Discord, no DB); :mod:`utils.fishing.rewards` does the
level-gated roll and :mod:`services.fishing_workflow` owns the writes.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger("bot.fishing")

#: 3 fish per fishing level, 7 levels — the owner's clean 21 = 3 × 7 split.
FISH_PER_LEVEL = 3
MAX_LEVEL = 7

_DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "fishing",
    "fish.json",
)


@dataclass(frozen=True)
class FishSpecies:
    """One catchable species — a static catalog row (ranked by size)."""

    name: str
    size_rank: int
    emoji: str


@dataclass(frozen=True)
class Catch:
    """One rolled catch — just the species (no value/weight in v1)."""

    species: FishSpecies


def _load_species() -> tuple[FishSpecies, ...]:
    """Load + sort the committed fish dataset by size rank (fail-safe → empty)."""
    try:
        with open(_DATA_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        rows = raw.get("fish", []) if isinstance(raw, dict) else []
        species = [
            FishSpecies(
                name=str(r["name"]).strip().lower(),
                size_rank=int(r["size_rank"]),
                emoji=str(r.get("emoji", "🐟")),
            )
            for r in rows
            if isinstance(r, dict) and "name" in r and "size_rank" in r
        ]
        species.sort(key=lambda s: s.size_rank)
        return tuple(species)
    except (OSError, ValueError, KeyError, TypeError):
        logger.exception("fishing: failed to load %s", _DATA_FILE)
        return ()


#: The full catalog, sorted smallest → largest.
SPECIES: tuple[FishSpecies, ...] = _load_species()

_BY_NAME: dict[str, FishSpecies] = {s.name: s for s in SPECIES}


def species_by_name(name: str) -> FishSpecies | None:
    """Look up a species by canonical lowercase name (``None`` if unknown)."""
    return _BY_NAME.get(name.strip().lower())


def max_size_rank_for_level(level: int) -> int:
    """The largest ``size_rank`` catchable at fishing *level* (1-based).

    Level 1 → 3, level 2 → 6, … capped at the catalog size (the owner's
    "each level unlocks +3 bigger fish" rule). Level ≤ 0 is treated as 1.
    """
    band = max(1, level) * FISH_PER_LEVEL
    return min(band, len(SPECIES))


def unlocked_species(level: int) -> list[FishSpecies]:
    """Every species catchable at fishing *level* (size_rank ≤ the band cap)."""
    cap = max_size_rank_for_level(level)
    return [s for s in SPECIES if s.size_rank <= cap]
