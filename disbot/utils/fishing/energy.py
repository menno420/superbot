"""Fishing energy — the playable-pace "fuel" for casting (pure domain).

The owner's "soft energy/cooldown" pacing decision (AskUserQuestion 2026-06-22):
each cast spends energy, energy refills passively over time, and being out of
energy makes you wait — so fishing is finite and a caught fish can sell for real
coins (the #1289 sell-value was kept low precisely because casting was unpaced).

**A SEPARATE bar from mining** (the owner's explicit choice): you can fish when
mined-out and vice-versa. The regen *math* mirrors :mod:`utils.mining.energy`,
but fishing keeps its own copy + its own tunables so the two systems stay
decoupled and mining is untouched. (Rule of three: if a *third* energy system
ever appears, extract the shared ``settle/spend`` core into one ``utils`` home
rather than copying a third time.)

Pure functions only — no DB, no Discord — so the regen math is unit-testable.
The persisted state is ``(energy:int, updated_at:unix)`` on the ``fishing_energy``
table; *effective* energy at any instant is computed from elapsed time by
:func:`settle` (a stored value + a timestamp, never a background ticker —
ADR-001/002: no external state, no scheduler).
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Fishing-energy tunables (separate from mining; tune against live play) ---
# A SEPARATE 60-unit bar, scale-parallel to mining's (the owner's pictured model,
# AskUserQuestion 2026-06-22), but paced gentler because a cast is a multi-second
# skill moment, not a one-shot dig: each cast costs 2 and energy regens 1/30s, so
# a full bar is a ~30-cast burst, then a gentle sustained rate — pacing, not a wall.
MAX_ENERGY = 60  # a full bar ≈ a 30-cast session before you regen-throttle
CAST_COST = 2  # energy spent per cast
REGEN_SECONDS = 30  # +1 energy every 30s (≈ 1 cast / minute sustained at cost 2)


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

    Caps at *max_energy*. When below the cap, the sub-interval remainder is
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


def can_cast(
    state: EnergyState,
    now: int,
    *,
    cost: int = CAST_COST,
    max_energy: int = MAX_ENERGY,
    regen_seconds: int = REGEN_SECONDS,
) -> bool:
    """True if settled energy at *now* covers one cast's *cost*."""
    return (
        settle(state, now, max_energy=max_energy, regen_seconds=regen_seconds).current
        >= cost
    )


def spend(
    state: EnergyState,
    now: int,
    *,
    cost: int = CAST_COST,
    max_energy: int = MAX_ENERGY,
    regen_seconds: int = REGEN_SECONDS,
) -> EnergyState:
    """Settle, then debit *cost* (never below 0). Caller checks :func:`can_cast`."""
    s = settle(state, now, max_energy=max_energy, regen_seconds=regen_seconds)
    return EnergyState(max(0, s.current - cost), s.updated_at)


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


def regen_seconds_for(regen_mult: float, *, base: int = REGEN_SECONDS) -> int:
    """The effective regen interval when a structure speeds regen by *regen_mult*.

    A built **Boathouse** (``utils.mining.structures.boathouse_regen_mult``) grants a
    multiplier ≤ 1.0 (lower = faster refill); this turns it into the ``regen_seconds``
    the :func:`settle` / :func:`spend` / :func:`seconds_until` calls use. ``regen_mult``
    of ``1.0`` (unbuilt) returns exactly *base* ⇒ byte-identical energy. Never below 1
    (a 0-second interval would divide-by-zero the regen math).
    """
    return max(1, round(base * regen_mult))


def bar(current: int, max_energy: int = MAX_ENERGY, *, width: int = 10) -> str:
    """A compact ``⚡ 42/60 [▰▰▰▰▰▰▰▱▱▱]`` energy gauge for the fishing panel."""
    current = max(0, min(max_energy, current))
    filled = round(width * current / max_energy) if max_energy else 0
    return f"⚡ {current}/{max_energy} [{'▰' * filled}{'▱' * (width - filled)}]"
