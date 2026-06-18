"""The fishing species catalog — fishing's own loot ladder (pure, stdlib-only).

The survival plan's ecosystem-ready-seams note (P3 "Open") requires fishing to
own its loot ladder rather than reskin the ore weights.  This module is that
ladder: a self-contained, frozen catalog of catchable species with a rarity
tier, a coin-value band, and a weight (kg) band.

A ``Catch`` is one rolled result — the species plus the specific weight and
coin value the roll produced.  :mod:`utils.fishing.rewards` does the rolling;
this module is data + lookups only.
"""

from __future__ import annotations

from dataclasses import dataclass

# Rarity tiers in ascending order.  The roll weight (how often a tier is picked)
# is the inverse of worth — common fish are caught constantly, legendary ones
# almost never.  One table to retune the whole economy.
RARITY_ROLL_WEIGHT: dict[str, float] = {
    "common": 60.0,
    "uncommon": 25.0,
    "rare": 11.0,
    "epic": 3.5,
    "legendary": 0.5,
}


@dataclass(frozen=True)
class FishSpecies:
    """One catchable species — the static catalog row (never a rolled result)."""

    name: str
    emoji: str
    rarity: str
    #: Inclusive coin-value band; the roll picks a value in ``[min, max]``.
    value_min: int
    value_max: int
    #: Inclusive weight band in kilograms (one decimal); flavour + records.
    weight_min: float
    weight_max: float


@dataclass(frozen=True)
class Catch:
    """One rolled catch — a species plus the specific weight + coins it yielded."""

    species: FishSpecies
    weight: float
    value: int


# The catalog.  Coin bands climb with rarity so a legendary is worth many
# commons, but every payout stays modest by design (a fish is worth less than a
# mined gem; balance lives here + the game-XP daily soft cap throttles grind).
SPECIES: tuple[FishSpecies, ...] = (
    # common
    FishSpecies("sardine", "🐟", "common", 2, 5, 0.1, 0.4),
    FishSpecies("anchovy", "🐟", "common", 2, 5, 0.1, 0.3),
    FishSpecies("herring", "🐟", "common", 3, 6, 0.2, 0.6),
    FishSpecies("perch", "🐟", "common", 3, 7, 0.3, 0.9),
    # uncommon
    FishSpecies("mackerel", "🐠", "uncommon", 6, 12, 0.4, 1.2),
    FishSpecies("bass", "🐠", "uncommon", 8, 15, 0.6, 2.5),
    FishSpecies("trout", "🐠", "uncommon", 8, 16, 0.5, 2.0),
    # rare
    FishSpecies("salmon", "🐡", "rare", 18, 30, 1.5, 5.0),
    FishSpecies("pike", "🐡", "rare", 20, 34, 2.0, 7.0),
    FishSpecies("tuna", "🐡", "rare", 25, 40, 8.0, 60.0),
    # epic
    FishSpecies("swordfish", "🗡️", "epic", 50, 85, 40.0, 200.0),
    FishSpecies("marlin", "🗡️", "epic", 60, 100, 60.0, 350.0),
    # legendary
    FishSpecies("golden koi", "✨", "legendary", 200, 400, 0.5, 4.0),
    FishSpecies("ancient leviathan", "🐉", "legendary", 400, 800, 500.0, 2000.0),
)

_BY_NAME: dict[str, FishSpecies] = {s.name: s for s in SPECIES}


def species_by_name(name: str) -> FishSpecies | None:
    """Look up a species by its canonical lowercase name (``None`` if unknown)."""
    return _BY_NAME.get(name.strip().lower())


def species_by_rarity(rarity: str) -> list[FishSpecies]:
    """Every species in *rarity*, in catalog order."""
    return [s for s in SPECIES if s.rarity == rarity]
