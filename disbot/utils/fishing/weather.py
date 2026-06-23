"""Fishing weather — a daily, date-seeded global bias (owner design "Other ideas").

The fishing design's surfaced idea (``docs/planning/fishing-minigame-design-2026-06-22.md``
§"Other ideas surfaced"): *"a global daily bias (e.g. 'storm: rare fish biting,
shorter windows') gives a reason to fish today and a shared talking point."*

The weather is **derived from the calendar date**, not stored — the same ISO date
always maps to the same condition (a deterministic sha256-seeded weighted pick),
so **everyone in every guild sees the same weather on the same day** (the shared
talking point) and it costs no DB / no scheduler (ADR-001/002 friendly). Clear is
the common default; storms are rare. Each condition compounds two multipliers onto
the cast that the workflow already threads:

* ``bite_speed_mult`` (≤ 1 = faster bites) multiplies the rod×bait bite speed;
* ``rarity_mult`` (≥ 1 = biases bigger) multiplies the rod×bait rarity pull.

So weather is a *third* "how-well" knob beside the rod and bait, but a transient,
shared, free one — it changes the *feel* of a day without touching progression
(it never unlocks a new size band; that stays the fishing-level axis).

Pure + stdlib-only (no Discord, no DB, no ambient clock in the core picker — the
date is passed in) so every number here is unit-testable.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timezone


@dataclass(frozen=True)
class Weather:
    """One weather condition — its identity, flavour, and the two cast knobs."""

    key: str
    name: str
    emoji: str
    #: Multiplier on the bite wait (≤ 1 = faster bites, > 1 = slower/patient).
    bite_speed_mult: float
    #: Multiplier on the rarity pull (≥ 1 = biases the catch toward bigger fish).
    rarity_mult: float
    #: Selection weight — higher = more common across days (clear dominates).
    weight: int
    #: One-line player-facing flavour for the forecast / cast embeds.
    blurb: str


#: The weather table. Weights sum to 100 (read as rough %-of-days). The spread is
#: a deliberate risk/reward: rain = fast & common, storm = slow but the rarest
#: fish run, fog = patient but rarer, calm = a gently better all-rounder.
CONDITIONS: tuple[Weather, ...] = (
    Weather(
        "clear",
        "Clear skies",
        "☀️",
        bite_speed_mult=1.0,
        rarity_mult=1.0,
        weight=38,
        blurb="Calm and clear — a steady, ordinary day to fish.",
    ),
    Weather(
        "rain",
        "Rain",
        "🌧️",
        bite_speed_mult=0.85,
        rarity_mult=1.0,
        weight=22,
        blurb="Rain stirs the surface — the fish are biting fast today.",
    ),
    Weather(
        "calm",
        "Glassy calm",
        "🌅",
        bite_speed_mult=0.92,
        rarity_mult=1.08,
        weight=18,
        blurb="Glassy, still water — quick bites and a touch more chance at a prize.",
    ),
    Weather(
        "fog",
        "Fog",
        "🌫️",
        bite_speed_mult=1.15,
        rarity_mult=1.12,
        weight=14,
        blurb="Thick fog — slow, patient bites, but rarer fish lurk beneath.",
    ),
    Weather(
        "storm",
        "Storm",
        "⛈️",
        bite_speed_mult=1.12,
        rarity_mult=1.30,
        weight=8,
        blurb="Storm's up — choppy and slow, but the big, rare ones are running.",
    ),
)

#: Neutral fallback (never selected; guards a malformed/empty table).
_NEUTRAL = CONDITIONS[0]

_TOTAL_WEIGHT = sum(c.weight for c in CONDITIONS)


def _date_fraction(d: date) -> float:
    """A deterministic uniform fraction in [0, 1) seeded by the ISO date.

    Uses sha256 (not Python's salted ``hash``) so the mapping is stable across
    processes and machines — every agent / shard computes the same weather for a
    given day.
    """
    digest = hashlib.sha256(d.isoformat().encode("utf-8")).digest()
    # First 8 bytes → a 64-bit int → a fraction of its range.
    value = int.from_bytes(digest[:8], "big")
    return value / float(1 << 64)


def weather_for_date(d: date) -> Weather:
    """The weather for calendar date *d* — deterministic, weighted by frequency."""
    if _TOTAL_WEIGHT <= 0:
        return _NEUTRAL
    target = _date_fraction(d) * _TOTAL_WEIGHT
    cumulative = 0.0
    for condition in CONDITIONS:
        cumulative += condition.weight
        if target < cumulative:
            return condition
    return CONDITIONS[-1]  # float-edge guard


def current_weather(now: datetime | None = None) -> Weather:
    """Today's weather (UTC date). *now* is injectable for tests."""
    moment = now or datetime.now(timezone.utc)
    return weather_for_date(moment.date())


def effect_text(weather: Weather) -> str:
    """A compact "what it does" line, e.g. ``faster bites · rarer fish``.

    Only names the knobs that actually move, so ``clear`` reads as "no effect".
    """
    parts: list[str] = []
    if weather.bite_speed_mult < 1.0:
        parts.append("faster bites")
    elif weather.bite_speed_mult > 1.0:
        parts.append("slower bites")
    if weather.rarity_mult > 1.0:
        parts.append("rarer fish")
    return " · ".join(parts) if parts else "no effect — a fair, ordinary day"
