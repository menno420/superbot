"""Pure tests for utils/mining/structures.py — the Forge build/gating math (Slice B).

Pins the numbers recorded in docs/planning/forge-numbers-2026-06-15.md and the
additive safety property: every non-gold/diamond recipe requires forge level 0.
"""

from __future__ import annotations

import pytest

from utils import equipment
from utils.mining import structures

# --------------------------------------------------------------------------- #
# The gate — derived from the gear tier ladder (additive: only gold/diamond gate)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("recipe", "expected"),
    [
        # Free tiers (bronze/iron/silver gear) — no forge.
        ("bronze helmet", 0),
        ("iron chestplate", 0),
        ("silver sword", 0),
        ("silver shield", 0),
        # Top tiers gate.
        ("gold helmet", 1),
        ("gold sword", 1),
        ("diamond chestplate", 2),
        ("diamond shield", 2),
        # Tools / starters / structures — never gate (gear_tier is None).
        ("pickaxe", 0),
        ("diamond pickaxe", 0),  # a tool, not set-gear → free
        ("diamond lantern", 0),
        ("sword", 0),
        ("stone hut", 0),
        ("giant fortress", 0),
        ("not a real item", 0),
    ],
)
def test_forge_level_required(recipe: str, expected: int) -> None:
    assert structures.forge_level_required(recipe) == expected


def test_no_existing_recipe_needs_above_max_forge() -> None:
    """Every shipped recipe is craftable within the forge ladder (no dead recipe)."""
    from utils.mining.recipes import DEFAULT_RECIPES

    for name in DEFAULT_RECIPES:
        assert structures.forge_level_required(name) <= structures.MAX_FORGE_LEVEL


def test_only_gold_and_diamond_gear_gate() -> None:
    """The additive property: nothing below gold tier ever needs a forge."""
    for name in equipment.gear_names():
        tier = equipment.gear_tier(name)
        required = structures.forge_level_required(name)
        if tier in (None, "bronze", "iron", "silver"):
            assert required == 0, name
        else:
            assert required >= 1, name


def test_meets_forge_requirement() -> None:
    assert structures.meets_forge_requirement("silver sword", 0) is True
    assert structures.meets_forge_requirement("gold sword", 0) is False
    assert structures.meets_forge_requirement("gold sword", 1) is True
    assert structures.meets_forge_requirement("diamond sword", 1) is False
    assert structures.meets_forge_requirement("diamond sword", 2) is True


# --------------------------------------------------------------------------- #
# The build ladder
# --------------------------------------------------------------------------- #


def test_forge_build_cost_ladder() -> None:
    c0 = structures.forge_build_cost(0)
    assert c0 is not None
    assert c0.coins == 3_000
    assert c0.materials == {"iron": 25, "stone": 15}
    c1 = structures.forge_build_cost(1)
    assert c1 is not None
    assert c1.coins == 8_000
    assert c1.materials == {"gold": 20, "iron": 10}
    # Rising sink.
    assert c1.coins > c0.coins


def test_forge_build_cost_maxed_returns_none() -> None:
    assert structures.forge_build_cost(structures.MAX_FORGE_LEVEL) is None
    assert structures.forge_build_cost(structures.MAX_FORGE_LEVEL + 1) is None
    assert structures.forge_build_cost(-1) is None


def test_tiers_unlocked_at() -> None:
    assert structures.tiers_unlocked_at(0) == ()
    assert structures.tiers_unlocked_at(1) == ("gold",)
    assert structures.tiers_unlocked_at(2) == ("gold", "diamond")


def test_forge_level_name() -> None:
    assert structures.forge_level_name(0) == "(not built)"
    assert structures.forge_level_name(1) == "Forge I"
    assert structures.forge_level_name(2) == "Forge II"
    # Clamped.
    assert structures.forge_level_name(99) == "Forge II"


def test_is_structure() -> None:
    assert structures.is_structure("forge") is True
    assert structures.is_structure("  Forge ") is True
    assert structures.is_structure("home") is True  # Slice C added Home
    assert structures.is_structure("  Home ") is True
    assert structures.is_structure("tide_pool") is True  # 2026-07-01 Tide Pool
    assert structures.is_structure("  Tide_Pool ") is True
    assert structures.is_structure("dock") is True  # 2026-07-01 Dock
    assert structures.is_structure("  Dock ") is True
    assert structures.is_structure("castle") is False
    assert structures.is_structure("") is False


