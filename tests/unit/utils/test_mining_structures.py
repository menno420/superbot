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
    assert structures.is_structure("home") is False
    assert structures.is_structure("") is False
