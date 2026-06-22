"""Pure idle-farm domain tests — egg accrual, capacity, and pricing math.

The accrual mirrors ``utils.fishing.energy.settle`` (a stored value + a timestamp,
computed from elapsed time), so the invariants are the same shape: monotonic,
capped, and remainder-preserving (settling repeatedly == settling once).
"""

from __future__ import annotations

import pytest

from utils import farm as farm_mod
from utils.farm import FarmState


def _state(chickens=1, eggs=0, updated_at=0, coop_level=0) -> FarmState:
    return FarmState(chickens, eggs, updated_at, coop_level)


# --------------------------------------------------------------------- capacity


def test_coop_capacity_grows_with_level():
    assert farm_mod.coop_capacity(0) == farm_mod.BASE_CAPACITY
    assert (
        farm_mod.coop_capacity(1)
        == farm_mod.BASE_CAPACITY + farm_mod.CAPACITY_PER_LEVEL
    )
    assert (
        farm_mod.coop_capacity(3)
        == farm_mod.BASE_CAPACITY + 3 * farm_mod.CAPACITY_PER_LEVEL
    )


def test_coop_capacity_floors_negative_level():
    assert farm_mod.coop_capacity(-5) == farm_mod.BASE_CAPACITY


# ----------------------------------------------------------------------- settle


def test_settle_accrues_eggs_per_interval_per_hen():
    # 3 hens, 2 full intervals elapsed → 6 eggs.
    now = 2 * farm_mod.LAY_INTERVAL_SECONDS
    out = farm_mod.settle(_state(chickens=3, updated_at=0), now)
    assert out.eggs == 6


def test_settle_caps_at_capacity():
    # One hen, a huge elapsed time → caps at the level-0 coop capacity.
    out = farm_mod.settle(_state(chickens=1, updated_at=0), 10**9)
    assert out.eggs == farm_mod.coop_capacity(0)
    assert out.updated_at == 10**9  # capped → clock snaps to now


def test_settle_preserves_sub_interval_remainder():
    # 1.5 intervals elapsed for one hen → 1 egg, and the half-interval remainder
    # is preserved so the next settle still credits it (no progress lost).
    interval = farm_mod.LAY_INTERVAL_SECONDS
    now = interval + interval // 2
    out = farm_mod.settle(_state(chickens=1, updated_at=0), now)
    assert out.eggs == 1
    assert out.updated_at == interval  # remainder (interval//2) preserved


def test_settle_is_idempotent_across_repeated_calls():
    # Settling in two steps must equal settling once (the energy invariant).
    interval = farm_mod.LAY_INTERVAL_SECONDS
    start = _state(chickens=2, updated_at=0)
    once = farm_mod.settle(start, 5 * interval)
    twice = farm_mod.settle(farm_mod.settle(start, 3 * interval), 5 * interval)
    assert once == twice


def test_settle_with_no_hens_lays_nothing():
    out = farm_mod.settle(_state(chickens=0, eggs=4, updated_at=0), 10**6)
    assert out.eggs == 4


def test_settle_never_exceeds_higher_capacity_after_upgrade():
    out = farm_mod.settle(_state(chickens=1, coop_level=2, updated_at=0), 10**9)
    assert out.eggs == farm_mod.coop_capacity(2)


# ----------------------------------------------------------- seconds_until_full


def test_seconds_until_full_zero_when_capped():
    capped = _state(chickens=1, eggs=farm_mod.coop_capacity(0), updated_at=0)
    assert farm_mod.seconds_until_full(capped, 0) == 0


def test_seconds_until_full_counts_remaining_batches():
    # Empty level-0 coop, 1 hen: needs `capacity` intervals to fill.
    out = farm_mod.seconds_until_full(_state(chickens=1, updated_at=0), 0)
    assert out == farm_mod.coop_capacity(0) * farm_mod.LAY_INTERVAL_SECONDS


def test_seconds_until_full_zero_with_no_hens():
    assert farm_mod.seconds_until_full(_state(chickens=0, updated_at=0), 0) == 0


# -------------------------------------------------------------------- economics


def test_collect_value_scales_with_eggs():
    assert farm_mod.collect_value(0) == 0
    assert farm_mod.collect_value(10) == 10 * farm_mod.EGG_VALUE


def test_collect_value_floors_negative():
    assert farm_mod.collect_value(-3) == 0


def test_chicken_price_starts_at_base_and_grows():
    # Owning the starter hen → the next costs the base price; each one more grows.
    base = farm_mod.chicken_price(farm_mod.STARTER_CHICKENS)
    assert base == farm_mod.BASE_CHICKEN_PRICE
    bigger = farm_mod.chicken_price(farm_mod.STARTER_CHICKENS + 3)
    assert bigger > base


def test_chicken_price_is_monotonic():
    prices = [farm_mod.chicken_price(n) for n in range(1, 12)]
    assert prices == sorted(prices)
    assert len(set(prices)) > 1  # genuinely increasing, not flat


def test_coop_upgrade_price_grows_with_level():
    assert farm_mod.coop_upgrade_price(0) == farm_mod.BASE_COOP_PRICE
    assert farm_mod.coop_upgrade_price(2) > farm_mod.coop_upgrade_price(1)


def test_lay_rate_per_hour():
    per_hen = 3600 // farm_mod.LAY_INTERVAL_SECONDS
    assert farm_mod.lay_rate_per_hour(1) == per_hen
    assert farm_mod.lay_rate_per_hour(4) == 4 * per_hen


# ----------------------------------------------------------------------- caps


def test_can_buy_chicken_respects_ceiling():
    assert farm_mod.can_buy_chicken(farm_mod.MAX_CHICKENS - 1) is True
    assert farm_mod.can_buy_chicken(farm_mod.MAX_CHICKENS) is False


def test_can_upgrade_coop_respects_ceiling():
    assert farm_mod.can_upgrade_coop(farm_mod.MAX_COOP_LEVEL - 1) is True
    assert farm_mod.can_upgrade_coop(farm_mod.MAX_COOP_LEVEL) is False


# -------------------------------------------------------------------------- bar


@pytest.mark.parametrize("eggs", [0, 5, 20, 999])
def test_egg_bar_stays_within_width(eggs):
    bar = farm_mod.egg_bar(eggs, 20, width=10)
    assert bar.count("▰") + bar.count("▱") == 10
