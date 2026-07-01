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


def test_regen_seconds_for_unbuilt_is_byte_identical():
    # A ×1.0 multiplier (unbuilt Boathouse) ⇒ exactly REGEN_SECONDS ⇒ byte-identical.
    assert energy.regen_seconds_for(1.0) == energy.REGEN_SECONDS


def test_regen_seconds_for_built_boathouse_shortens_the_interval():
    # The pinned Boathouse multipliers (0.88 / 0.76) over the 30s base → 26 / 23.
    assert energy.regen_seconds_for(0.88) == 26
    assert energy.regen_seconds_for(0.76) == 23
    # A faster multiplier is a strictly shorter interval.
    assert energy.regen_seconds_for(0.76) < energy.regen_seconds_for(0.88)


def test_regen_seconds_for_never_below_one():
    # A pathological near-zero multiplier can never produce a 0-second (÷0) interval.
    assert energy.regen_seconds_for(0.0) == 1
    assert energy.regen_seconds_for(0.001) == 1


def test_settle_at_a_faster_interval_regens_more_in_the_same_time():
    # Same elapsed time, faster regen interval ⇒ more energy: 100s at 30s/tick = 3,
    # at 23s/tick (×0.76 boathouse) = 4.
    elapsed = 100
    normal = energy.settle(_state(5, 0), now=elapsed).current
    faster = energy.settle(
        _state(5, 0), now=elapsed, regen_seconds=energy.regen_seconds_for(0.76),
    ).current
    assert normal == 8
    assert faster == 9
    assert faster > normal
