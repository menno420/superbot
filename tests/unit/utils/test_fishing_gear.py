"""Fishing gear → cast-knob conversion (Q-0175 / V-14).

Pins the sim numbers in ``docs/planning/fishing-gear-numbers-2026-06-27.md`` and
the default-preserving (additive) safety property: no fishing gear ⇒ ×1.0 knobs.
"""

from __future__ import annotations

import math

import pytest

from utils import equipment as eq
from utils.fishing import gear


def _stats(**kw: int) -> eq.EffectiveStats:
    return eq.EffectiveStats(**kw)


# --- default-preserving (byte-identical) safety property ---------------------


def test_no_fishing_gear_is_neutral():
    """Zero fishing stats ⇒ both multipliers are exactly 1.0 (the additive
    safety property: a cast is byte-identical to the pre-gear behaviour)."""
    s = _stats()
    assert gear.fishing_pull_mult(s) == 1.0
    assert gear.fishing_bite_speed_mult(s) == 1.0
    assert gear.has_fishing_bonus(s) is False


def test_mining_combat_stats_do_not_leak_into_fishing():
    """Only fishing_power/bite_luck move the knobs — mining/combat stats are inert."""
    s = _stats(mining_power=9, damage=20, defense=14, luck=5, loot_bonus=5)
    assert gear.fishing_pull_mult(s) == 1.0
    assert gear.fishing_bite_speed_mult(s) == 1.0
    assert gear.has_fishing_bonus(s) is False


# --- the sim-pinned ladder numbers ------------------------------------------


@pytest.mark.parametrize(
    ("power", "expected"),
    [(2, 1.08), (4, 1.16), (6, 1.24)],  # the three charm tiers
)
def test_pull_mult_matches_the_pinned_ladder(power: int, expected: float):
    assert math.isclose(gear.fishing_pull_mult(_stats(fishing_power=power)), expected)


@pytest.mark.parametrize(
    ("luck", "expected"),
    [(1, 0.97), (2, 0.94), (3, 0.91)],  # the three charm tiers
)
def test_bite_speed_mult_matches_the_pinned_ladder(luck: int, expected: float):
    assert math.isclose(
        gear.fishing_bite_speed_mult(_stats(bite_luck=luck)),
        expected,
    )


def test_master_angler_stays_under_a_silver_rod_pull():
    """The full ladder's pull (×1.24) is a touch under a Silver rod (1.25) — gear
    is an optimisation on top of the rod, never a replacement for it."""
    from utils.fishing import rods

    silver = rods.rod_for_tier(2)
    assert gear.fishing_pull_mult(_stats(fishing_power=6)) < silver.rarity_pull


# --- bounds + monotonicity --------------------------------------------------


def test_pull_is_capped():
    assert gear.fishing_pull_mult(_stats(fishing_power=10_000)) == gear.MAX_GEAR_PULL


def test_bite_speed_is_floored():
    assert (
        gear.fishing_bite_speed_mult(_stats(bite_luck=10_000))
        == gear.MIN_GEAR_BITE_SPEED
    )


def test_negative_stats_are_clamped_to_neutral():
    s = _stats(fishing_power=-3, bite_luck=-3)
    assert gear.fishing_pull_mult(s) == 1.0
    assert gear.fishing_bite_speed_mult(s) == 1.0


def test_knobs_are_monotonic():
    pulls = [gear.fishing_pull_mult(_stats(fishing_power=p)) for p in range(0, 8)]
    bites = [gear.fishing_bite_speed_mult(_stats(bite_luck=b)) for b in range(0, 8)]
    assert pulls == sorted(pulls)  # non-decreasing pull
    assert bites == sorted(bites, reverse=True)  # non-increasing (faster) bite


def test_has_fishing_bonus_detects_either_stat():
    assert gear.has_fishing_bonus(_stats(fishing_power=1)) is True
    assert gear.has_fishing_bonus(_stats(bite_luck=1)) is True
