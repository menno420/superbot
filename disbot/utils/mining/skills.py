"""Skill tree — pure, table-driven skill→stats model (brainstorm §7.4).

Four branches, each capped, mapping allocated points onto the shared
:class:`~utils.equipment.EffectiveStats` block so skills stack with gear through
one read model (``utils.mining.character.character_stats``).  A **soft total
cap** below ``len(BRANCHES) × PER_BRANCH_CAP`` is the design crux: you cannot max
every branch, so play forces a specialization (digger / duelist / tycoon /
smith), which is what lights up solo / PvP / leaderboards / co-op (§7.3).

Pure + stdlib-only (no Discord / DB / state), like :mod:`utils.equipment`, so the
mapping is trivially unit-testable and shared across layers.  The numbers here
are the recommended v1 defaults from the plan — tunable; pin changes in a
``docs/planning/*-numbers-*.md`` record + a test.
"""

from __future__ import annotations

from utils.equipment import EffectiveStats

# The four skill branches.  Branch names are the stored ``player_skills.branch``
# vocabulary and the UI/command tokens.
MINING = "mining"
COMBAT = "combat"
FORTUNE = "fortune"
CRAFTING = "crafting"
BRANCHES: tuple[str, ...] = (MINING, COMBAT, FORTUNE, CRAFTING)

# Per-branch cap and the soft total cap.  20 < 4 × 10 = 40 ⇒ a fully-levelled
# player can fill at most two branches (or spread thinner) — never all four.
PER_BRANCH_CAP = 10
SOFT_TOTAL_CAP = 20

# Human-readable branch blurbs (panel copy; pure, no Discord).
BRANCH_LABELS: dict[str, str] = {
    MINING: "⛏️ Mining — raw digging power",
    COMBAT: "⚔️ Combat — duel damage & health",
    FORTUNE: "🍀 Fortune — luck & loot",
    CRAFTING: "🛠️ Crafting — loot yield",
}


def is_branch(branch: str) -> bool:
    """True if *branch* is a real skill branch."""
    return branch in BRANCHES


def branch_stats(branch: str, points: int) -> EffectiveStats:
    """The :class:`EffectiveStats` contribution of *points* in one *branch*.

    Recommended v1 mapping (1 point each, kept deliberately simple):
    - mining → ``mining_power`` +1 per point
    - combat → ``damage`` +1 every 2 points, ``max_health`` +2 per point
    - fortune → ``luck`` +1 per point, ``loot_bonus`` +1 every 2 points
    - crafting → ``loot_bonus`` +1 per point

    Unknown branches and non-positive points contribute nothing.
    """
    if points <= 0 or branch not in BRANCHES:
        return EffectiveStats()
    if branch == MINING:
        return EffectiveStats(mining_power=points)
    if branch == COMBAT:
        return EffectiveStats(damage=points // 2, max_health=points * 2)
    if branch == FORTUNE:
        return EffectiveStats(luck=points, loot_bonus=points // 2)
    # CRAFTING
    return EffectiveStats(loot_bonus=points)


def skill_stats(alloc: dict[str, int]) -> EffectiveStats:
    """Sum the stat contribution of every allocated branch in *alloc*.

    *alloc* is ``{branch: points}``.  An empty allocation yields all-zero stats
    (the additive safety property — skills change nothing until a point is
    spent).
    """
    total = EffectiveStats()
    for branch, points in alloc.items():
        total = total + branch_stats(branch, points)
    return total


def total_spent(alloc: dict[str, int]) -> int:
    """Total points allocated across all branches in *alloc*."""
    return sum(max(0, p) for p in alloc.values())


__all__ = [
    "MINING",
    "COMBAT",
    "FORTUNE",
    "CRAFTING",
    "BRANCHES",
    "PER_BRANCH_CAP",
    "SOFT_TOTAL_CAP",
    "BRANCH_LABELS",
    "is_branch",
    "branch_stats",
    "skill_stats",
    "total_spent",
]
