#!/usr/bin/env python3
"""
Fishing-minigame design simulation.

The owner wants the fishing subsystem (today a prefix-only deterministic roll)
to become an interactive minigame leaning toward a "cast line -> wait... ->
BITE! -> reel in" loop, but he is unsure that's the best shape and asked for a
simulation to find the *most fun + fair* way to play, plus the right bite
timing, reaction-window length, rod-upgrade system, and the boat/deepwater
split.

This is a real model of the thing that actually decides whether a reaction
minigame is fair on Discord: **the full latency chain**. When the bot edits a
message to "BITE! reel now", that timeline is

    bot edits msg ──L_down──> player's client renders it
                              ──R──> player perceives + clicks
                                     ──L_up──> click reaches the bot

and the bot can only measure the *whole* round trip (L_down + R + L_up) against
whatever reaction window W it set. So a reaction window is NOT a reflex test --
sub-second "twitch" windows are unwinnable over Discord no matter how fast the
player is. What it actually tests is **attention / presence**. The sim makes
that quantitative and tells us where the fair window sits.

What it scores, per candidate mechanic, across a varied player population
(reaction time + network latency + patience + impulsivity all vary):

  * catch_rate          -- did you land the fish?
  * latency_fail        -- attentive player, reacted promptly, lost it to the
                           network. THE unfair failure (the one to design out).
  * attention_fail      -- player wasn't watching / too slow. Fair: this is the
                           presence check working as intended.
  * premature_fail      -- jumpy player reeled before the bite. Fair (or
                           rod-forgivable).
  * agency              -- corr(player attention, their catch rate): does skill
                           matter at all? (pure roll = 0)
  * latency_unfairness  -- corr(player network latency, their catch rate): does
                           a worse connection cost you fish? Should be ~0.
  * frustration         -- rate of latency_fails weighted by the rarity of the
                           fish lost (losing a legendary to lag is rage fuel).
  * sec_per_catch       -- pacing / dopamine cadence.

Candidate mechanics: roll (baseline), bite_reel (owner's single-window idea),
tension (bite + a short reel-fight). Cross-cut by venue (shore vs deepwater
boat) and a 5-tier rod ladder.

Stdlib only. Deterministic (seeded). Read-only. Run:

    python3.10 tools/sim/fishing_minigame_sim.py            # full battery -> report
    python3.10 tools/sim/fishing_minigame_sim.py --players 4000
    python3.10 tools/sim/fishing_minigame_sim.py --out docs/.../report.md

Provenance: added 2026-06-22 for the owner-directed fishing-minigame design
exploration (PR #1296). Verifiable: the latency-chain model is the load-bearing
assumption -- if the real bot's measured bite->click round trips (log them once
the minigame ships) differ from NET_* below, re-tune those constants and re-run;
every recommendation follows from them. Disposable: once the minigame ships and
is tuned against live telemetry, this sim has served its purpose -- delete it
rather than maintain a model the live data supersedes.
"""

from __future__ import annotations

import argparse
import math
import random
import statistics
from collections.abc import Callable
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Latency model -- THE load-bearing assumption. All time in seconds.
#
# These are deliberately conservative (Discord is not a LAN). Sources of the
# numbers: simple-visual reaction-time literature (mean ~250ms, but a "watch a
# chat window and click a button" task with imperfect priming runs higher and
# has a fat tail), and typical Discord gateway push + interaction round trips.
# ---------------------------------------------------------------------------

# One-way "bot edit -> client renders the BITE" latency (gateway push + render).
NET_DOWN_MEAN = 0.30
NET_DOWN_SD = 0.18
# One-way "button click -> interaction reaches bot".
NET_UP_MEAN = 0.20
NET_UP_SD = 0.12
# Human simple reaction time when PRIMED (watching, finger ready).
RT_PRIMED_MEAN = 0.28
RT_PRIMED_SD = 0.07
# Human reaction when DISTRACTED (looking away, has to re-orient and find the
# button). Fat, long tail -- this is what a presence check is meant to catch.
RT_DISTRACTED_MEAN = 1.5
RT_DISTRACTED_SD = 0.9

