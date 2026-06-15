"""Titles — pure, table-driven earned-title model (brainstorm §7.6 identity).

The cheapest identity feature: earned, equippable text titles. Each title is
**derived** from existing progression — skill mastery (a branch at its cap),
depth milestones (the deepest biome reached), and game-level milestones — so
nothing new has to be *granted* on a mutation path: a player's earned set is a
pure function of state they already have (``TitleContext``). Only the player's
*equipped choice* is persisted (``mining_player_state.equipped_title``).

Pure + stdlib-only (no Discord / DB / state), like :mod:`utils.mining.skills` and
:mod:`utils.equipment`, so the catalogue and earn checks are trivially unit-tested
and shared across layers. Thresholds are the recommended v1 defaults — tunable;
pin changes in ``docs/planning/titles-numbers-2026-06-15.md`` + a test.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from utils.mining import skills

# Depth band indices (utils.mining.world): Surface 0 → Cavern 1 → Deep 2 →
# Magma core 3.  Milestone titles fire on reaching each biome (max_depth ≥ band).
# These are biome-*named* (not absolute "depth 50") on purpose: the brainstorm's
# P6 grid arc expands depth well beyond today's 4 bands, at which point new
# deeper-milestone titles are simply appended to _RULES — the ``max_depth >= N``
# check already extends, nothing here assumes 3 is the floor of the world.
_CAVERN, _DEEP, _MAGMA = 1, 2, 3

# Game-level milestones (the shared game-XP level — game_xp_service).
_VETERAN_LEVEL, _LEGEND_LEVEL = 10, 25


@dataclass(frozen=True)
class Title:
    """One earnable title: its id, display text, and how it's earned."""

    id: str
    label: str  # display name, e.g. "the Deep One"
    emoji: str
    requirement: str  # human description, shown locked in the panel


@dataclass(frozen=True)
class TitleContext:
    """The progression a title earn-check reads — all already-owned state."""

    skills: dict[str, int]  # branch -> allocated points
    max_depth: int  # deepest band ever reached
    level: int  # shared game-XP level


_Pred = Callable[[TitleContext], bool]


def _mastered(branch: str) -> _Pred:
    """Earned when *branch* is at the per-branch cap (full mastery)."""
    return lambda c: c.skills.get(branch, 0) >= skills.PER_BRANCH_CAP


def _reached(depth: int) -> _Pred:
    return lambda c: c.max_depth >= depth


def _levelled(level: int) -> _Pred:
    return lambda c: c.level >= level


# The catalogue: (Title, earn-predicate).  Order is the display order in the
# panel (mastery → depth → level).  Adding a title is a one-line append here.
_RULES: tuple[tuple[Title, _Pred], ...] = (
    (
        Title("the_deep", "the Deep One", "⛏️", "Master the Mining branch (10/10)"),
        _mastered(skills.MINING),
    ),
    (
        Title("ironclad", "the Ironclad", "⚔️", "Master the Combat branch (10/10)"),
        _mastered(skills.COMBAT),
    ),
    (
        Title("the_lucky", "the Lucky", "🍀", "Master the Fortune branch (10/10)"),
        _mastered(skills.FORTUNE),
    ),
    (
        Title(
            "master_smith",
            "Master Smith",
            "🛠️",
            "Master the Crafting branch (10/10)",
        ),
        _mastered(skills.CRAFTING),
    ),
    (
        Title("spelunker", "the Spelunker", "🪨", "Reach the Cavern"),
        _reached(_CAVERN),
    ),
    (
        Title("deepdelver", "the Deepdelver", "💎", "Reach the Deep"),
        _reached(_DEEP),
    ),
    (
        Title("coreborn", "the Coreborn", "🌋", "Reach the Magma core"),
        _reached(_MAGMA),
    ),
    (
        Title("veteran", "the Veteran", "🎖️", "Reach game level 10"),
        _levelled(_VETERAN_LEVEL),
    ),
    (
        Title("legend", "the Legend", "👑", "Reach game level 25"),
        _levelled(_LEGEND_LEVEL),
    ),
)

ALL_TITLES: tuple[Title, ...] = tuple(t for t, _ in _RULES)
_BY_ID: dict[str, Title] = {t.id: t for t in ALL_TITLES}
_PRED_BY_ID: dict[str, _Pred] = {t.id: p for t, p in _RULES}


def get_title(title_id: str | None) -> Title | None:
    """The :class:`Title` with this id, or None if it's not a real title."""
    if not title_id:
        return None
    return _BY_ID.get(title_id)


def is_earned(title_id: str, ctx: TitleContext) -> bool:
    """True if *title_id* is a real title and *ctx* satisfies its requirement."""
    pred = _PRED_BY_ID.get(title_id)
    return bool(pred and pred(ctx))


def earned_titles(ctx: TitleContext) -> tuple[Title, ...]:
    """Every title *ctx* currently qualifies for, in catalogue order."""
    return tuple(t for t in ALL_TITLES if _PRED_BY_ID[t.id](ctx))


def display(title: Title) -> str:
    """The one-line display form — ``"🪨 the Spelunker"``."""
    return f"{title.emoji} {title.label}"


__all__ = [
    "Title",
    "TitleContext",
    "ALL_TITLES",
    "get_title",
    "is_earned",
    "earned_titles",
    "display",
]
