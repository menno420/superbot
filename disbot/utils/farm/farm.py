"""Chicken farm — the pure *idle* domain (no DB, no Discord).

The bot's first **idle** activity: hens lay eggs over time, you collect them for
coins, and you spend coins on more hens (faster lay rate) and a bigger coop
(larger egg cap). The whole point of "idle" is that progress accrues **while you
are away** — so the egg count is never a stored running total kept current by a
ticker; it is a stored ``(eggs, updated_at)`` pair plus the flock size, and the
*effective* egg count at any instant is computed from elapsed time by
:func:`settle`.

This mirrors :mod:`utils.fishing.energy` / :mod:`utils.mining.energy` exactly
(a stored value + a timestamp, settled in pure code) — **no background ticker,
no external state** (ADR-001: no Redis; ADR-002: game state is best-effort, and
this design happens to be fully restart-safe because everything lives in the
``chicken_farm`` row).

Pure functions only, so the accrual + pricing math is unit-testable. The DB CRUD
lives in :mod:`utils.db.games.farm`; the audited write boundary (collect / buy /
upgrade, with the coin legs) lives in :mod:`services.farm_workflow`.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Idle-farm tunables (conservative faucet — the owner's standing "rewards
# too large & too frequent" caution from the mining rebalance applies to every
# new faucet). One free starter hen lays 1 egg / 5 min into a 20-egg coop, so an
# idle player banks at most ~40 coins over ~100 min before the coop caps — a
# small fraction of a `!daily`. Buying hens scales the faucet but each costs more
# coins (the sink), so the loop stays self-balancing. Tune against live play.
LAY_INTERVAL_SECONDS = 300  # one egg per hen every 5 minutes
EGG_VALUE = 2  # coins paid per egg on collect

STARTER_CHICKENS = 1  # every farmer starts with one free hen
MAX_CHICKENS = 100  # soft flock ceiling (price growth makes this self-limiting)
MAX_COOP_LEVEL = 10  # coop upgrade ceiling

BASE_CAPACITY = 20  # eggs a level-0 coop holds before it caps
CAPACITY_PER_LEVEL = 15  # +eggs of capacity per coop level

BASE_CHICKEN_PRICE = 40  # cost of the 2nd hen (when you own 1)
CHICKEN_PRICE_GROWTH = 1.55  # each additional hen costs this much more
BASE_COOP_PRICE = 100  # cost of coop level 1
COOP_PRICE_GROWTH = 1.8  # each coop level costs this much more


@dataclass(frozen=True)
class FarmState:
    """A player's farm: ``eggs`` uncollected as of ``updated_at`` (unix seconds).

    ``eggs`` is the *stored* (unsettled) count — the caller applies passive
    accrual via :func:`settle` against the current time before showing or
    collecting it.
    """

    chickens: int
    eggs: int
    updated_at: int
    coop_level: int


def coop_capacity(coop_level: int) -> int:
    """Max eggs a coop of *coop_level* can hold before it stops accruing."""
    return BASE_CAPACITY + CAPACITY_PER_LEVEL * max(0, coop_level)


def settle(state: FarmState, now: int) -> FarmState:
    """Apply passive egg-laying up to *now* and return the settled state.

    Eggs accrue in batches of ``chickens`` once per :data:`LAY_INTERVAL_SECONDS`,
    capped at :func:`coop_capacity`. When below the cap, the sub-interval
    remainder is preserved in the returned ``updated_at`` so repeated settles
    never discard partial progress (settling every second equals settling once).
    """
    cap = coop_capacity(state.coop_level)
    if state.chickens <= 0:
        # No hens → no laying; keep eggs, just advance the clock.
        return FarmState(state.chickens, min(state.eggs, cap), now, state.coop_level)
    if state.eggs >= cap:
        return FarmState(state.chickens, cap, now, state.coop_level)
    elapsed = max(0, now - state.updated_at)
    intervals = elapsed // LAY_INTERVAL_SECONDS
    new_eggs = min(cap, state.eggs + intervals * state.chickens)
    if new_eggs >= cap:
        return FarmState(state.chickens, cap, now, state.coop_level)
    return FarmState(
        state.chickens,
        new_eggs,
        state.updated_at + intervals * LAY_INTERVAL_SECONDS,
        state.coop_level,
    )


def seconds_until_full(state: FarmState, now: int) -> int:
    """Seconds of passive laying until the coop is full (0 if already / no hens)."""
    s = settle(state, now)
    cap = coop_capacity(s.coop_level)
    if s.chickens <= 0 or s.eggs >= cap:
        return 0
    remaining = cap - s.eggs
    # Eggs arrive `chickens` at a time; ceil-divide for the batches still needed.
    intervals_needed = -(-remaining // s.chickens)
    remainder = now - s.updated_at  # 0 ≤ remainder < LAY_INTERVAL_SECONDS
    return max(0, intervals_needed * LAY_INTERVAL_SECONDS - remainder)


def collect_value(eggs: int) -> int:
    """Coins paid out for collecting *eggs* (the modest faucet leg)."""
    return max(0, eggs) * EGG_VALUE


def chicken_price(current_chickens: int) -> int:
    """Coin cost of buying the *next* hen when you own ``current_chickens``.

    The first extra hen is cheap (:data:`BASE_CHICKEN_PRICE`) and each one after
    costs :data:`CHICKEN_PRICE_GROWTH`× more — the scaling coin sink that keeps
    the faucet from running away.
    """
    extra = max(0, current_chickens - STARTER_CHICKENS)
    return round(BASE_CHICKEN_PRICE * (CHICKEN_PRICE_GROWTH**extra))


def coop_upgrade_price(coop_level: int) -> int:
    """Coin cost of upgrading from *coop_level* to the next level."""
    return round(BASE_COOP_PRICE * (COOP_PRICE_GROWTH ** max(0, coop_level)))


def can_buy_chicken(current_chickens: int) -> bool:
    """True if the flock is below the soft :data:`MAX_CHICKENS` ceiling."""
    return current_chickens < MAX_CHICKENS


def can_upgrade_coop(coop_level: int) -> bool:
    """True if the coop is below the :data:`MAX_COOP_LEVEL` ceiling."""
    return coop_level < MAX_COOP_LEVEL


def lay_rate_per_hour(chickens: int) -> int:
    """Eggs laid per hour at a flock of *chickens* (for the panel blurb)."""
    return max(0, chickens) * (3600 // LAY_INTERVAL_SECONDS)


def egg_bar(eggs: int, capacity: int, *, width: int = 10) -> str:
    """A compact ``🥚 12/20 [▰▰▰▰▰▰▱▱▱▱]`` coop-fill gauge for the panel."""
    eggs = max(0, min(capacity, eggs))
    filled = round(width * eggs / capacity) if capacity else 0
    return f"🥚 {eggs}/{capacity} [{'▰' * filled}{'▱' * (width - filled)}]"