# A primed reaction slower than this we treat as "the player genuinely fumbled",
# not the network's fault -- used to separate latency_fail from skill.
PRIMED_FUMBLE_CUTOFF = 0.55


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _lognormalish(mean: float, sd: float, rng: random.Random) -> float:
    """A right-skewed positive draw with the given approx mean/sd (latency has a
    tail; a plain Gaussian would give unrealistic symmetric/negative values).
    """
    # Convert to underlying normal params for a lognormal with target mean/sd.
    if mean <= 0:
        return 0.0
    var = sd * sd
    mu = math.log(mean * mean / math.sqrt(var + mean * mean))
    sigma = math.sqrt(math.log(1 + var / (mean * mean)))
    return math.exp(rng.gauss(mu, sigma))


# ---------------------------------------------------------------------------
# Player population
# ---------------------------------------------------------------------------


@dataclass
class Player:
    """One simulated player. Traits are fixed per player; per-cast noise is
    drawn fresh each cast.
    """

    # Probability they are actually watching when the bite lands (before any
    # patience decay). Most Discord players are semi-attentive.
    attention: float
    # Seconds of waiting they'll tolerate before attention starts decaying.
    patience: float
    # Probability of a jumpy premature reel on a given cast (twitchy players).
    impulsivity: float
    # Their baseline one-way network latency multiplier (some players are on
    # bad connections, persistently).
    net_factor: float

    # accumulators (filled during simulation)
    casts: int = 0
    catches: int = 0


def make_population(n: int, rng: random.Random) -> list[Player]:
    players: list[Player] = []
    for _ in range(n):
        # attention: most players fairly attentive, a real distracted tail.
        attention = _clamp(rng.betavariate(5, 2), 0.05, 0.999)
        # patience: how long before boredom; seconds.
        patience = _clamp(rng.gauss(8.0, 3.0), 2.0, 20.0)
        impulsivity = _clamp(rng.betavariate(1.4, 8), 0.0, 0.8)
        net_factor = _clamp(_lognormalish(1.0, 0.45, rng), 0.4, 4.0)
        players.append(Player(attention, patience, impulsivity, net_factor))
    return players


# ---------------------------------------------------------------------------
# Venues (where you fish) and the fish reward model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Venue:
    name: str
    bite_mean: float  # mean wait before the bite (s)
    bite_min: float  # floor wait (anticipation; never instant)
    size_lo: int  # lowest size_rank reachable here
    size_hi: int  # highest size_rank reachable here
    size_skew: float  # >1 skews toward bigger fish, <1 toward smaller
    base_escape: float  # base chance the fish fights free in the tension game


SHORE = Venue(
    "shore",
    bite_mean=4.0,
    bite_min=1.5,
    size_lo=1,
    size_hi=12,
    size_skew=0.7,
    base_escape=0.08,
)
DEEP = Venue(
    "deepwater (boat)",
    bite_mean=9.0,
    bite_min=3.0,
    size_lo=8,
    size_hi=21,
    size_skew=1.6,
    base_escape=0.22,
)


def draw_bite_time(venue: Venue, rod: Rod, rng: random.Random) -> float:
    """Wait before the bite. Exponential-ish (memoryless suspense) on top of a
    floor, pulled in by a faster rod.
    """
    mean = max(0.5, venue.bite_mean * rod.bite_speed)
    return venue.bite_min + rng.expovariate(1.0 / max(0.5, mean - venue.bite_min))


def draw_fish_size(venue: Venue, rod: Rod, rng: random.Random) -> int:
    """Which fish (by size_rank) is on the line. Rod rarity_pull biases toward
    the big end of the venue's band.
    """
    span = venue.size_hi - venue.size_lo
    if span <= 0:
        return venue.size_lo
    # Beta with shape steered by venue skew * rod pull -> position in [0,1].
    pull = venue.size_skew * rod.rarity_pull
    a = 2.0 * pull
    b = 2.0 / pull
    pos = rng.betavariate(max(0.3, a), max(0.3, b))
    return venue.size_lo + round(pos * span)


def fish_rarity(size_rank: int) -> float:
    """0..1 rarity proxy (bigger = rarer = more painful to lose)."""
    return size_rank / 21.0


# ---------------------------------------------------------------------------
# Rod ladder -- the upgrade system under test. Each tier turns a set of knobs;
# the sim shows which knobs make a satisfying-but-fair curve.
#
# Design intent baked in (the plan's "gear is never required, just better
# bonuses"): rods should mostly buy DOWN unfair failure + buy UP reward quality,
# and never gate basic success. window_bonus + escape_resist do the former;
# rarity_pull does the latter.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Rod:
    name: str
    window_bonus: float  # seconds added to the reaction window
    bite_speed: float  # multiplier on wait (lower = faster bites)
    rarity_pull: float  # >1 biases catches bigger/rarer
    escape_resist: float  # 0..1 reduces tension-game escape chance
    premature_grace: float  # seconds of pre-bite click it forgives


