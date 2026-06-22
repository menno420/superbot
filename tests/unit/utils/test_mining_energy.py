"""Unit tests for utils.mining.energy — the pure regen/spend/restore math.

Energy is the owner's chosen frequency brake for mining (2026-06-22). The math
is pure (value + timestamp → effective energy), so it is fully unit-testable
without a DB or clock. These pins guard the two subtle properties: the cap, and
that repeated settles never lose partial regen.
"""

from __future__ import annotations

from utils.mining import energy
from utils.mining.energy import EnergyState


def test_settle_caps_at_max():
    s = energy.settle(EnergyState(10, 0), now=10_000, max_energy=60, regen_seconds=10)
    assert s.current == 60


def test_settle_regenerates_over_time():
    # 35s at 1/10s → +3 energy (floored), from 20 → 23.
    s = energy.settle(EnergyState(20, 1000), now=1035, max_energy=60, regen_seconds=10)
    assert s.current == 23


def test_settle_preserves_remainder_idempotent():
    """Settling in two steps must equal settling once (no lost partial regen)."""
    start = EnergyState(0, 0)
    once = energy.settle(start, now=95, regen_seconds=10, max_energy=60)
    step1 = energy.settle(start, now=44, regen_seconds=10, max_energy=60)
    twice = energy.settle(step1, now=95, regen_seconds=10, max_energy=60)
    assert once.current == twice.current == 9  # 95 // 10 = 9


def test_can_dig_and_spend():
    full = EnergyState(60, 0)
    assert energy.can_dig(full, now=60, cost=1)
    after = energy.spend(full, now=60, cost=1, max_energy=60, regen_seconds=10)
    assert after.current == 59


def test_cannot_dig_when_empty_and_no_regen_yet():
    # 0 energy, settled 'now' (no elapsed) → can't dig.
    s = EnergyState(0, 1000)
    assert not energy.can_dig(s, now=1000, cost=1, regen_seconds=10)


def test_spend_never_below_zero():
    s = energy.spend(EnergyState(0, 1000), now=1000, cost=1, regen_seconds=10)
    assert s.current == 0


def test_restore_caps_at_max():
    s = energy.restore(EnergyState(50, 0), now=0, amount=25, max_energy=60)
    assert s.current == 60


def test_seconds_until_next_dig():
    # empty, settled now → need 1 unit → a full regen interval away.
    s = EnergyState(0, 1000)
    assert energy.seconds_until(s, now=1000, target=1, regen_seconds=10) == 10
    # already have it → 0.
    assert energy.seconds_until(EnergyState(5, 1000), now=1000, target=1) == 0


def test_restore_value_lookup():
    assert energy.restore_value("ration") == 25
    assert energy.restore_value("Energy Drink") == 50  # case-insensitive
    assert energy.restore_value("stone") is None
    assert energy.restore_value("diamond pickaxe") is None


def test_bar_renders_proportionally():
    assert energy.bar(0, 60).startswith("⚡ 0/60")
    assert energy.bar(60, 60) == "⚡ 60/60 [▰▰▰▰▰▰▰▰▰▰]"
    mid = energy.bar(30, 60)
    assert mid.count("▰") == 5 and mid.count("▱") == 5


def test_restore_values_match_known_food():
    """The food/booster table mirrors the items added to the catalog/market."""
    assert set(energy.RESTORE_VALUES) == {"ration", "energy drink", "cooked fish"}
