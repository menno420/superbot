"""Pure skill-tree model — branch stats, caps, the specialization invariant."""

from __future__ import annotations

from utils.equipment import EffectiveStats
from utils.mining import skills


def test_branches_and_caps():
    assert skills.BRANCHES == ("mining", "combat", "fortune", "crafting")
    # The specialization crux: the soft total cap is strictly below filling
    # every branch, so a player can NEVER max all four.
    assert skills.SOFT_TOTAL_CAP < len(skills.BRANCHES) * skills.PER_BRANCH_CAP


def test_branch_stats_v1_mapping():
    assert skills.branch_stats("mining", 5) == EffectiveStats(mining_power=5)
    # combat: +1 damage every 2 points, +2 max_health per point.
    assert skills.branch_stats("combat", 5) == EffectiveStats(damage=2, max_health=10)
    # fortune: +1 luck per point, +1 loot_bonus every 2 points.
    assert skills.branch_stats("fortune", 5) == EffectiveStats(luck=5, loot_bonus=2)
    assert skills.branch_stats("crafting", 5) == EffectiveStats(loot_bonus=5)


def test_branch_stats_zero_and_unknown_contribute_nothing():
    assert skills.branch_stats("mining", 0) == EffectiveStats()
    assert skills.branch_stats("mining", -3) == EffectiveStats()
    assert skills.branch_stats("nonsense", 5) == EffectiveStats()


def test_skill_stats_sums_branches():
    alloc = {"mining": 3, "combat": 4}
    assert skills.skill_stats(alloc) == EffectiveStats(
        mining_power=3,
        damage=2,
        max_health=8,
    )


def test_skill_stats_empty_is_all_zero():
    assert skills.skill_stats({}) == EffectiveStats()


def test_total_spent_floors_negative():
    assert skills.total_spent({"mining": 3, "combat": 2}) == 5
    assert skills.total_spent({"mining": -1, "combat": 2}) == 2


def test_is_branch():
    assert skills.is_branch("mining")
    assert not skills.is_branch("digging")


def test_branch_labels_cover_every_branch():
    assert set(skills.BRANCH_LABELS) == set(skills.BRANCHES)