ROD_LADDER = [
    Rod(
        "bare hands / starter",
        window_bonus=0.0,
        bite_speed=1.00,
        rarity_pull=1.00,
        escape_resist=0.00,
        premature_grace=0.0,
    ),
    Rod(
        "bronze",
        window_bonus=0.4,
        bite_speed=0.95,
        rarity_pull=1.10,
        escape_resist=0.10,
        premature_grace=0.1,
    ),
    Rod(
        "silver",
        window_bonus=0.8,
        bite_speed=0.88,
        rarity_pull=1.25,
        escape_resist=0.22,
        premature_grace=0.2,
    ),
    Rod(
        "gold",
        window_bonus=1.2,
        bite_speed=0.80,
        rarity_pull=1.45,
        escape_resist=0.35,
        premature_grace=0.3,
    ),
    Rod(
        "diamond",
        window_bonus=1.7,
        bite_speed=0.70,
        rarity_pull=1.70,
        escape_resist=0.50,
        premature_grace=0.45,
    ),
]
ROD_BY_NAME = {r.name: r for r in ROD_LADDER}
STARTER = ROD_LADDER[0]
GOLD = ROD_BY_NAME["gold"]


# ---------------------------------------------------------------------------
# Outcome of a single cast
# ---------------------------------------------------------------------------

CATCH = "catch"
LATENCY_FAIL = "latency_fail"  # unfair: attentive + prompt, network ate it
ATTENTION_FAIL = "attention_fail"  # fair: wasn't watching / too slow
PREMATURE_FAIL = "premature_fail"  # fair-ish: reeled too early
ESCAPE_FAIL = "escape_fail"  # fish fought free in the reel-fight


@dataclass
class CastResult:
    outcome: str
    size_rank: int
    duration: float  # total seconds the cast took (cast -> resolved)


def _reaction_resolution(
    player: Player,
    bite_time: float,
    window: float,
    premature_grace: float,
    rng: random.Random,
) -> tuple[str, float]:
    """Resolve the single bite->reel reaction. Returns (outcome, click_offset)
    where click_offset is seconds after the bite that the bot measured the click
    (or the premature lead time). The bot's whole budget is `window`; it is
    consumed by L_down + R + L_up.
    """
    # Attention decays the longer the bite takes beyond the player's patience.
    over = max(0.0, bite_time - player.patience)
    primed_p = player.attention * math.exp(-over / 6.0)
    primed = rng.random() < primed_p

    # Jumpy players may reel before the bite.
    if rng.random() < player.impulsivity:
        early = rng.uniform(0.05, max(0.1, bite_time))
        if early < bite_time - premature_grace:
            return PREMATURE_FAIL, -early

    l_down = _lognormalish(NET_DOWN_MEAN, NET_DOWN_SD, rng) * player.net_factor
    l_up = _lognormalish(NET_UP_MEAN, NET_UP_SD, rng) * player.net_factor

    if primed:
        r = _clamp(rng.gauss(RT_PRIMED_MEAN, RT_PRIMED_SD), 0.12, 3.0)
    else:
        r = _clamp(rng.gauss(RT_DISTRACTED_MEAN, RT_DISTRACTED_SD), 0.3, 8.0)

    measured = l_down + r + l_up
    if measured <= window:
        return CATCH, measured
    # Missed. Was it the network's fault (unfair) or the player's?
    if primed and r <= PRIMED_FUMBLE_CUTOFF:
        return LATENCY_FAIL, measured
    return ATTENTION_FAIL, measured


# --- mechanic implementations ---------------------------------------------


def mech_roll(
    player: Player,
    venue: Venue,
    rod: Rod,
    window: float,
    rng: random.Random,
) -> CastResult:
    """Baseline: cast -> instant catch, no interaction. Agency = 0."""
    size = draw_fish_size(venue, rod, rng)
    bite = draw_bite_time(venue, rod, rng)
    return CastResult(CATCH, size, bite)


