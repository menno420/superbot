"""Mining structures — pure build/gating math for the §7.5 structure sinks.

Slice B of ``docs/planning/mining-structures-skill-tree-plan-2026-06-14.md``: the
**Forge**, a *built* structure (coin + material sink) that unlocks higher-tier
gear crafting, tying the structure ladder into the existing 5-tier gear ladder
(``utils.equipment``).  The ``mining_structures`` table is generic
(``(user, guild, structure, level)``) so later slices — the Home backdrop
(Slice C) — reuse the same store and this module's ``BuildCost`` shape.

Design (kept **additive**): the forge requirement is derived from a recipe's
gear tier, but only the **top two** tiers gate — bronze / iron / silver gear,
every tool, and every structure stay craftable at forge level 0, so existing
play is unchanged until a player reaches gold/diamond gear.  Gold needs a level-1
forge, diamond a level-2 forge, and the forge is cheap and buildable immediately,
so the gate is a progression beat, not a wall.

Numbers here are the **pinned defaults** — see
``docs/planning/forge-numbers-2026-06-15.md`` (mirrored by
``tests/unit/utils/test_mining_structures.py``).  This is a ``utils`` module: it
imports stdlib + ``utils.equipment`` only (no services / db), so the service,
view, and cog layers share one source of truth for the math.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from utils import equipment

#: The buildable structures.  Each is a ``(user, guild, structure, level)`` row in
#: the generic ``mining_structures`` table and shares ``build_structure`` — adding
#: one is its registry entry below plus (for Home) a render hook.
FORGE = "forge"
HOME = "home"

#: Gear at or below this tier index needs **no** forge (bronze=1, iron=2,
#: silver=3 are free; gold=4 → forge 1; diamond=5 → forge 2).  ``forge_level =
#: max(0, tier_index - FREE_TIER_CEILING)``.
FREE_TIER_CEILING = 3

#: The forge level shown in the panel / gate message per level.
_FORGE_LEVEL_NAMES = ("(not built)", "Forge I", "Forge II")

#: Home is purely cosmetic (Slice C): each level unlocks a nicer Character-card
#: backdrop (the colour palette lives in ``utils.character_render``).  No gameplay
#: gate — Home is a coin/material *sink* with a visible reward, never a wall.
_HOME_LEVEL_NAMES = ("(not built)", "Cozy Cabin", "Stone Keep", "Grand Hall")


@dataclass(frozen=True)
class BuildCost:
    """The cost to build/upgrade a structure one level: coins + raw materials."""

    coins: int
    materials: dict[str, int] = field(default_factory=dict)


#: Forge build ladder — cost to go level → level + 1.  Index ``i`` is the cost to
#: build the *(i+1)*-th level (index 0 = unbuilt → Forge I).  Rising coin +
#: material sink; tunable (pin changes in the numbers doc + the test).
_FORGE_BUILD_LADDER: tuple[BuildCost, ...] = (
    # → Forge I (unlocks gold-tier gear)
    BuildCost(coins=3_000, materials={"iron": 25, "stone": 15}),
    # → Forge II (unlocks diamond-tier gear)
    BuildCost(coins=8_000, materials={"gold": 20, "iron": 10}),
)

#: Home build ladder — a rising coin + material sink for the three cosmetic tiers
#: (pin changes in ``docs/planning/home-numbers-2026-06-15.md`` + the test).
_HOME_BUILD_LADDER: tuple[BuildCost, ...] = (
    # → Cozy Cabin (a warm backdrop)
    BuildCost(coins=2_000, materials={"wood": 30, "stone": 20}),
    # → Stone Keep (a cool stone backdrop)
    BuildCost(coins=5_000, materials={"stone": 50, "iron": 15}),
    # → Grand Hall (a regal backdrop)
    BuildCost(coins=12_000, materials={"gold": 15, "diamond": 3}),
)


@dataclass(frozen=True)
class StructureDef:
    """A buildable structure: its display name, build ladder, and level names."""

    key: str
    display: str
    ladder: tuple[BuildCost, ...]
    level_names: tuple[str, ...]


#: The structure registry — the single source of truth for build math + naming.
#: ``build_structure`` and the panels read this generically, so a new structure
#: is one entry here (plus any structure-specific reward wiring).
_DEFS: dict[str, StructureDef] = {
    FORGE: StructureDef(FORGE, "Forge", _FORGE_BUILD_LADDER, _FORGE_LEVEL_NAMES),
    HOME: StructureDef(HOME, "Home", _HOME_BUILD_LADDER, _HOME_LEVEL_NAMES),
}

STRUCTURES: tuple[str, ...] = tuple(_DEFS)

#: Highest forge level (level 2 unlocks the diamond tier — the top of the gear
#: ladder, so nothing above it needs a higher forge).
MAX_FORGE_LEVEL = len(_FORGE_BUILD_LADDER)

#: Highest Home level (the top cosmetic backdrop).
MAX_HOME_LEVEL = len(_HOME_BUILD_LADDER)


def is_structure(name: str) -> bool:
    """True if *name* is a buildable structure (case/space-insensitive)."""
    return name.strip().lower() in _DEFS


# --------------------------------------------------------------------------- #
# Generic per-structure build math — the registry-driven source of truth.
# --------------------------------------------------------------------------- #


def display_name(structure: str) -> str:
    """The human display name of *structure* (e.g. ``"Forge"`` / ``"Home"``)."""
    return _DEFS[structure].display


def max_level(structure: str) -> int:
    """The highest level *structure* can reach (= its build-ladder length)."""
    return len(_DEFS[structure].ladder)


def level_name(structure: str, level: int) -> str:
    """A short display name for *structure* at *level* (clamped to its ladder)."""
    defn = _DEFS[structure]
    level = max(0, min(level, len(defn.ladder)))
    return defn.level_names[level]


def build_cost(structure: str, level: int) -> BuildCost | None:
    """Cost to upgrade *structure* **from** *level* to *level* + 1, or ``None`` if maxed."""
    defn = _DEFS[structure]
    if level < 0 or level >= len(defn.ladder):
        return None
    return defn.ladder[level]


# --------------------------------------------------------------------------- #
# Forge-specific helpers — thin wrappers over the generic math (back-compat with
# the Slice B forge panel + tests; behaviour byte-identical).
# --------------------------------------------------------------------------- #


def forge_level_name(level: int) -> str:
    """A short display name for a forge at *level* (clamped to the ladder)."""
    return level_name(FORGE, level)


def forge_build_cost(level: int) -> BuildCost | None:
    """Cost to upgrade the forge **from** *level* to *level* + 1, or ``None`` if maxed."""
    return build_cost(FORGE, level)


def forge_level_required(recipe_name: str) -> int:
    """Minimum forge level needed to craft *recipe_name* (0 = no forge needed).

    Derived from the recipe product's gear tier: only gold/diamond set-gear
    gates.  Tools, structures, starters, and bronze/iron/silver gear all return
    0, so the overwhelming majority of recipes are forge-free (the additive
    property — existing craft paths never change behaviour).
    """
    tier = equipment.gear_tier(recipe_name)
    if tier is None:
        return 0
    return max(0, equipment.tier_index(tier) - FREE_TIER_CEILING)


def meets_forge_requirement(recipe_name: str, forge_level: int) -> bool:
    """True if a forge at *forge_level* may craft *recipe_name*."""
    return forge_level >= forge_level_required(recipe_name)


def tiers_unlocked_at(forge_level: int) -> tuple[str, ...]:
    """The gear tiers a forge at *forge_level* unlocks **beyond** the free tiers.

    For the panel: Forge I → ("gold",), Forge II → ("gold", "diamond").  An
    unbuilt forge unlocks nothing extra (the free tiers craft without it).
    """
    unlocked: list[str] = []
    for tier in equipment.TIER_ORDER:
        need = max(0, equipment.tier_index(tier) - FREE_TIER_CEILING)
        if 0 < need <= forge_level:
            unlocked.append(tier)
    return tuple(unlocked)


__all__ = [
    "FORGE",
    "STRUCTURES",
    "MAX_FORGE_LEVEL",
    "FREE_TIER_CEILING",
    "BuildCost",
    "is_structure",
    "forge_level_name",
    "forge_build_cost",
    "forge_level_required",
    "meets_forge_requirement",
    "tiers_unlocked_at",
]
