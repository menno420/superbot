"""character_stats — the gear + skills merge, and the additive safety property."""

from __future__ import annotations

from utils import equipment
from utils.equipment import EffectiveStats
from utils.mining.character import character_stats


def test_empty_allocation_is_byte_identical_to_gear_only():
    """The safety property: spending nothing changes nothing.

    With no skill allocation, character_stats must equal compute_stats exactly,
    so the skill tree ships without altering any existing player's stats.
    """
    equipped = {"tool": "diamond pickaxe", "light": "lantern"}
    assert character_stats(equipped, None) == equipment.compute_stats(equipped)
    assert character_stats(equipped, {}) == equipment.compute_stats(equipped)


def test_skills_stack_on_top_of_gear():
    equipped = {"tool": "pickaxe"}  # mining_power=2
    alloc = {"mining": 3}  # +3 mining_power
    assert character_stats(equipped, alloc) == EffectiveStats(mining_power=5)


def test_no_gear_no_skills_is_zero():
    assert character_stats({}, {}) == EffectiveStats()
