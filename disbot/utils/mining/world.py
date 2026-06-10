"""World / position — pure depth↔biome + descent-gating model (foundation).

The *position* half of the mining "Descent".  A player has a persistent integer
**depth** (stored in ``mining_player_state``); this module maps that depth onto a
:class:`~utils.mining.exploration.Biome` and decides — from the player's equipped
gear :class:`~utils.equipment.EffectiveStats` — how deep they may descend.

Pure: no Discord, no DB, no state.  Sibling to ``exploration.py`` (which owns the
outcome *catalog*) and ``equipment.py`` (which owns the stat block); it reuses
``exploration.BIOME_ORDER`` so the depth↔biome mapping has a single source of
truth.

**Descent-gating decision (brainstorm §6.8 P2).** Depth access is gated by the
already-shipped ``depth_access`` stat from equipped gear — a torch grants access
to depth 1 (Cavern), a lantern depth 2 (Deep) — and is **persistent, not consumed
per descent**.  Consuming a light per descent belongs with the later durability
slice; this keeps position a stable, reversible game constant (one function,
:func:`max_accessible_depth`).
"""

from __future__ import annotations

from utils.equipment import EffectiveStats
from utils.mining.exploration import BIOME_ORDER, Biome

# Deepest reachable band index (MAGMA).  Position is clamped to [0, MAX_DEPTH].
MAX_DEPTH: int = len(BIOME_ORDER) - 1

# Display labels / icons, keyed by Biome — used by the cog + hub embeds.
BIOME_LABELS: dict[Biome, str] = {
    Biome.SURFACE: "Surface",
    Biome.CAVERN: "Cavern",
    Biome.DEEP: "the Deep",
    Biome.MAGMA: "the Magma core",
}

BIOME_EMOJI: dict[Biome, str] = {
    Biome.SURFACE: "🌳",
    Biome.CAVERN: "🪨",
    Biome.DEEP: "💎",
    Biome.MAGMA: "🌋",
}


def clamp_depth(depth: int) -> int:
    """Constrain *depth* to the valid ``[0, MAX_DEPTH]`` band range."""
    return max(0, min(depth, MAX_DEPTH))


def biome_for_depth(depth: int) -> Biome:
    """The :class:`Biome` a player at *depth* is currently in."""
    return BIOME_ORDER[clamp_depth(depth)]


def max_accessible_depth(stats: EffectiveStats) -> int:
    """The deepest band *stats* (from equipped gear) unlocks.

    Surface (0) is always reachable; each point of light-driven ``depth_access``
    unlocks one deeper band (torch → 1/Cavern, lantern → 2/Deep).  Clamped to the
    world's deepest band, so unbuilt-yet headroom (Magma) stays unreachable until
    a deeper light exists.
    """
    return clamp_depth(stats.depth_access)


def can_descend(depth: int, stats: EffectiveStats) -> bool:
    """True when the player can go one band deeper given their gear."""
    return depth < max_accessible_depth(stats)


def can_ascend(depth: int) -> bool:
    """True when the player is below the surface and can climb one band."""
    return depth > 0


def descend(depth: int, stats: EffectiveStats) -> int:
    """New depth after a descend attempt — unchanged if gear can't reach deeper."""
    return clamp_depth(depth + 1) if can_descend(depth, stats) else clamp_depth(depth)


def ascend(depth: int) -> int:
    """New depth after climbing one band — never above the surface."""
    return clamp_depth(depth - 1) if can_ascend(depth) else 0


def describe_position(depth: int) -> str:
    """Human-readable ``"<emoji> <Label> (depth N/MAX)"`` for embeds."""
    biome = biome_for_depth(depth)
    label = f"{BIOME_EMOJI[biome]} {BIOME_LABELS[biome]}"
    return f"{label} (depth {clamp_depth(depth)}/{MAX_DEPTH})"


def descend_hint(stats: EffectiveStats) -> str:
    """Why a descend is blocked / what unlocks the next band — for UX copy."""
    reach = max_accessible_depth(stats)
    if reach >= MAX_DEPTH:
        return "You have the gear to reach the deepest bands."
    next_biome = BIOME_ORDER[reach + 1]
    return (
        f"Equip a brighter light to descend to {BIOME_LABELS[next_biome]} "
        f"(needs depth access {reach + 1})."
    )


__all__ = [
    "MAX_DEPTH",
    "BIOME_LABELS",
    "BIOME_EMOJI",
    "clamp_depth",
    "biome_for_depth",
    "max_accessible_depth",
    "can_descend",
    "can_ascend",
    "descend",
    "ascend",
    "describe_position",
    "descend_hint",
]
