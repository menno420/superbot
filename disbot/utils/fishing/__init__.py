"""Fishing — pure domain for ecosystem #2 (the second character-platform activity).

Mirrors ``utils/mining/``: stdlib-only, state-in/return-out, no Discord and no
DB.  The species catalog (:mod:`utils.fishing.fish`) and the catch roll
(:mod:`utils.fishing.rewards`) are independently unit-testable without a mock
harness.  The audited write boundary lives in ``services/fishing_workflow.py``;
this package never touches the database.

Plan: ``docs/planning/fishing-ecosystem-plan-2026-06-18.md``.
"""

from __future__ import annotations

from utils.fishing.fish import (
    SPECIES,
    Catch,
    FishSpecies,
    species_by_name,
)
from utils.fishing.rewards import roll_catch

__all__ = [
    "SPECIES",
    "Catch",
    "FishSpecies",
    "roll_catch",
    "species_by_name",
]
