"""Seed-deterministic procedural mine grid — pure (grid Mine, hub-redesign PR 3).

The *spatial* half of the mining world.  Where :mod:`utils.mining.world` owns the
vertical depth↔biome mapping (``z``), this module owns the LATERAL grid (``x``,
``y``) at a given depth and the deterministic content of every cell.

Owner design (Q-0173, 2026-06-17/19 — ``docs/planning/mining-hub-redesign-2026-06-15.md``):

* **Seed-deterministic procedural** — a cell's content is a pure function of the
  world *seed* and its ``(x, y, z)`` coordinates, so ``seed 12345`` gives everyone
  the same world (deterministic · shareable · effectively infinite).  We generate
  it ourselves; this is NOT literal Minecraft terrain.
* **One shared grid per seed** — the seed is per-guild (see
  ``utils/db/games/mining_grid``), so every player in a guild roams the same world.
* **The vertical axis = the existing depth bands** — ``z`` is the depth-band index
  (:mod:`utils.mining.world`); "deeper = richer" carries over via
  :func:`utils.mining.rewards.ore_weights_for_depth`.  Horizontal (N/S/E/W) is
  lateral variety within a band; each cell's exact yield stays seed-determined.
* **v1 = free movement, NO encounters** — this module models cell *content*
  (a richness multiplier + a featured ore), never an encounter / combat system.

Pure: stdlib only, no Discord, no DB, no global RNG — every cell is reproducible
from ``(seed, x, y, z)``, so it is trivially unit-testable.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum

from utils.mining.rewards import ore_weights_for_depth

# Compass + vertical movement tokens.  N/S/E/W move laterally within a depth
# band; UP/DOWN change the band — the caller routes those through the light-gated
# :mod:`utils.mining.world` descend/ascend, so :func:`step` only handles lateral.
NORTH = "north"
SOUTH = "south"
EAST = "east"
WEST = "west"
UP = "up"
DOWN = "down"

LATERAL: frozenset[str] = frozenset({NORTH, SOUTH, EAST, WEST})
VERTICAL: frozenset[str] = frozenset({UP, DOWN})
DIRECTIONS: frozenset[str] = LATERAL | VERTICAL

# (dx, dy) per lateral step.  North = +y (renders at the top of the map),
# East = +x.
_STEP: dict[str, tuple[int, int]] = {
    NORTH: (0, 1),
    SOUTH: (0, -1),
    EAST: (1, 0),
    WEST: (-1, 0),
}

_MOVE_PHRASE: dict[str, str] = {
    NORTH: "north",
    SOUTH: "south",
    EAST: "east",
    WEST: "west",
    UP: "upward",
    DOWN: "deeper",
}


def step(x: int, y: int, direction: str) -> tuple[int, int]:
    """New ``(x, y)`` after one lateral step; unchanged for a non-lateral token."""
    dx, dy = _STEP.get(direction, (0, 0))
    return x + dx, y + dy


def move_phrase(direction: str) -> str:
    """Human phrase for *direction* (e.g. ``"north"`` / ``"deeper"``)."""
    return _MOVE_PHRASE.get(direction, direction)


class CellFeature(Enum):
    """What a cell holds.  Deterministic from the seed — never an encounter."""

    NORMAL = "normal"
    RICH = "rich"
    BARREN = "barren"
    TREASURE = "treasure"


# Selection weights for a cell's feature (most cells are unremarkable).
# Rebalanced 2026-06-22 (60/20/15/5 → 70/10/18/2) so a "lucky strike" fires on
# ~12% of cells, not 25% — rewards stay special, not constant. Sim-pinned:
# docs/planning/mining-economy-balance-2026-06-22.md.
_FEATURE_WEIGHTS: tuple[tuple[CellFeature, float], ...] = (
    (CellFeature.NORMAL, 70.0),
    (CellFeature.RICH, 10.0),
    (CellFeature.BARREN, 18.0),
    (CellFeature.TREASURE, 2.0),
)

# Yield multiplier each feature applies to a mined amount. Treasure trimmed
# ×3 → ×2 in the same 2026-06-22 rebalance (cap the lucky-strike spike).
_RICHNESS: dict[CellFeature, float] = {
    CellFeature.NORMAL: 1.0,
    CellFeature.RICH: 2.0,
    CellFeature.BARREN: 0.5,
    CellFeature.TREASURE: 2.0,
}

# Flavour for a lucky strike (rich / treasure cells), formatted with the ore.
_STRIKE_NOTE: dict[CellFeature, str] = {
    CellFeature.RICH: "💎 You struck a rich {ore} vein!",
    CellFeature.TREASURE: "🤑 A treasure pocket, packed with {ore}!",
}

# 64-bit mask for the stable coordinate hash (Python ints are unbounded).
_MASK = (1 << 64) - 1


def _cell_seed(seed: int, x: int, y: int, z: int) -> int:
    """A stable 64-bit hash of ``(seed, x, y, z)`` — deterministic across processes.

    Built from integer arithmetic only (a splitmix64-style mix), so it never
    depends on Python's per-process string-hash randomization; negative
    coordinates wrap deterministically under the mask.
    """
    h = seed & _MASK
    for value in (x, y, z):
        h = (h ^ (value & _MASK)) & _MASK
        h = (h + 0x9E3779B97F4A7C15 + ((h << 6) & _MASK) + (h >> 2)) & _MASK
    return h


@dataclass(frozen=True)
class Cell:
    """The deterministic content of one grid cell."""

    x: int
    y: int
    z: int
    feature: CellFeature
    featured_resource: str
    richness: float


def cell_at(seed: int, x: int, y: int, z: int) -> Cell:
    """The cell at ``(x, y, z)`` in world *seed* — a pure function of its inputs.

    The featured ore is drawn from the depth-weighted ore table
    (:func:`utils.mining.rewards.ore_weights_for_depth`), so a rich vein deep
    down is far likelier to be gold/diamond than one near the surface — "deeper =
    richer" with no separate balance table.
    """
    rng = random.Random(_cell_seed(seed, x, y, z))
    features = [f for f, _ in _FEATURE_WEIGHTS]
    feature = rng.choices(features, weights=[w for _, w in _FEATURE_WEIGHTS], k=1)[0]
    weights = ore_weights_for_depth(z)
    ores = list(weights)
    featured = rng.choices(ores, weights=[weights[o] for o in ores], k=1)[0]
    return Cell(x, y, z, feature, featured, _RICHNESS[feature])


def apply_cell_to_loot(
    cell: Cell,
    found: str,
    amount: int,
) -> tuple[str, int, str | None]:
    """Fold a cell's content into a base mine roll → ``(item, amount, flavour)``.

    Richness scales the amount (a rich vein yields more, a barren one less but
    never nothing); a rich / treasure cell's mined ore becomes its *featured*
    resource (the lucky strike).  The flavour note is short UI copy, or ``None``
    for an unremarkable (NORMAL) cell.
    """
    scaled = max(1, round(amount * cell.richness))
    if cell.feature in (CellFeature.RICH, CellFeature.TREASURE):
        note = _STRIKE_NOTE[cell.feature].format(ore=cell.featured_resource)
        return cell.featured_resource, scaled, note
    if cell.feature is CellFeature.BARREN:
        return found, scaled, "The rock here is barren — slim pickings."
    return found, scaled, None


# ---------------------------------------------------------------------------
# Rendering (pure text — the caller wraps the map body in a code block).
# ---------------------------------------------------------------------------

PLAYER_GLYPH = "@"
FOG_GLYPH = "?"
_FEATURE_GLYPH: dict[CellFeature, str] = {
    CellFeature.NORMAL: ".",
    CellFeature.RICH: "*",
    CellFeature.BARREN: "-",
    CellFeature.TREASURE: "$",
}
MAP_LEGEND = "@ you · . rock · * rich · - barren · $ treasure · ? unexplored"

_FEATURE_LABEL: dict[CellFeature, str] = {
    CellFeature.NORMAL: "ordinary rock",
    CellFeature.RICH: "a rich vein",
    CellFeature.BARREN: "barren rock",
    CellFeature.TREASURE: "a treasure pocket",
}


def render_local_map(
    seed: int,
    cx: int,
    cy: int,
    z: int,
    discovered: set[tuple[int, int]],
    *,
    radius: int = 2,
) -> str:
    """A square fog-of-war map window centred on the player (pure text).

    Cells the player has visited (in *discovered*) show their feature glyph;
    unvisited cells are fog (``?``); the player's own cell is always ``@``.
    North (higher ``y``) renders at the top.  Returns the grid body only.
    """
    lines: list[str] = []
    for y in range(cy + radius, cy - radius - 1, -1):
        row: list[str] = []
        for x in range(cx - radius, cx + radius + 1):
            if x == cx and y == cy:
                row.append(PLAYER_GLYPH)
            elif (x, y) in discovered:
                row.append(_FEATURE_GLYPH[cell_at(seed, x, y, z).feature])
            else:
                row.append(FOG_GLYPH)
        lines.append(" ".join(row))
    return "\n".join(lines)


def describe_cell(cell: Cell) -> str:
    """One-line description of what the player is standing on."""
    label = _FEATURE_LABEL[cell.feature]
    if cell.feature is CellFeature.NORMAL:
        return f"You're standing on {label}."
    return f"You're standing on {label} ({cell.featured_resource})."


__all__ = [
    "NORTH",
    "SOUTH",
    "EAST",
    "WEST",
    "UP",
    "DOWN",
    "LATERAL",
    "VERTICAL",
    "DIRECTIONS",
    "step",
    "move_phrase",
    "CellFeature",
    "Cell",
    "cell_at",
    "apply_cell_to_loot",
    "render_local_map",
    "describe_cell",
    "PLAYER_GLYPH",
    "FOG_GLYPH",
    "MAP_LEGEND",
]