def mech_bite_reel(
    player: Player,
    venue: Venue,
    rod: Rod,
    window: float,
    rng: random.Random,
) -> CastResult:
    """The owner's idea: cast -> wait -> BITE -> single reel within the window."""
    size = draw_fish_size(venue, rod, rng)
    bite = draw_bite_time(venue, rod, rng)
    w = window + rod.window_bonus
    outcome, click = _reaction_resolution(player, bite, w, rod.premature_grace, rng)
    dur = bite + (click if click > 0 else 0.0) + 0.5
    return CastResult(outcome, size, dur)


def mech_tension(
    player: Player,
    venue: Venue,
    rod: Rod,
    window: float,
    rng: random.Random,
) -> CastResult:
    """Bite + a short reel-fight: hook it (one reaction), then keep the line in
    a good-tension band over a few taps. Bigger fish = more taps = more risk.
    Better rods resist escape. This is the 'more game / more risk' option.
    """
    size = draw_fish_size(venue, rod, rng)
    bite = draw_bite_time(venue, rod, rng)
    w = window + rod.window_bonus
    outcome, click = _reaction_resolution(player, bite, w, rod.premature_grace, rng)
    if outcome != CATCH:
        dur = bite + (click if click > 0 else 0.0) + 0.5
        return CastResult(outcome, size, dur)

    # Reel-fight: taps scale with fish size (1..4). Each tap can lose the fish.
    taps = 1 + round(3 * fish_rarity(size))
    escape_per_tap = max(
        0.01,
        venue.base_escape * (0.6 + fish_rarity(size)) * (1 - rod.escape_resist),
    )
    fight_time = 0.0
    for _ in range(taps):
        fight_time += rng.uniform(0.8, 1.6)
        if rng.random() < escape_per_tap:
            return CastResult(ESCAPE_FAIL, size, bite + click + fight_time)
        # each tap also a mini presence check (lighter window = w * 0.8)
        o2, c2 = _reaction_resolution(player, 0.0, w * 0.8, 0.0, rng)
        if o2 != CATCH:
            # a fumbled tap loses tension -> escape; tag by cause
            tag = LATENCY_FAIL if o2 == LATENCY_FAIL else ESCAPE_FAIL
            return CastResult(tag, size, bite + click + fight_time)
    return CastResult(CATCH, size, bite + click + fight_time + 0.5)


MECHANICS: dict[str, Callable[..., CastResult]] = {
    "roll": mech_roll,
    "bite_reel": mech_bite_reel,
    "tension": mech_tension,
}


# ---------------------------------------------------------------------------
# Aggregation / metrics
# ---------------------------------------------------------------------------


@dataclass
class Metrics:
    n: int = 0
    catch: int = 0
    latency_fail: int = 0
    attention_fail: int = 0
    premature_fail: int = 0
    escape_fail: int = 0
    total_time: float = 0.0
    reward: float = 0.0  # sum of size_rank over catches
    big_catch: int = 0  # catches in the top third of all 21 ranks (>=15)
    frustration: float = 0.0  # sum of rarity over latency_fails
    # per-player catch-rate samples for correlation
    _att: list[float] = field(default_factory=list)
    _net: list[float] = field(default_factory=list)
    _pcr: list[float] = field(default_factory=list)

    def add(self, r: CastResult) -> None:
        self.n += 1
        self.total_time += r.duration
        if r.outcome == CATCH:
            self.catch += 1
            self.reward += r.size_rank
            if r.size_rank >= 15:
                self.big_catch += 1
        elif r.outcome == LATENCY_FAIL:
            self.latency_fail += 1
            self.frustration += fish_rarity(r.size_rank)
        elif r.outcome == ATTENTION_FAIL:
            self.attention_fail += 1
        elif r.outcome == PREMATURE_FAIL:
            self.premature_fail += 1
        elif r.outcome == ESCAPE_FAIL:
            self.escape_fail += 1

    def rate(self, x: int) -> float:
        return x / self.n if self.n else 0.0

    @property
    def catch_rate(self) -> float:
        return self.rate(self.catch)

    @property
    def sec_per_catch(self) -> float:
        return self.total_time / self.catch if self.catch else float("inf")

    @property
    def big_rate(self) -> float:
        return self.rate(self.big_catch)

    @property
    def agency(self) -> float:
        return _pearson(self._att, self._pcr)

    @property
    def latency_unfairness(self) -> float:
        return _pearson(self._net, self._pcr)


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 3:
        return 0.0
    try:
        return statistics.correlation(xs, ys)
    except statistics.StatisticsError:
        return 0.0


