"""Character stats — the gear + skills merge point (brainstorm §7.4).

The single read model for "how strong is this character?", combining equipped
gear (:func:`utils.equipment.compute_stats`) with allocated skill points
(:func:`utils.mining.skills.skill_stats`) into one
:class:`~utils.equipment.EffectiveStats` block.  Game logic (mining descent,
deathmatch) reads *this*, never gear or skills separately, so adding skills did
not touch any game's stat math.

Pure + stdlib-only.  An **empty allocation makes the result byte-identical to
gear-only stats** — the additive safety property that lets the skill tree ship
without changing existing play (asserted in
``tests/unit/utils/test_character_stats.py``).
"""

from __future__ import annotations

from utils.equipment import EffectiveStats, compute_stats
from utils.mining.skills import skill_stats


def character_stats(
    equipped: dict[str, str],
    alloc: dict[str, int] | None = None,
) -> EffectiveStats:
    """Combined gear + skill stats.

    *equipped* is ``{slot: item_name}``; *alloc* is ``{branch: points}`` (or
    ``None``/empty for a player who has spent nothing — in which case the result
    equals :func:`utils.equipment.compute_stats` exactly).
    """
    stats = compute_stats(equipped)
    if alloc:
        stats = stats + skill_stats(alloc)
    return stats


__all__ = ["character_stats"]