# --------------------------------------------------------------------------- #
# Generic per-structure registry (forge helpers delegate to this) — Slice C
# --------------------------------------------------------------------------- #


def test_forge_helpers_match_generic_registry() -> None:
    """The forge-specific wrappers stay byte-identical to the generic lookups."""
    assert structures.max_level(structures.FORGE) == structures.MAX_FORGE_LEVEL
    assert structures.display_name(structures.FORGE) == "Forge"
    for level in range(-1, structures.MAX_FORGE_LEVEL + 2):
        assert structures.forge_build_cost(level) == structures.build_cost(
            structures.FORGE,
            level,
        )
        assert structures.forge_level_name(level) == structures.level_name(
            structures.FORGE,
            level,
        )


# --------------------------------------------------------------------------- #
# Home structure (Slice C) — a cosmetic coin/material sink, never a gate
# --------------------------------------------------------------------------- #


def test_home_registered_and_named() -> None:
    assert structures.HOME in structures.STRUCTURES
    assert structures.display_name(structures.HOME) == "Home"
    assert structures.max_level(structures.HOME) == structures.MAX_HOME_LEVEL == 3


def test_home_level_names() -> None:
    assert structures.level_name(structures.HOME, 0) == "(not built)"
    assert structures.level_name(structures.HOME, 1) == "Cozy Cabin"
    assert structures.level_name(structures.HOME, 2) == "Stone Keep"
    assert structures.level_name(structures.HOME, 3) == "Grand Hall"
    # Clamped above the ladder.
    assert structures.level_name(structures.HOME, 99) == "Grand Hall"


def test_home_build_cost_ladder_is_a_rising_sink() -> None:
    costs = [structures.build_cost(structures.HOME, lvl) for lvl in range(3)]
    assert [c.coins for c in costs] == [2_000, 5_000, 12_000]
    assert costs[0].materials == {"wood": 30, "stone": 20}
    assert costs[2].materials == {"gold": 15, "diamond": 3}
    # Strictly rising coin sink.
    assert costs[0].coins < costs[1].coins < costs[2].coins


def test_home_build_cost_maxed_returns_none() -> None:
    assert structures.build_cost(structures.HOME, structures.MAX_HOME_LEVEL) is None
    assert structures.build_cost(structures.HOME, -1) is None


def test_home_does_not_gate_crafting() -> None:
    """Home is cosmetic — it never appears in the gear-craft forge gate."""
    # forge_level_required only ever consults the gear ladder, never Home.
    assert structures.forge_level_required("home") == 0


# --------------------------------------------------------------------------- #
# Tide Pool (2026-07-01) — coral's functional sink; the fishing cast's 5th knob.
# Numbers pinned to docs/planning/fishing-tide-pool-numbers-2026-07-01.md.
# --------------------------------------------------------------------------- #


def test_tide_pool_registered_and_named() -> None:
    assert structures.TIDE_POOL in structures.STRUCTURES
    assert structures.display_name(structures.TIDE_POOL) == "Tide Pool"
    assert (
        structures.max_level(structures.TIDE_POOL)
        == structures.MAX_TIDE_POOL_LEVEL
        == 3
    )


def test_tide_pool_level_names() -> None:
    assert structures.level_name(structures.TIDE_POOL, 0) == "(not built)"
    assert structures.level_name(structures.TIDE_POOL, 1) == "Reef Pool"
    assert structures.level_name(structures.TIDE_POOL, 2) == "Tidal Basin"
    assert structures.level_name(structures.TIDE_POOL, 3) == "Grand Reef"
    # Clamped above the ladder.
    assert structures.level_name(structures.TIDE_POOL, 99) == "Grand Reef"


