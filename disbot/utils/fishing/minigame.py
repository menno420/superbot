"""Fishing minigame — pure tuning + resolve logic (owner design Q-0175).

The interactive ``cast → wait → BITE → reel`` loop, turned from a guess into
tuned numbers by the design simulation
(``tools/sim/fishing_minigame_sim.py`` → ``docs/planning/fishing-minigame-design-2026-06-22.md``).

The load-bearing finding: a reaction window over Discord is a **presence check,
not a reflex test** — the bot can only measure the whole round trip
``L_down + reaction + L_up`` against the window, so sub-second windows are
unwinnable on a normal connection. Hence the generous ~2.5 s window: an attentive
player almost always lands it; an AFK / distracted one misses (the fish gets
away). The *skill* is being present and holding your nerve through the fake-out.

Pure + stdlib-only (no Discord, no DB, no clock) so every number here is
unit-testable; :mod:`views.fishing.cast_view` owns the Discord + asyncio timing
and :mod:`services.fishing_workflow` owns the writes.
"""

from __future__ import annotations

import random

from utils.fishing.fish import FishSpecies, max_size_rank_for_level

# --- tuning (sim-recommended; re-tune against live telemetry once shipped) ---

#: Shore reaction window, seconds. The window flattens unfair latency-losses to
#: near-zero around 2–2.5 s (sim §2); rod tiers will *add* to this later.
REACTION_WINDOW = 2.5

#: Bite wait is randomised in this band so it never feels scripted (sim §3:
#: 3–6 s is "anticipation without boredom"). Memoryless within the band.
BITE_DELAY_MIN = 3.0
BITE_DELAY_MAX = 6.0

#: A hard floor so a bite is *never* instant — the floor is the anticipation.
BITE_DELAY_FLOOR = 1.5

#: Chance a cast gets a fake-out: a tiny shake shortly before the real bite.
#: Reeling on the fake-out scares the fish (a premature miss) — it turns the
#: wait into a "hold your nerve" skill (sim §3). Lead time before the real bite.
FAKEOUT_CHANCE = 0.45
FAKEOUT_LEAD = 0.6

#: A catch is a "trophy" when it sits in the top third of the player's currently
#: unlocked size band — the payoff fish that trigger the reel-fight. Exposed so
#: the cast view can flavour the BITE message and branch into the fight.
TROPHY_BAND_FRACTION = 1.0 / 3.0

#: Reel-fight (trophy) tuning. The fight is a short sequence of timed reel taps:
#: each tap is its own presence-check window (kept at the *full* generous window,
#: NOT the sim's tighter ``w*0.8`` — over Discord a tighter window punishes
#: latency, not skill, and trophies are already harder via more taps + escape).
#: A tap that lands in time can still let the fish snap free with a small escape
#: chance; that is the "the big one got away" tension (rod escape-resist will buy
#: this down in a later PR).
FIGHT_WINDOW = REACTION_WINDOW
FIGHT_INTER_ROUND_DELAY = 0.8  # a suspense beat between reel taps
FIGHT_MIN_TAPS = 2
FIGHT_MAX_TAPS = 4
SHORE_ESCAPE_CHANCE = 0.06  # per-tap snap-free chance on shore (no rod yet)


def roll_bite_delay(rng: random.Random | None = None) -> float:
    """Seconds to wait before the bite — uniform in the band, never below floor."""
    r = rng or random.Random()
    return max(BITE_DELAY_FLOOR, r.uniform(BITE_DELAY_MIN, BITE_DELAY_MAX))


def roll_fakeout(rng: random.Random | None = None) -> bool:
    """Whether this cast gets a pre-bite fake-out shake."""
    r = rng or random.Random()
    return r.random() < FAKEOUT_CHANCE


def is_trophy(species: FishSpecies, fishing_level: int) -> bool:
    """True when *species* is a trophy for a player at *fishing_level*.

    Trophy = the top :data:`TROPHY_BAND_FRACTION` of the unlocked size band, so
    it scales with progression: a freshly-unlocked big fish always reads as a
    trophy, while the same fish becomes ordinary once you out-level it.
    """
    cap = max_size_rank_for_level(fishing_level)
    threshold = cap - cap * TROPHY_BAND_FRACTION
    return species.size_rank > threshold


def reel_fight_taps(species: FishSpecies) -> int:
    """How many reel taps it takes to land *species* — scales with its size.

    The smallest trophy is a quick :data:`FIGHT_MIN_TAPS`-tap tussle; the biggest
    fish in the catalog is a full :data:`FIGHT_MAX_TAPS`-tap fight. Bigger fish
    fight harder (sim §1's ``tension`` model — taps scale with rarity).
    """
    span = FIGHT_MAX_TAPS - FIGHT_MIN_TAPS
    return FIGHT_MIN_TAPS + round(span * (species.size_rank / 21.0))


def fight_escape_chance(species: FishSpecies, escape_resist: float = 0.0) -> float:
    """Per-tap chance the fish snaps free, before/after rod escape-resist.

    ``escape_resist`` (0…1) is the rod knob a later PR turns; at v1 it is 0, so
    every fight runs at the base shore chance. Bigger fish are slightly more
    likely to throw the hook.
    """
    rarity = species.size_rank / 21.0
    base = SHORE_ESCAPE_CHANCE * (0.6 + rarity)
    return max(0.0, base * (1.0 - escape_resist))


def roll_escape(
    species: FishSpecies,
    *,
    escape_resist: float = 0.0,
    rng: random.Random | None = None,
) -> bool:
    """Roll whether the fish snaps free on this tap (see :func:`fight_escape_chance`)."""
    r = rng or random.Random()
    return r.random() < fight_escape_chance(species, escape_resist)


def reel_is_in_time(elapsed: float, window: float = REACTION_WINDOW) -> bool:
    """Did the reel land within the window? (``elapsed`` = bite → measured click.)

    The bot-measured ``elapsed`` already includes the network round trip the
    player can't control — see the module docstring for why the window is set
    generously rather than as a reflex test.
    """
    return 0.0 <= elapsed <= window
