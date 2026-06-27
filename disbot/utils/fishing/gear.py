"""Fishing gear → cast knobs (Q-0175 / V-14 "matching gear → better fishing").

The pure converter that turns the equipped character's :class:`~utils.equipment.
EffectiveStats` into the fishing cast's **4th** how-well knob, beside the rod, the
bait, and the day's weather.  Two stats feed two multipliers:

* ``fishing_power`` → a **rarity-pull** multiplier (≥ 1): like a rod's
  ``rarity_pull``, it biases the catch toward the big end of the *same* unlocked
  band — never a new band (that stays the fishing-level axis).
* ``bite_luck`` → a **bite-speed** multiplier (≤ 1 = faster): like a rod's
  ``bite_speed``, it quickens the bite wait.

Both are **bounded** and **default-preserving**: with no fishing gear equipped
(``fishing_power == bite_luck == 0``) every multiplier is exactly ``1.0``, so a
cast is byte-identical to the pre-gear behaviour.  The full ladder of three
charms tops out well below a rod tier on its own, so fishing gear is an
*optimisation*, never a gate (the starter still fishes fine).

Pure + stdlib-only (no Discord, no DB).  :mod:`services.fishing_workflow` reads
these and compounds them into the cast; the numbers are sim-pinned in
``docs/planning/fishing-gear-numbers-2026-06-27.md`` and
``tests/unit/utils/test_fishing_gear.py``.
"""

from __future__ import annotations

from utils.equipment import EffectiveStats

#: Per-point rarity-pull added by ``fishing_power`` (the full ladder's
#: ``fishing_power=6`` → ×1.24, a touch under a Silver rod's 1.25 pull).
PULL_PER_FISHING_POWER = 0.04
#: Per-point bite-wait reduction from ``bite_luck`` (``bite_luck=3`` → ×0.91).
BITE_SPEED_PER_BITE_LUCK = 0.03

#: Hard caps so gear can never dominate the rod×bait×weather stack even if a
#: future item or stacking path pushes the stats far past the charm ladder.
MAX_GEAR_PULL = 1.40  # ceiling on the rarity-pull multiplier
MIN_GEAR_BITE_SPEED = 0.75  # floor on the bite-speed multiplier (faster)


def fishing_pull_mult(stats: EffectiveStats) -> float:
    """Rarity-pull multiplier (≥ 1.0) contributed by ``stats.fishing_power``.

    ``1.0`` when no fishing gear is equipped (``fishing_power <= 0``); rises
    ``PULL_PER_FISHING_POWER`` per point, capped at :data:`MAX_GEAR_PULL`.
    """
    power = max(0, stats.fishing_power)
    return min(1.0 + PULL_PER_FISHING_POWER * power, MAX_GEAR_PULL)


def fishing_bite_speed_mult(stats: EffectiveStats) -> float:
    """Bite-speed multiplier (≤ 1.0 = faster) contributed by ``stats.bite_luck``.

    ``1.0`` when no fishing gear is equipped (``bite_luck <= 0``); falls
    ``BITE_SPEED_PER_BITE_LUCK`` per point, floored at :data:`MIN_GEAR_BITE_SPEED`.
    """
    luck = max(0, stats.bite_luck)
    return max(1.0 - BITE_SPEED_PER_BITE_LUCK * luck, MIN_GEAR_BITE_SPEED)


def has_fishing_bonus(stats: EffectiveStats) -> bool:
    """Whether *stats* carry any fishing gear contribution (for cast-panel copy)."""
    return stats.fishing_power > 0 or stats.bite_luck > 0


__all__ = [
    "PULL_PER_FISHING_POWER",
    "BITE_SPEED_PER_BITE_LUCK",
    "MAX_GEAR_PULL",
    "MIN_GEAR_BITE_SPEED",
    "fishing_pull_mult",
    "fishing_bite_speed_mult",
    "has_fishing_bonus",
]