def test_tide_pool_build_cost_ladder_is_a_rising_coral_sink() -> None:
    costs = [structures.build_cost(structures.TIDE_POOL, lvl) for lvl in range(3)]
    assert [c.coins for c in costs] == [1_500, 4_000, 9_000]
    assert [c.materials["coral"] for c in costs] == [3, 6, 10]
    # Strictly rising coin + coral sink.
    assert costs[0].coins < costs[1].coins < costs[2].coins
    assert (
        costs[0].materials["coral"]
        < costs[1].materials["coral"]
        < costs[2].materials["coral"]
    )


def test_tide_pool_build_cost_maxed_returns_none() -> None:
    assert (
        structures.build_cost(structures.TIDE_POOL, structures.MAX_TIDE_POOL_LEVEL)
        is None
    )
    assert structures.build_cost(structures.TIDE_POOL, -1) is None


def test_tide_pool_pull_mult_ladder_and_additive_safety() -> None:
    # Unbuilt ⇒ exactly 1.0 (byte-identical cast — the additive-safety property).
    assert structures.tide_pool_pull_mult(0) == 1.0
    assert structures.tide_pool_pull_mult(1) == 1.04
    assert structures.tide_pool_pull_mult(2) == 1.08
    assert structures.tide_pool_pull_mult(3) == 1.12
    # Clamped: an out-of-range level can never over-reward.
    assert structures.tide_pool_pull_mult(99) == 1.12
    assert structures.tide_pool_pull_mult(-5) == 1.0
    # Strictly rising bonus across the ladder.
    mults = [structures.tide_pool_pull_mult(lvl) for lvl in range(4)]
    assert mults == sorted(mults)
    assert mults[0] < mults[-1]


def test_tide_pool_does_not_gate_crafting() -> None:
    """The Tide Pool is a fishing bonus — never a gear-craft forge gate."""
    assert structures.forge_level_required("tide_pool") == 0


# --------------------------------------------------------------------------- #
# Dock (2026-07-01) — the Tide Pool's bite-speed sibling; the entry coral sink.
# Numbers pinned to docs/planning/fishing-dock-numbers-2026-07-01.md.
# --------------------------------------------------------------------------- #


def test_dock_registered_and_named() -> None:
    assert structures.DOCK in structures.STRUCTURES
    assert structures.display_name(structures.DOCK) == "Dock"
    assert structures.max_level(structures.DOCK) == structures.MAX_DOCK_LEVEL == 2


def test_dock_level_names() -> None:
    assert structures.level_name(structures.DOCK, 0) == "(not built)"
    assert structures.level_name(structures.DOCK, 1) == "Fishing Dock"
    assert structures.level_name(structures.DOCK, 2) == "Deepwater Pier"
    # Clamped above the ladder.
    assert structures.level_name(structures.DOCK, 99) == "Deepwater Pier"


def test_dock_build_cost_ladder_is_a_rising_coral_and_wood_sink() -> None:
    costs = [structures.build_cost(structures.DOCK, lvl) for lvl in range(2)]
    assert [c.coins for c in costs] == [1_200, 3_500]
    assert [c.materials["coral"] for c in costs] == [2, 5]
    assert [c.materials["wood"] for c in costs] == [15, 30]
    # Strictly rising coin + material sink.
    assert costs[0].coins < costs[1].coins
    assert costs[0].materials["coral"] < costs[1].materials["coral"]


def test_dock_build_cost_maxed_returns_none() -> None:
    assert structures.build_cost(structures.DOCK, structures.MAX_DOCK_LEVEL) is None
    assert structures.build_cost(structures.DOCK, -1) is None


def test_dock_bite_speed_mult_ladder_and_additive_safety() -> None:
    # Unbuilt ⇒ exactly 1.0 (byte-identical cast — the additive-safety property).
    assert structures.dock_bite_speed_mult(0) == 1.0
    assert structures.dock_bite_speed_mult(1) == 0.94
    assert structures.dock_bite_speed_mult(2) == 0.88
    # Clamped: an out-of-range level can never over-reward (nor go negative).
    assert structures.dock_bite_speed_mult(99) == 0.88
    assert structures.dock_bite_speed_mult(-5) == 1.0
    # Strictly falling (faster) across the ladder, always positive.
    mults = [structures.dock_bite_speed_mult(lvl) for lvl in range(3)]
    assert mults == sorted(mults, reverse=True)
    assert mults[-1] > 0