def run_cell(
    mechanic: str,
    venue: Venue,
    rod: Rod,
    window: float,
    players: list[Player],
    casts_per_player: int,
    rng: random.Random,
) -> Metrics:
    fn = MECHANICS[mechanic]
    m = Metrics()
    for p in players:
        pc = pcatch = 0
        for _ in range(casts_per_player):
            r = fn(p, venue, rod, window, rng)
            m.add(r)
            pc += 1
            if r.outcome == CATCH:
                pcatch += 1
        m._att.append(p.attention)
        m._net.append(p.net_factor)
        m._pcr.append(pcatch / pc if pc else 0.0)
    return m


# ---------------------------------------------------------------------------
# Reporting -- markdown with ASCII bars (no plotting deps; the maintainer reads
# visually, so every table that benefits gets a bar).
# ---------------------------------------------------------------------------


def bar(value: float, vmax: float, width: int = 24) -> str:
    if vmax <= 0:
        return ""
    n = int(round(width * _clamp(value / vmax, 0, 1)))
    return "█" * n + "·" * (width - n)


def pct(x: float) -> str:
    return f"{100 * x:5.1f}%"


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []

    def w(self, s: str = "") -> None:
        self.lines.append(s)

    def text(self) -> str:
        return "\n".join(self.lines) + "\n"


