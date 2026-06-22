"""Fishing bait — the optional *second* pre-cast economy knob (Q-0175 §4).

The fishing design's named follow-up layer
(``docs/planning/fishing-minigame-design-2026-06-22.md`` §4, "Bait as the second
economy knob"): bait is an **optional, coin-bought consumable** that biases the
catch toward rarer / bigger fish for a bounded number of casts. Fish became
sellable + cookable in #1289, so bait gives those coins somewhere to go *and* a
pre-cast decision ("load a lure before this trip?") sitting beside the rod ladder.

The two-knob model stays clean:

* **Fishing level** (``game_xp``) gates *what* you can catch — the size bands.
* **The rod** (:mod:`utils.fishing.rods`) is the permanent *how-well* axis.
* **Bait** is the *consumable* how-well axis: while you hold charges, each cast
  spends one and multiplies the rod's ``rarity_pull`` (the reward-quality knob),
  so a loaded lure pulls the catch toward the big end of your unlocked band —
  *never* a new band (that stays the fishing-level axis), and the starter setup
  still catches fine without it (bait only improves, never gates).

Pure + stdlib-only (no Discord, no DB): :mod:`services.fishing_workflow` owns the
purchase write + the per-cast consume; the bait shop view reads this catalog.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Bait:
    """One bait type — a stable key, presentation, its knob, charges, and price."""

    key: str  # stable lookup key (stored in the fishing_bait row)
    name: str
    emoji: str
    rarity_pull: float  # ≥ 1 multiplier applied ON TOP of the equipped rod's pull
    charges: int  # casts one bought pack lasts
    price: int  # coin cost of one pack


#: The bait shelf, cheapest → finest. ``rarity_pull`` multiplies the rod's own
#: pull (so a Gold Rod at 1.45 with a Shimmer Lure at 2.0 fishes at 2.9), charges
#: bound the boost so it's a *consumable* sink, prices are tunable constants.
BAIT_CATALOG: tuple[Bait, ...] = (
    Bait("worm", "Worm Bait", "🪱", rarity_pull=1.25, charges=10, price=150),
    Bait("grub", "Glow Grub", "🐛", rarity_pull=1.50, charges=10, price=400),
    Bait("lure", "Shimmer Lure", "✨", rarity_pull=2.00, charges=10, price=1000),
)

_BY_KEY: dict[str, Bait] = {b.key: b for b in BAIT_CATALOG}

#: The stable keys, in shelf order (for selects / validation).
BAIT_KEYS: tuple[str, ...] = tuple(b.key for b in BAIT_CATALOG)


def bait_by_key(key: str | None) -> Bait | None:
    """The :class:`Bait` for *key*, or ``None`` for an unknown / empty key."""
    if not key:
        return None
    return _BY_KEY.get(key)