def test_dock_is_cheaper_on_coral_than_the_tide_pool() -> None:
    """The Dock is the *entry* coral structure — a smaller total-coral commitment
    than the full Tide Pool, so a player can afford faster fishing before rarer.
    """
    dock_coral = sum(
        structures.build_cost(structures.DOCK, lvl).materials["coral"]
        for lvl in range(structures.MAX_DOCK_LEVEL)
    )
    pool_coral = sum(
        structures.build_cost(structures.TIDE_POOL, lvl).materials["coral"]
        for lvl in range(structures.MAX_TIDE_POOL_LEVEL)
    )
    assert dock_coral < pool_coral


def test_dock_does_not_gate_crafting() -> None:
    """The Dock is a fishing bonus — never a gear-craft forge gate."""
    assert structures.forge_level_required("dock") == 0


def test_boathouse_registered_and_named() -> None:
    assert structures.BOATHOUSE in structures.STRUCTURES
    assert structures.display_name(structures.BOATHOUSE) == "Boathouse"
    assert (
        structures.max_level(structures.BOATHOUSE)
        == structures.MAX_BOATHOUSE_LEVEL
        == 2
    )


def test_boathouse_level_names() -> None:
    assert structures.level_name(structures.BOATHOUSE, 0) == "(not built)"
    assert structures.level_name(structures.BOATHOUSE, 1) == "Boathouse"
    assert structures.level_name(structures.BOATHOUSE, 2) == "Grand Boathouse"
    # Clamped past the top.
    assert structures.level_name(structures.BOATHOUSE, 99) == "Grand Boathouse"


def test_boathouse_build_cost_ladder_is_a_rising_coral_and_wood_sink() -> None:
    costs = [structures.build_cost(structures.BOATHOUSE, lvl) for lvl in range(2)]
    assert [c.coins for c in costs] == [2_000, 5_000]
    assert [c.materials["coral"] for c in costs] == [3, 6]
    assert [c.materials["wood"] for c in costs] == [20, 40]
    # Strictly rising coin + material sink.
    assert costs[0].coins < costs[1].coins
    assert costs[0].materials["coral"] < costs[1].materials["coral"]


def test_boathouse_build_cost_maxed_returns_none() -> None:
    assert (
        structures.build_cost(structures.BOATHOUSE, structures.MAX_BOATHOUSE_LEVEL)
        is None
    )


def test_boathouse_regen_mult_ladder_and_additive_safety() -> None:
    # Unbuilt ⇒ exactly 1.0 (byte-identical energy — the additive-safety property).
    assert structures.boathouse_regen_mult(0) == 1.0
    assert structures.boathouse_regen_mult(1) == 0.88
    assert structures.boathouse_regen_mult(2) == 0.76
    # Clamped: an out-of-range level can never over-reward (nor go non-positive).
    assert structures.boathouse_regen_mult(99) == 0.76
    assert structures.boathouse_regen_mult(-5) == 1.0
    # Strictly falling (faster) across the ladder, always positive.
    mults = [structures.boathouse_regen_mult(lvl) for lvl in range(3)]
    assert mults == sorted(mults, reverse=True)
    assert mults[-1] > 0


def test_boathouse_coral_cost_sits_between_the_dock_and_the_tide_pool() -> None:
    """The Boathouse is the middle coral sink — dearer than the Dock, cheaper than the pool."""
    dock_coral = sum(
        structures.build_cost(structures.DOCK, lvl).materials["coral"]
        for lvl in range(structures.MAX_DOCK_LEVEL)
    )
    boathouse_coral = sum(
        structures.build_cost(structures.BOATHOUSE, lvl).materials["coral"]
        for lvl in range(structures.MAX_BOATHOUSE_LEVEL)
    )
    pool_coral = sum(
        structures.build_cost(structures.TIDE_POOL, lvl).materials["coral"]
        for lvl in range(structures.MAX_TIDE_POOL_LEVEL)
    )
    assert dock_coral < boathouse_coral < pool_coral


def test_boathouse_does_not_gate_crafting() -> None:
    """The Boathouse is a fishing bonus — never a gear-craft forge gate."""
    assert structures.forge_level_required("boathouse") == 0


