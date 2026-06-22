"""Mining energy — the playable-pace "fuel" for digging (pure domain).

Energy is the frequency brake the owner chose **instead of a per-dig cooldown**
(2026-06-22): each dig spends energy, energy refills passively over time, and
food / boosters top it up.  It is sized to the sim-pinned ~360-digs-per-active-
hour sustained throttle (``docs/planning/mining-economy-balance-2026-06-22.md``)
— a full bar is a short burst, after which you regen ~1 unit / ``REGEN_SECONDS``
(= 360 / hour), so the faucet lands in line with the rest of the economy without
making every action wait.  Food and boosters let an active player keep going
past the passive rate (a coin/fish sink, not a wall).

Pure functions only — no DB, no Discord — so the regen math is unit-testable.
The persisted state is ``(energy:int, updated_at:unix)`` on
``mining_player_state``; the *effective* energy at any instant is computed from
elapsed time by :func:`settle` (we store a value + a timestamp, never a
background ticker — ADR-001/002: no external state, no scheduler dependency).
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Sim-pinned tunables (docs/planning/mining-economy-balance-2026-06-22.md) ---
MAX_ENERGY = 60  # a full bar ≈ a 60-dig burst before you regen-throttle
DIG_COST = 1  # energy spent per dig
REGEN_SECONDS = 10  # +1 energy every 10s → 360/hour (the chosen throttle)

# Energy restored by eating/consuming a food or booster item. Boosters (ration /
# energy drink) are the buyable refill; "cooked fish" is the cooked-at-a-campfire
# food (services/mining_workflow.cook) — the owner's "refill by eating fish".
RESTORE_VALUES: dict[str, int] = {
    "ration": 25,
    "energy drink": 50,
    "cooked fish": 30,
}


@dataclass(frozen=True)
class EnergyState:
    """Persisted energy: ``current`` units as of ``updated_at`` (unix seconds)."""

    current: int
    updated_at: int


def settle(
    state: EnergyState,
    now: int,
    *,
    max_energy: int = MAX_ENERGY,
    regen_seconds: int = REGEN_SECONDS,
) -> EnergyState:
    """Apply passive regen up to *now* and return the settled state.

    Caps at *max_energy*.  When below the cap, the sub-interval remainder is
    preserved in the returned ``updated_at`` so repeated settles never discard
    partial regen (settling every second must equal settling once).
    """
    if state.current >= max_energy:
        return EnergyState(max_energy, now)
    elapsed = max(0, now - state.updated_at)
    gained = elapsed // regen_seconds
    new = min(max_energy, state.current + gained)
    if new >= max_energy:
        return EnergyState(max_energy, now)
    return EnergyState(new, state.updated_at + gained * regen_seconds)


def can_dig(
    state: EnergyState,
    now: int,
    *,
    cost: int = DIG_COST,
    max_energy: int = MAX_ENERGY,
    regen_seconds: int = REGEN_SECONDS,
) -> bool:
    """True if settled energy at *now* covers one dig's *cost*."""
    return (
        settle(state, now, max_energy=max_energy, regen_seconds=regen_seconds).current
        >= cost
    )


def spend(
    state: EnergyState,
    now: int,
    *,
    cost: int = DIG_COST,
    max_energy: int = MAX_ENERGY,
    regen_seconds: int = REGEN_SECONDS,
) -> EnergyState:
    """Settle, then debit *cost* (never below 0). Caller checks :func:`can_dig`."""
    s = settle(state, now, max_energy=max_energy, regen_seconds=regen_seconds)
    return EnergyState(max(0, s.current - cost), s.updated_at)


def restore(
    state: EnergyState,
    now: int,
    amount: int,
    *,
    max_energy: int = MAX_ENERGY,
    regen_seconds: int = REGEN_SECONDS,
) -> EnergyState:
    """Settle, then add *amount* (capped at *max_energy*) — eating food/boosters."""
    s = settle(state, now, max_energy=max_energy, regen_seconds=regen_seconds)
    return EnergyState(min(max_energy, s.current + amount), s.updated_at)


def seconds_until(
    state: EnergyState,
    now: int,
    target: int,
    *,
    max_energy: int = MAX_ENERGY,
    regen_seconds: int = REGEN_SECONDS,
) -> int:
    """Seconds of passive regen until settled energy reaches *target* (0 if already)."""
    s = settle(state, now, max_energy=max_energy, regen_seconds=regen_seconds)
    if s.current >= target:
        return 0
    needed = min(max_energy, target) - s.current
    remainder = now - s.updated_at  # 0 ≤ remainder < regen_seconds
    return max(0, needed * regen_seconds - remainder)


def restore_value(item: str) -> int | None:
    """Energy an item restores when eaten/used, or ``None`` if it is not food."""
    return RESTORE_VALUES.get(item.strip().lower())


def bar(current: int, max_energy: int = MAX_ENERGY, *, width: int = 10) -> str:
    """A compact ``⚡ 42/60 [▰▰▰▰▰▰▰▱▱▱]`` energy gauge for the navigator embed."""
    current = max(0, min(max_energy, current))
    filled = round(width * current / max_energy) if max_energy else 0
    return f"⚡ {current}/{max_energy} [{'▰' * filled}{'▱' * (width - filled)}]"
