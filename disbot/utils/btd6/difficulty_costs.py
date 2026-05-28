"""Derive BTD6 tower/upgrade costs for any difficulty from the Medium price.

BTD6 stores a single "Medium" (default) cost for every tower and upgrade
and computes the other difficulties by a fixed multiplier, then rounds to
the nearest $5. Storing only the Medium value and deriving the rest keeps
the data set small and single-sourced — see ``docs`` / the BTD6 data
fixtures, which persist Medium costs only.

Multipliers (verified exact against the published Bomb Shooter cost table,
all 16 upgrades incl. the Paragon — every Easy/Hard/Impoppable value
reproduced):

    Easy        × 0.85
    Medium      × 1.00   (the stored value)
    Hard        × 1.08
    Impoppable  × 1.20

Rounding is to the nearest multiple of 5; exact half-ties (which only arise
from the ×0.85 Easy multiplier) resolve **down** to the lower multiple.
``Fraction`` is used so the half-tie boundary is decided exactly rather than
at the mercy of binary float error.

Lives in ``utils/`` (pure, stdlib-only) so services, views, and the AI
grounding layer can all derive costs without crossing a layer boundary.
"""

from __future__ import annotations

import math
from fractions import Fraction

# Canonical difficulty keys, in display order.
DIFFICULTIES: tuple[str, ...] = ("easy", "medium", "hard", "impoppable")

_MULTIPLIERS: dict[str, Fraction] = {
    "easy": Fraction(85, 100),
    "medium": Fraction(1),
    "hard": Fraction(108, 100),
    "impoppable": Fraction(120, 100),
}

# Game modes that price like an existing difficulty rather than defining
# their own multiplier (e.g. CHIMPS uses Hard pricing).
_DIFFICULTY_ALIASES: dict[str, str] = {
    "": "medium",
    "normal": "medium",
    "standard": "medium",
    "chimps": "hard",
}


def _round_to_5_ties_down(value: Fraction) -> int:
    """Round to the nearest multiple of 5; exact .5-of-5 ties go down."""
    # round-half-down(x) == ceil(x - 1/2); applied in units of 5.
    fifths = math.ceil(value / 5 - Fraction(1, 2))
    return fifths * 5


def normalize_difficulty(difficulty: str) -> str:
    """Map a free-form difficulty/mode label to a canonical key.

    Raises ``ValueError`` for anything we don't recognise so callers fail
    loudly rather than silently pricing at Medium.
    """
    key = difficulty.strip().lower()
    key = _DIFFICULTY_ALIASES.get(key, key)
    if key not in _MULTIPLIERS:
        raise ValueError(f"unknown BTD6 difficulty: {difficulty!r}")
    return key


def cost_for_difficulty(medium_cost: int, difficulty: str) -> int:
    """Scale a Medium cost to ``difficulty``.

    ``medium_cost`` is the stored value; ``difficulty`` is case-insensitive
    and accepts mode aliases (e.g. ``"chimps"`` → Hard pricing).
    """
    key = normalize_difficulty(difficulty)
    if key == "medium":
        return medium_cost
    return _round_to_5_ties_down(Fraction(medium_cost) * _MULTIPLIERS[key])


def all_difficulty_costs(medium_cost: int) -> dict[str, int]:
    """Return ``{difficulty: cost}`` for all four difficulties."""
    return {d: cost_for_difficulty(medium_cost, d) for d in DIFFICULTIES}


__all__ = [
    "DIFFICULTIES",
    "all_difficulty_costs",
    "cost_for_difficulty",
    "normalize_difficulty",
]
