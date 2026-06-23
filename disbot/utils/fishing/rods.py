"""The fishing rod ladder — the second, orthogonal progression axis (Q-0175).

The design's two-axis model (``docs/planning/fishing-minigame-design-2026-06-22.md``):

* **Fishing level** (``game_xp``) gates *what* you can catch — the size bands.
* **The rod** gates *how well / which-within-band* you catch it — five knobs the
  design sim tuned (``tools/sim/fishing_minigame_sim.py`` § 4):

  - ``window_bonus``     — seconds added to the reaction window (the fairness knob;
    a weak connection on a good rod is comfortable).
  - ``bite_speed``       — multiplier on the bite wait (<1 = faster bites = pacing).
  - ``rarity_pull``      — >1 biases the catch toward the big end of your band
    (the reward-quality knob).
  - ``escape_resist``    — 0…1 reduces the reel-fight snap-free chance (makes the
    bigger fish / future deepwater viable).
  - ``premature_grace``  — 0…1 chance a *premature* reel (reeling before the bite —
    the fake-out's trap) is forgiven instead of spooking the fish (the nerve knob;
    the design's fifth axis that the fake-out was meant to make meaningful). Spent
    once per cast, so it rescues an itchy-finger slip, never button-mashing.

Crucially the **starter rod still catches fine** — rods make fishing *nicer and
more rewarding*, never *possible* (the plan's "gear is never required"). Rods are
**bought with coins** (a finite sink for the coins fish now sell for, #1289);
each tier requires the one below it. Prices are tuning constants.

Pure + stdlib-only (no Discord, no DB). :mod:`services.fishing_workflow` owns the
purchase write; the cast view + roll read the equipped rod's knobs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rod:
    """One rung of the rod ladder — a tier index, a name, the four knobs, price."""

    tier: int
    name: str
    emoji: str
    window_bonus: float  # seconds added to the reaction window
    bite_speed: float  # multiplier on the bite wait (<1 = faster)
    rarity_pull: float  # >1 biases catches toward the big end of the band
    escape_resist: float  # 0…1 reduces reel-fight snap-free chance
    premature_grace: float  # 0…1 chance a premature reel is forgiven (once/cast)
    price: int  # coin cost to upgrade *into* this tier (starter = 0)


#: The ladder, tier 0 (starter) → tier 4 (diamond). Mirrors the sim's
#: ``ROD_LADDER`` knob values; prices are conservative starting points (tunable).
ROD_LADDER: tuple[Rod, ...] = (
    Rod(
        0,
        "Bare Rod",
        "🎣",
        window_bonus=0.0,
        bite_speed=1.00,
        rarity_pull=1.00,
        escape_resist=0.00,
        premature_grace=0.00,
        price=0,
    ),
    Rod(
        1,
        "Bronze Rod",
        "🥉",
        window_bonus=0.4,
        bite_speed=0.95,
        rarity_pull=1.10,
        escape_resist=0.10,
        premature_grace=0.15,
        price=250,
    ),
    Rod(
        2,
        "Silver Rod",
        "🥈",
        window_bonus=0.8,
        bite_speed=0.88,
        rarity_pull=1.25,
        escape_resist=0.22,
        premature_grace=0.30,
        price=750,
    ),
    Rod(
        3,
        "Gold Rod",
        "🥇",
        window_bonus=1.2,
        bite_speed=0.80,
        rarity_pull=1.45,
        escape_resist=0.35,
        premature_grace=0.45,
        price=2000,
    ),
    Rod(
        4,
        "Diamond Rod",
        "💎",
        window_bonus=1.7,
        bite_speed=0.70,
        rarity_pull=1.70,
        escape_resist=0.50,
        premature_grace=0.60,
        price=5000,
    ),
)

MAX_TIER = len(ROD_LADDER) - 1
STARTER = ROD_LADDER[0]


def rod_for_tier(tier: int) -> Rod:
    """The :class:`Rod` for *tier*, clamped into the ladder (unknown → starter)."""
    if tier < 0:
        return STARTER
    if tier > MAX_TIER:
        return ROD_LADDER[MAX_TIER]
    return ROD_LADDER[tier]


def next_rod(tier: int) -> Rod | None:
    """The next rod up from *tier*, or ``None`` if already at the top."""
    if tier >= MAX_TIER:
        return None
    return ROD_LADDER[tier + 1]