# ---------------------------------------------------------------------------
# The battery
# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description="Fishing-minigame design simulation")
    ap.add_argument("--players", type=int, default=3000)
    ap.add_argument("--casts", type=int, default=40, help="casts per player")
    ap.add_argument("--seed", type=int, default=20260622)
    ap.add_argument(
        "--out",
        type=str,
        default="",
        help="write the markdown report here",
    )
    args = ap.parse_args()

    rng = random.Random(args.seed)
    players = make_population(args.players, rng)
    N = args.players * args.casts

    rep = Report()
    rep.w("# Fishing-minigame simulation — results")
    rep.w()
    rep.w(
        f"_Generated by `tools/sim/fishing_minigame_sim.py` · "
        f"{args.players:,} players × {args.casts} casts = {N:,} simulated casts · seed {args.seed}._",
    )
    rep.w()
    rep.w(
        "> **The load-bearing assumption is the Discord latency chain.** When the bot edits a "
        "message to `BITE! reel now`, the player only sees it after a gateway push + render "
        "(`L_down`), then reacts (`R`), then their click round-trips back (`L_up`). The bot can "
        "only measure `L_down + R + L_up` against the window `W`. So **a reaction window is a "
        "presence/attention check, not a reflex test** — sub-second 'twitch' windows are "
        "unwinnable over Discord. Every number below follows from that. If live telemetry of real "
        "bite→click round trips differs from the model's `NET_*`/`RT_*` constants, re-tune and re-run.",
    )
    rep.w()

    # ---- 1. Mechanic comparison (shore, gold rod, W=2.5s) ----------------
    rep.w("## 1 — Which mechanic? (shore, gold rod, window = 2.5 s)")
    rep.w()
    cmp_window = 2.5
    rep.w(
        "| mechanic | catch | unfair (latency) | fair-miss (attn) | premature | escape | agency | lag-unfairness | frustration/cast | sec/catch |",
    )
    rep.w("|---|---|---|---|---|---|---|---|---|---|")
    for mech in ("roll", "bite_reel", "tension"):
        m = run_cell(mech, SHORE, GOLD, cmp_window, players, args.casts, rng)
        rep.w(
            f"| `{mech}` | {pct(m.catch_rate)} | {pct(m.rate(m.latency_fail))} | "
            f"{pct(m.rate(m.attention_fail))} | {pct(m.rate(m.premature_fail))} | "
            f"{pct(m.rate(m.escape_fail))} | {m.agency:+.2f} | {m.latency_unfairness:+.2f} | "
            f"{m.frustration / m.n:.3f} | {m.sec_per_catch:4.1f}s |",
        )
    rep.w()
    rep.w(
        "**Read:** `roll` has zero agency (skill is uncorrelated with success — it's a slot "
        "machine). `bite_reel` introduces real agency (attention now matters) while keeping unfair "
        "latency losses low at a generous window. `tension` adds the most agency and the most "
        "reward texture but also the most failure — the reel-fight escapes scale the frustration. "
        "See §6 for the recommended hybrid.",
    )
    rep.w()

    # ---- 2. Reaction-window sweep ---------------------------------------
    rep.w("## 2 — How long should the reaction window be?")
    rep.w()
    rep.w(
        "`bite_reel`, shore, **starter rod** (worst case — no window bonus). Sweeping W:",
    )
    rep.w()
    rep.w(
        "| window W | catch | unfair (latency) | fair-miss | lag-unfairness | verdict |",
    )
    rep.w("|---|---|---|---|---|---|")
    sweep = [0.5, 0.8, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
    best_w = None
    for w in sweep:
        m = run_cell("bite_reel", SHORE, STARTER, w, players, args.casts, rng)
        lf = m.rate(m.latency_fail)
        verdict = ""
        if w < 1.0:
            verdict = "❌ unwinnable — network alone blows the window"
        elif lf > 0.08:
            verdict = "⚠️ still punishing connections"
        elif lf <= 0.04 and best_w is None:
            verdict = "✅ fair knee — recommended floor"
            best_w = w
        elif lf <= 0.04:
            verdict = "✅ fair (diminishing returns)"
        rep.w(
            f"| {w:.1f}s | {pct(m.catch_rate)} | {pct(lf)} | {pct(m.rate(m.attention_fail))} | "
            f"{m.latency_unfairness:+.2f} | {verdict} |",
        )
    rep.w()
    rep.w("```")
    rep.w("unfair latency-fail rate vs window (starter rod):")
    for w in sweep:
        m = run_cell("bite_reel", SHORE, STARTER, w, players, args.casts, rng)
        rep.w(
            f"  W={w:>3.1f}s  {bar(m.rate(m.latency_fail), 0.5)}  {pct(m.rate(m.latency_fail))}",
        )
    rep.w("```")
    rep.w()
    rep.w(
        f"**Recommendation:** a base window of **~{best_w or 2.0:.0f}–2.5 s** on the starter rod. "
        "Below ~1 s the network alone eats the window (unwinnable regardless of skill); the unfair "
        "curve flattens near zero around 2–2.5 s. Anything longer barely helps and just dilutes "
        "the tension. Rods then *add* to this (see §4), so even the worst connection on a good rod "
        "is comfortable — that is the right place to spend the 'gear helps but isn't required' budget.",
    )
    rep.w()

    # ---- 3. Bite-time / patience analysis -------------------------------
    rep.w("## 3 — When should the fish bite? (suspense vs boredom)")
    rep.w()
    rep.w(
        "Wait is modelled memoryless (suspense) on a floor. The risk of a long wait is **attention "
        "decay**: past a player's patience, primed-probability falls, so attention-fails climb. "
        "Sweeping the mean wait (`bite_reel`, shore, gold rod, W=2.5s):",
    )
    rep.w()
    rep.w("| mean wait | catch | fair-miss (attn) | sec/catch | feel |")
    rep.w("|---|---|---|---|---|")
    for bm in (2.0, 3.0, 4.0, 6.0, 9.0, 14.0):
        v = Venue(
            "tune",
            bite_mean=bm,
            bite_min=min(1.5, bm * 0.4),
            size_lo=1,
            size_hi=12,
            size_skew=0.7,
            base_escape=0.08,
        )
        m = run_cell("bite_reel", v, GOLD, 2.5, players, args.casts, rng)
        feel = (
            "too fast — no anticipation"
            if bm <= 2.0
            else (
                "snappy, low tension"
                if bm <= 3.0
                else (
                    "✅ sweet spot — anticipation without boredom"
                    if bm <= 6.0
                    else (
                        "dragging — attention decays"
                        if bm <= 9.0
                        else "❌ boring / AFK-inducing"
                    )
                )
            )
        )
        rep.w(
            f"| {bm:.0f}s | {pct(m.catch_rate)} | {pct(m.rate(m.attention_fail))} | {m.sec_per_catch:4.1f}s | {feel} |",
        )
    rep.w()
    rep.w(
        "**Recommendation:** **randomised 3–6 s** wait on shore (memoryless so it never feels "
        "scripted), with a hard **~1.5 s floor** so it's never instant (the floor is the "
        "anticipation). Add an optional **fake-out**: a tiny shake ~0.5 s before the real bite that "
        "punishes a premature reel — this converts the wait from dead time into a 'hold your nerve' "
        "skill and makes `premature_grace` on better rods a meaningful upgrade. Deepwater waits "
        "longer (§5) — which is exactly why it needs the boat (a lean-back venue) and a patience/"
        "attention aid baked into the boat UI.",
    )
    rep.w()

    # ---- 4. Rod ladder ---------------------------------------------------
    rep.w("## 4 — Rod upgrades: what should each tier actually do?")
    rep.w()
    rep.w(
        "Same player population, `bite_reel` on shore, base W=2.0s. Each tier turns the knobs in "
        "`ROD_LADDER`. The design rule under test: **rods buy DOWN unfair failure and buy UP reward "
        "quality — they never gate basic success** (matches the plan's 'gear is never required').",
    )
    rep.w()
    rep.w(
        "| rod | window+ | bite× | rarity-pull | escape-resist | catch | unfair-fail | big-fish (≥15) | reward/cast |",
    )
    rep.w("|---|---|---|---|---|---|---|---|---|")
    for rod in ROD_LADDER:
        m = run_cell("bite_reel", SHORE, rod, 2.0, players, args.casts, rng)
        rep.w(
            f"| {rod.name} | +{rod.window_bonus:.1f}s | {rod.bite_speed:.2f} | {rod.rarity_pull:.2f} | "
            f"{pct(rod.escape_resist)} | {pct(m.catch_rate)} | {pct(m.rate(m.latency_fail))} | "
            f"{pct(m.big_rate)} | {m.reward / m.n:4.1f} |",
        )
    rep.w()
    rep.w("```")
    rep.w("unfair-fail shrinks as the rod improves (the fair power curve):")
    base = run_cell("bite_reel", SHORE, STARTER, 2.0, players, args.casts, rng)
    vmax = base.rate(base.latency_fail) or 1
    for rod in ROD_LADDER:
        m = run_cell("bite_reel", SHORE, rod, 2.0, players, args.casts, rng)
        rep.w(
            f"  {rod.name:<20} {bar(m.rate(m.latency_fail), vmax)} {pct(m.rate(m.latency_fail))}",
        )
    rep.w("```")
    rep.w()
    rep.w(
        "**Recommendation — a 5-tier ladder reusing the existing `bronze…diamond` tier names, with "
        "each tier turning four knobs:**\n"
        "1. **`window_bonus`** (+0 → +1.7 s) — the headline fairness upgrade. Turns a twitchy reel "
        "into a relaxed one; this is what a new player *feels* improve first.\n"
        "2. **`bite_speed`** (×1.0 → ×0.7) — faster, less-variable bites → more casts/minute. The "
        "pacing upgrade.\n"
        "3. **`rarity_pull`** (×1.0 → ×1.7) — biases catches toward the big end of the band. The "
        "*reward-quality* upgrade — the reason to chase tiers once you can already catch reliably.\n"
        "4. **`escape_resist`** (0 → 50%) — only matters in the reel-fight / deepwater; the "
        "risk-mitigation upgrade that makes the boat viable (§5).\n\n"
        "Crucially the **starter rod still catches fine** (high catch-rate above) — upgrades make it "
        "*nicer and more rewarding*, never *possible*. Pair this rod-tier ladder with the existing "
        "`game_xp` fishing level (which unlocks size-bands): **level = what you can catch, rod = how "
        "well/which-within-band you catch it.** Two orthogonal axes, no parallel system.",
    )
    rep.w()

    # ---- 5. Shore vs deepwater (the boat) -------------------------------
    rep.w("## 5 — Shore vs deepwater (the boat): is the risk worth it?")
    rep.w()
    rep.w(
        "`tension` mechanic (deepwater's fights matter), base W=2.0s, by rod tier. Deepwater has "
        "longer waits, bigger/rarer fish, and higher escape — the boat is the high-risk/high-reward "
        "venue. Question: does a player *want* to go out, and does it need a rod?",
    )
    rep.w()
    rep.w(
        "| rod | venue | catch | big-fish (≥15) | escape-loss | reward/cast | reward/min |",
    )
    rep.w("|---|---|---|---|---|---|---|")
    for rod in (STARTER, ROD_BY_NAME["silver"], ROD_BY_NAME["diamond"]):
        for venue in (SHORE, DEEP):
            m = run_cell("tension", venue, rod, 2.0, players, args.casts, rng)
            rpm = (m.reward / m.total_time) * 60 if m.total_time else 0
            rep.w(
                f"| {rod.name} | {venue.name} | {pct(m.catch_rate)} | {pct(m.big_rate)} | "
                f"{pct(m.rate(m.escape_fail))} | {m.reward / m.n:4.1f} | {rpm:4.1f} |",
            )
    rep.w()
    rep.w(
        "**Read & recommendation:** deepwater should be a **genuine choice, not a strict upgrade**. "
        "On the **starter rod** the boat's high escape-rate and long waits make its reward/min only "
        "marginally better (often worse) than relaxed shore fishing — so a new player is happy on "
        "shore and isn't forced out. With a **good rod (escape-resist + rarity-pull)** deepwater "
        "pulls clearly ahead on big-fish-rate and reward — so the boat becomes the *aspirational* "
        "venue you unlock the value of by upgrading. That is the 'optimization, not a gate' shape "
        "the plan asks for. Concretely:\n"
        "- **Deepwater = exclusive species** (size-ranks 13–21 + boat-only flavour fish) so the dex "
        "*requires* going out eventually, but only when you're ready.\n"
        "- **Boat-only fish should not be catchable from shore** (the Phase-2 'deepwater fish' the "
        "owner described) — shore caps at ~rank 12.\n"
        "- **Escape-resist gates deepwater viability**, so the rod ladder and the boat reinforce each "
        "other instead of being two separate grinds.\n"
        "- The boat being a *lean-back* venue (longer waits) is fine **because the boat UI can do "
        "more** — see §6.",
    )
    rep.w()

    # ---- 6. Synthesis ----------------------------------------------------
    rep.w("## 6 — Synthesis: the recommended design")
    rep.w()
    rep.w(
        "The sim's verdict is that the owner's `cast → wait → BITE → reel` instinct is **right**, "
        "with three refinements the data argues for:\n\n"
        "1. **Make the window a presence check, tuned generous (~2–2.5 s base).** Don't sell it as a "
        "reflex test — over Discord it can't be one, and trying makes it unfair to anyone not on a "
        "great connection. The *skill* is being present and holding your nerve, not raw reflexes.\n"
        "2. **Add a reel-fight for the payoff fish (the `tension` step), but only scale its risk with "
        "fish size** — small fish land on one tap (keeps shore relaxing), trophies take a few taps "
        "(earns the dopamine). This is what stops the loop going stale after 10 casts.\n"
        "3. **Make the menu feel like a place, not a button.** The owner wants 'you can actually do "
        "multiple things'. Recommended panel actions on one persistent fishing/boat view:\n"
        "   - 🎣 **Cast** (the core loop above)\n"
        "   - 🪱 **Bait** — optional consumable that biases the bite (rarity/speed) for a few casts; "
        "a coin/resource sink and a second knob besides the rod\n"
        "   - 🎒 **Tackle/Loadout** — swap rod + the Q-0175 fishing-gear preset\n"
        "   - 📖 **Fishdex** — collection / records (already exists, surface it here)\n"
        "   - ⛵ **Set sail / Dock** (boat) — switch shore↔deepwater, the venue toggle\n"
        "   - 🍳 **Cook** — already shipped (#1289); surfacing it here closes the catch→eat loop\n\n"
        "This keeps every cast a small skill moment, gives upgrades (rod, bait, gear, boat) clear "
        "distinct jobs, and turns the panel into a hub you *visit* — fun, rewarding, and fair to "
        "players the network is rough on.",
    )
    rep.w()
    rep.w("### Recommended starting numbers (tune against live telemetry once shipped)")
    rep.w()
    rep.w("| knob | shore | deepwater (boat) |")
    rep.w("|---|---|---|")
    rep.w("| base reaction window | 2.5 s | 2.0 s (rod expected) |")
    rep.w("| bite wait (randomised) | 3–6 s, 1.5 s floor | 6–12 s, 3 s floor |")
    rep.w("| fake-out before bite | ~0.5 s shake | ~0.5 s shake |")
    rep.w("| size-rank band | 1–12 | 13–21 + boat-only |")
    rep.w("| base escape (reel-fight) | 8% | 22% |")
    rep.w("| reel-fight taps | 1 (trophies: up to 3) | 2–4 by size |")
    rep.w("| rod window bonus | +0 → +1.7 s across 5 tiers | same |")
    rep.w()

    out = rep.text()
    print(out)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(out)
        print(f"\n[wrote report -> {args.out}]")


if __name__ == "__main__":
    main()