# --------------------------------------------------------------------------- #
# The Fishery — the FOURTH coral structure (yield/abundance: double-catch chance).
# Pinned in docs/planning/fishing-fishery-numbers-2026-07-01.md.
# --------------------------------------------------------------------------- #


def test_fishery_registered_and_named() -> None:
    assert structures.FISHERY in structures.STRUCTURES
    assert structures.display_name(structures.FISHERY) == "Fishery"
    assert (
        structures.max_level(structures.FISHERY)
        == structures.MAX_FISHERY_LEVEL
        == 2
    )


def test_fishery_level_names() -> None:
    assert structures.level_name(structures.FISHERY, 0) == "(not built)"
    assert structures.level_name(structures.FISHERY, 1) == "Fishery"
    assert structures.level_name(structures.FISHERY, 2) == "Grand Fishery"
    # Clamped past the top.
    assert structures.level_name(structures.FISHERY, 99) == "Grand Fishery"


def test_fishery_build_cost_ladder_is_a_rising_coral_and_wood_sink() -> None:
    costs = [structures.build_cost(structures.FISHERY, lvl) for lvl in range(2)]
    assert [c.coins for c in costs] == [2_500, 6_000]
    assert [c.materials["coral"] for c in costs] == [4, 8]
    assert [c.materials["wood"] for c in costs] == [25, 45]
    # Strictly rising coin + material sink.
    assert costs[0].coins < costs[1].coins
    assert costs[0].materials["coral"] < costs[1].materials["coral"]


def test_fishery_build_cost_maxed_returns_none() -> None:
    assert (
        structures.build_cost(structures.FISHERY, structures.MAX_FISHERY_LEVEL)
        is None
    )


def test_fishery_bonus_chance_ladder_and_additive_safety() -> None:
    # Unbuilt ⇒ exactly +0.0 (byte-identical catch economics — additive-safety).
    assert structures.fishery_bonus_chance(0) == 0.0
    assert structures.fishery_bonus_chance(1) == 0.05
    assert structures.fishery_bonus_chance(2) == 0.10
    # Clamped: an out-of-range level can never over-reward (nor go negative).
    assert structures.fishery_bonus_chance(99) == 0.10
    assert structures.fishery_bonus_chance(-5) == 0.0
    # Strictly rising across the ladder, always non-negative.
    bonuses = [structures.fishery_bonus_chance(lvl) for lvl in range(3)]
    assert bonuses == sorted(bonuses)
    assert bonuses[0] == 0.0


def test_fishery_is_the_dearest_coral_and_wood_structure() -> None:
    """The Fishery's yield payoff compounds every catch — dearest of the coral+wood set."""
    def coral_total(structure: str, max_level: int) -> int:
        return sum(
            structures.build_cost(structure, lvl).materials["coral"]
            for lvl in range(max_level)
        )

    fishery_coral = coral_total(structures.FISHERY, structures.MAX_FISHERY_LEVEL)
    boathouse_coral = coral_total(structures.BOATHOUSE, structures.MAX_BOATHOUSE_LEVEL)
    dock_coral = coral_total(structures.DOCK, structures.MAX_DOCK_LEVEL)
    # Dearest of the three coral+wood structures (Dock < Boathouse < Fishery); the
    # coral-only Tide Pool is dearer on coral alone (no wood leg) — a separate sink.
    assert dock_coral < boathouse_coral < fishery_coral


def test_fishery_does_not_gate_crafting() -> None:
    """The Fishery is a fishing bonus — never a gear-craft forge gate."""
    assert structures.forge_level_required("fishery") == 0


def test_every_registered_structure_resolves_a_build_reason() -> None:
    """BUG-0031 regression: build_structure derives the audit reason generically, so
    a *newly-registered* structure can never crash the build path for want of a
    hand-maintained map entry (the boathouse KeyError that shipped in #1605)."""
    from utils.mining import market

    for structure in structures.STRUCTURES:
        reason = market.structure_build_reason(structure)
        assert reason == f"mining:{structure}_build"
        assert reason  # non-empty for every registered structure
