"""Coverage policy for BTD6 data areas — single source of truth.

Lives in ``utils/`` (mirroring ``utils/btd6/freshness_render.py``) so that
``services/``, ``views/`` and ``cogs/btd6/`` can all consume the *same*
coverage copy without crossing layer boundaries. The goal is that a command
answer, a panel embed, and the AI's grounding all describe the same data
limitations in the same words.

Each area carries:

* ``supported`` — is the area modeled at all?
* ``completeness`` — ``"full"`` / ``"partial"`` / ``"none"``.
* ``limitation`` — terse machine-facing description (feeds AI grounding
  signal lines and operator output).
* ``user_label`` — concise, friendly copy for user-facing embeds/footers.
* ``staff_label`` — operator-facing copy (slightly more technical).

These limitations previously lived only in scattered code comments
(page-1-only leaderboards, boss = standard difficulty / teamSize 1, odyssey
= easy only, capabilities = camo/lead only, hero per-level stats incomplete,
economy unmodeled) and were never surfaced to users or the model.

Pure data + accessors; no I/O, no Discord, no services. Import the stable
``AREA_*`` constants rather than bare strings so call sites can't drift.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

Completeness = Literal["full", "partial", "none"]


@dataclass(frozen=True)
class CoverageArea:
    """Immutable coverage descriptor for a single BTD6 data area."""

    area: str
    supported: bool
    completeness: Completeness
    limitation: str
    user_label: str
    staff_label: str


# ---------------------------------------------------------------------------
# Stable area ids (import these — never the bare string literal)
# ---------------------------------------------------------------------------

AREA_LEADERBOARDS = "leaderboards"
AREA_BOSS = "boss"
AREA_ODYSSEY = "odyssey"
AREA_RACES = "races"
AREA_CAPABILITIES = "capabilities"
AREA_HERO_STATS = "hero_stats"
AREA_ECONOMY = "economy"


# ---------------------------------------------------------------------------
# Registry (single source of truth)
# ---------------------------------------------------------------------------

_COVERAGE: dict[str, CoverageArea] = {
    AREA_LEADERBOARDS: CoverageArea(
        area=AREA_LEADERBOARDS,
        supported=True,
        completeness="partial",
        limitation="top page only — lower ranks are not indexed",
        user_label="Leaderboard data covers the top page only — lower ranks aren't indexed.",
        staff_label="Leaderboards: first page only (no pagination); lower ranks not ingested.",
    ),
    AREA_BOSS: CoverageArea(
        area=AREA_BOSS,
        supported=True,
        completeness="partial",
        limitation="standard difficulty / teamSize 1 only",
        user_label="Boss data is standard difficulty, single-player (teamSize 1) only.",
        staff_label="Boss: standard difficulty + teamSize=1 only; elite/co-op not ingested.",
    ),
    AREA_ODYSSEY: CoverageArea(
        area=AREA_ODYSSEY,
        supported=True,
        completeness="partial",
        limitation="easy difficulty only",
        user_label="Odyssey data covers the easy difficulty only.",
        staff_label="Odyssey: easy difficulty only; medium/hard not ingested.",
    ),
    AREA_RACES: CoverageArea(
        area=AREA_RACES,
        supported=True,
        completeness="partial",
        limitation="top page only — lower placements are not indexed",
        user_label="Race data covers the top page only — lower placements aren't indexed.",
        staff_label="Races: first page only (no pagination); lower placements not ingested.",
    ),
    AREA_CAPABILITIES: CoverageArea(
        area=AREA_CAPABILITIES,
        supported=True,
        completeness="partial",
        limitation="camo detection and lead/black/white/purple popping only",
        user_label=(
            "Capability lookups cover camo detection and lead/black/white/purple "
            "popping; glass, frozen, and MOAB-class immunities aren't modeled."
        ),
        staff_label=(
            "Capabilities: camo + lead/black/white/purple popping; glass, frozen, "
            "and MOAB-class immunities not modeled."
        ),
    ),
    AREA_HERO_STATS: CoverageArea(
        area=AREA_HERO_STATS,
        supported=True,
        completeness="partial",
        limitation="per-level stats are incomplete",
        user_label="Hero per-level stats are incomplete — only some heroes/levels are modeled.",
        staff_label="Hero stats: per-level data incomplete; only a subset of heroes loaded.",
    ),
    AREA_ECONOMY: CoverageArea(
        area=AREA_ECONOMY,
        supported=False,
        completeness="none",
        limitation="not modeled",
        user_label="Economy/income data isn't modeled yet.",
        staff_label="Economy: no fixture, loader, or model — not ingested.",
    ),
}

# Read-only public view — callers must not mutate the registry.
COVERAGE: Mapping[str, CoverageArea] = MappingProxyType(_COVERAGE)


def get_coverage(area: str) -> CoverageArea:
    """Return the :class:`CoverageArea` for ``area``.

    Raises ``KeyError`` for an unknown area id — callers should pass one of
    the ``AREA_*`` constants, so a miss means a typo/drift worth failing on.
    """
    return COVERAGE[area]


__all__ = [
    "AREA_BOSS",
    "AREA_CAPABILITIES",
    "AREA_ECONOMY",
    "AREA_HERO_STATS",
    "AREA_LEADERBOARDS",
    "AREA_ODYSSEY",
    "AREA_RACES",
    "COVERAGE",
    "Completeness",
    "CoverageArea",
    "get_coverage",
]
