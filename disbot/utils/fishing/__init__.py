"""Fishing — pure domain for ecosystem #2 (the second character-platform activity).

Owner design: ``docs/planning/fishing-open-world-expansion-plan-2026-06-18.md``
(Q-0175). Phase 1 = 21 size-ranked fish, 7 levels × 3 fish (level-gated catch),
leveling reuses ``game_xp``; fish value/use is an explicitly deferred owner
question, so v1 has no coins — the reward is progression (unlock bigger fish) +
the collection log.

stdlib-only, state-in/return-out, no Discord and no DB. The species catalog
(:mod:`utils.fishing.fish`) and the level-gated roll (:mod:`utils.fishing.rewards`)
are independently unit-testable; the audited writes live in
``services/fishing_workflow.py``.
"""

from __future__ import annotations

from utils.fishing.fish import (
    FISH_PER_LEVEL,
    MAX_LEVEL,
    SHORE_VENUE,
    SPECIES,
    Catch,
    FishSpecies,
    max_size_rank_for_level,
    species_by_name,
    species_for_venue,
    unlocked_species,
    venue_size_cap,
)
from utils.fishing.rewards import roll_catch
from utils.fishing.venue import (
    DEEPWATER,
    SHORE,
    VenueProfile,
    profile_for,
    toggle,
)
from utils.fishing.weather import (
    CONDITIONS,
    Weather,
    current_weather,
    weather_for_date,
)
from utils.fishing.weight import nominal_weight, roll_weight

__all__ = [
    "CONDITIONS",
    "DEEPWATER",
    "FISH_PER_LEVEL",
    "MAX_LEVEL",
    "SHORE",
    "SHORE_VENUE",
    "SPECIES",
    "Catch",
    "FishSpecies",
    "VenueProfile",
    "Weather",
    "current_weather",
    "max_size_rank_for_level",
    "nominal_weight",
    "profile_for",
    "roll_catch",
    "roll_weight",
    "species_by_name",
    "species_for_venue",
    "toggle",
    "unlocked_species",
    "venue_size_cap",
    "weather_for_date",
]
