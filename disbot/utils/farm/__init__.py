"""Pure idle-farm domain — egg accrual, capacity, and pricing math.

Re-exports the public surface of :mod:`utils.farm.farm` so callers can write
``from utils.farm import FarmState, settle`` (mirrors ``utils.fishing``).
"""

from __future__ import annotations

from utils.farm.farm import (
    BASE_CAPACITY,
    BASE_CHICKEN_PRICE,
    BASE_COOP_PRICE,
    CAPACITY_PER_LEVEL,
    EGG_VALUE,
    LAY_INTERVAL_SECONDS,
    MAX_CHICKENS,
    MAX_COOP_LEVEL,
    STARTER_CHICKENS,
    FarmState,
    can_buy_chicken,
    can_upgrade_coop,
    chicken_price,
    collect_value,
    coop_capacity,
    coop_upgrade_price,
    egg_bar,
    lay_rate_per_hour,
    seconds_until_full,
    settle,
)

__all__ = [
    "BASE_CAPACITY",
    "BASE_CHICKEN_PRICE",
    "BASE_COOP_PRICE",
    "CAPACITY_PER_LEVEL",
    "EGG_VALUE",
    "LAY_INTERVAL_SECONDS",
    "MAX_CHICKENS",
    "MAX_COOP_LEVEL",
    "STARTER_CHICKENS",
    "FarmState",
    "can_buy_chicken",
    "can_upgrade_coop",
    "chicken_price",
    "collect_value",
    "coop_capacity",
    "coop_upgrade_price",
    "egg_bar",
    "lay_rate_per_hour",
    "seconds_until_full",
    "settle",
]
