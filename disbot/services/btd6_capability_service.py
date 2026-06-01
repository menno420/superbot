"""Cross-entity BTD6 capability queries — "which towers have property X".

Answers discovery questions the entity resolver cannot ("which tower sees camo
unupgraded?", "what pops lead at base?") by scanning the per-tier tower stats
from :mod:`services.btd6_stats_service`. Derived at runtime, so it always
matches the committed stats files — there is no separate index to maintain.

Backs the ``btd6_capability_lookup`` AI tool; could back a UI later. Read-only,
no DB, no network.
"""

from __future__ import annotations

from dataclasses import dataclass

from services import btd6_data_service, btd6_stats_service
from utils.btd6 import tier_codes

# Supported capability keys (kept small and well-defined — these are the
# cross-entity questions the resolver path cannot answer on its own).
CAMO_DETECTION = "camo_detection"
LEAD_POPPING = "lead_popping"
BLACK_POPPING = "black_popping"
WHITE_POPPING = "white_popping"
PURPLE_POPPING = "purple_popping"
CAPABILITIES: tuple[str, ...] = (
    CAMO_DETECTION,
    LEAD_POPPING,
    BLACK_POPPING,
    WHITE_POPPING,
    PURPLE_POPPING,
)

# Capability key -> the bloon-type keyword that, when named in a tier's
# ``cannot_pop`` note, means the tier CANNOT pop that bloon. All popping
# capabilities share one derivation: a tier with positive damage pops the bloon
# unless its immunity note names it. (None of these keywords is a substring of
# another, so the membership test is unambiguous.)
_POPPING_IMMUNITY: dict[str, str] = {
    LEAD_POPPING: "lead",
    BLACK_POPPING: "black",
    WHITE_POPPING: "white",
    PURPLE_POPPING: "purple",
}


@dataclass(frozen=True)
class CapabilityHit:
    """One tower that has the requested capability, and where it gets it."""

    tower_id: str
    canonical: str
    detail: str  # e.g. "innate (0-0-0)" or "Explosion at base" / "from 0-2-0"


def _tier_has_capability(capability: str, tier: dict) -> bool:
    """True when a single tier node satisfies ``capability``."""
    ns = btd6_stats_service.normal_stats(tier)
    if capability == CAMO_DETECTION:
        # Only meaningful for attacking tiers — a tier with no attack cannot
        # "see" anything, so require a damage value before crediting camo.
        return ns.damage is not None and ns.can_see_camo
    immunity = _POPPING_IMMUNITY.get(capability)
    if immunity is not None:
        if ns.damage is None or ns.damage <= 0:
            return False
        # cannot_pop is the authoritative immunity note (from the BTD6 dt
        # table); a tier pops the bloon unless that note names it.
        return immunity not in (ns.cannot_pop or "").lower()
    return False


def _base_detail(capability: str, tier: dict) -> str:
    ns = btd6_stats_service.normal_stats(tier)
    if capability == CAMO_DETECTION:
        return "innate (0-0-0)"
    return f"{ns.damage_type or 'damage'} at base (0-0-0)"


def towers_with_capability(
    capability: str,
    *,
    unupgraded: bool = True,
) -> list[CapabilityHit]:
    """Towers that have ``capability``.

    ``unupgraded=True`` (default) checks only the base (0-0-0) tier — the
    classic "without any upgrades" question. ``unupgraded=False`` also includes
    towers that gain it via an upgrade, reporting the earliest crosspath.
    Returns an empty list for an unknown capability or unknown towers.
    """
    if capability not in CAPABILITIES:
        return []
    hits: list[CapabilityHit] = []
    for tower in btd6_data_service.get_dataset().towers:
        stats = btd6_stats_service.get_tower_stats(tower.id)
        if stats is None or not stats.has_combat_stats:
            continue
        base = stats.tier("000")
        if base is not None and _tier_has_capability(capability, base):
            hits.append(
                CapabilityHit(
                    tower_id=tower.id,
                    canonical=tower.canonical,
                    detail=_base_detail(capability, base),
                ),
            )
            continue
        if unupgraded:
            continue
        # Earliest single-path tier that grants the capability (crosspaths are a
        # presentation concern; capability discovery stays on the 16 tiers).
        for code in stats.tier_codes():
            if code == "000" or not tier_codes.is_single_path(code):
                continue
            tier = stats.tier(code)
            if tier is not None and _tier_has_capability(capability, tier):
                hits.append(
                    CapabilityHit(
                        tower_id=tower.id,
                        canonical=tower.canonical,
                        detail=f"from {'-'.join(code)}",
                    ),
                )
                break
    return hits


__all__ = [
    "BLACK_POPPING",
    "CAMO_DETECTION",
    "CAPABILITIES",
    "LEAD_POPPING",
    "PURPLE_POPPING",
    "WHITE_POPPING",
    "CapabilityHit",
    "towers_with_capability",
]
