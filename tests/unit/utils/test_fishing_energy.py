"""fishing energy — the pure pacing math (settle / spend / regen / gauge)."""

from __future__ import annotations

from utils.fishing import energy


def _state(current, updated_at=0):
    return energy.EnergyState(current, updated_at)


def test_settle_regens_one_per_regen_interval_capped():
    # 5 energy, 0 updated; after 3 regen intervals → 8.
    s = energy.settle(_state(5, 0), now=3 * energy.REGEN_SECONDS)
    assert s.current == 8
    # never exceeds the cap no matter how much time passed
    full = energy.settle(_state(5, 0), now=10**9)
    assert full.current == energy.MAX_ENERGY


def test_settle_preserves_sub_interval_remainder():
    # settling twice must equal settling once (no lost partial regen)
    start = _state(0, 0)
    once = energy.settle(start, now=95)  # 95s @ 30s/regen → +3, 5s remainder kept
    twice = energy.settle(energy.settle(start, now=40), now=95)
    assert once == twice
    assert once.current == 3


def test_can_cast_and_spend():
    empty = _state(0, 0)
    assert energy.can_cast(empty, now=0) is False
    # a cast costs CAST_COST (2): 1 energy is not enough, the full cost is
    assert energy.can_cast(_state(energy.CAST_COST - 1, 0), now=0) is False
    assert energy.can_cast(_state(energy.CAST_COST, 0), now=0) is True
    after = energy.spend(_state(5, 0), now=0)
    assert after.current == 5 - energy.CAST_COST  # one cast = one CAST_COST
    # spending never drops below zero (caller is meant to gate with can_cast)
    assert energy.spend(empty, now=0).current == 0


def test_seconds_until_a_cast_is_affordable():
    empty = _state(0, 0)
    assert energy.seconds_until(empty, now=0, target=1) == energy.REGEN_SECONDS
    # already affordable → 0
    assert energy.seconds_until(_state(5, 0), now=0, target=1) == 0


def test_bar_renders_a_gauge():
    g = energy.bar(energy.MAX_ENERGY)
    assert f"{energy.MAX_ENERGY}/{energy.MAX_ENERGY}" in g
    assert "▱" not in energy.bar(energy.MAX_ENERGY)  # full bar = all filled
    assert "▰" not in energy.bar(0)  # empty bar = none filled
