#!/usr/bin/env python3.10
"""Mining economy balance simulator (design tool, not runtime).

Why this exists
---------------
The mining grid's first real grid-``Mine`` is now live (#1281/#1282) and the
owner's read is that **rewards are too large and too frequent** — he asked for a
*simulation that finds a balanced way to configure the game so it stays fun and
playable for everyone* (the same "simulation-sane numbers" discipline the gear
sets and the creature game used — ``tools/game_sim/creature_battle_sim.py``,
``docs/planning/gear-set-numbers-2026-06-11.md``).

This script models the mining **faucet** (coins + XP earned per dig and per
active hour) for a spread of player profiles, measures it against the rest of
the bot's *gated* economy, and then **sweeps candidate configurations** to find
one that is rewarding but in line — i.e. an active mining session pays on the
order of a daily claim, the gap between a fresh player and a fully-geared
veteran stays bounded ("playable for everyone"), and lucky strikes feel special
rather than constant.

What it models (the real game, as of #1282 — see the source refs inline)
------------------------------------------------------------------------
One dig yields ``(ore, amount)`` where::

    amount = randint(1, BASE_MAX) * tool_multiplier * cell_richness

- ``BASE_MAX`` = 3                        (``utils/mining/rewards.py:90``)
- ``tool_multiplier`` ∈ {1,2,3,4,5} for none/pickaxe/iron/gold/diamond
  (``rewards.mine_multiplier`` = ``1 + mining_power // 2``;
   powers 0/2/4/6/8 in ``utils/equipment.py``)
- ``cell_richness`` per feature: NORMAL 1.0, RICH 2.0, BARREN 0.5, TREASURE 3.0
  with feature weights NORMAL 60 / RICH 20 / BARREN 15 / TREASURE 5
  (``utils/mining/grid.py``)
- the ore is drawn from a **depth-weighted** table (deeper = richer ores)
  (``rewards.ore_weights_for_depth``); ore sells for
  stone 1 / bronze 2 / iron 3 / silver 4 / gold 6 / diamond 12
  (``utils/mining/items.py`` ``RESOURCE`` values, sold via ``market.sell_price``)
- **there is no cooldown, no energy, no rate limit** on digging (verified — the
  faucet is throttled only by how fast a human clicks).

Economy benchmark (what "balanced" is measured against)
-------------------------------------------------------
``!daily`` pays a weighted 500–5000 once / 24h (mean ≈ 1,692) and ``!work`` pays
~60 coins once / hour (``services/economy_helpers.py``). So the gated economy
gives a casual player on the order of **~1,700 coins/day**. A mining faucet that
lets someone out-earn that in minutes is the imbalance this tool quantifies.

It is **stdlib-only, deterministic** (``--seed``) and prints a verdict with
PASS/WARN flags plus a **recommended config**. Nothing here is imported by the
bot; it informs a design doc, and the owner decides which knobs to apply.

Run::

    python3.10 tools/game_sim/mining_economy_sim.py
    python3.10 tools/game_sim/mining_economy_sim.py --trials 8000 --seed 7

Provenance: added 2026-06-22 (owner request — "create/run a simulation that
finds the most balanced way for the mining game"). Disposable design tool —
delete once the numbers are pinned into the mining subsystem, or if the approach
is dropped. **Unverified:** confirm its faucet numbers against a live play
session a few times before trusting the recommendation as gospel.
"""

from __future__ import annotations

import argparse
import random
import statistics
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# The real game's constants (mirrored, with source refs — see module docstring).
# A parity test (tests/unit/tools/test_mining_economy_sim.py) asserts these match
# the live source so this tool can't silently drift from the bot.
# ---------------------------------------------------------------------------

# Ore sell value (coins per unit) — utils/mining/items.py RESOURCE values.
ORE_VALUE: dict[str, int] = {
    "stone": 1,
    "bronze": 2,
    "iron": 3,
    "silver": 4,
    "gold": 6,
    "diamond": 12,
}

# Surface (depth 0) ore selection weights — utils/mining/rewards.py ORE_WEIGHTS.
SURFACE_ORE_WEIGHTS: dict[str, float] = {
    "stone": 3.0,
    "bronze": 2.5,
    "iron": 2.0,
    "silver": 1.5,
    "gold": 1.0,
    "diamond": 0.5,
}

# Tool multipliers by tier — rewards.mine_multiplier (1 + power*0.0625, the
# 2026-06-22 rebalance; powers 0/2/4/6/8 → ×1/1.125/1.25/1.375/1.5).
TOOL_MULT: dict[str, float] = {
    "none": 1.0,
    "pickaxe": 1.125,
    "iron": 1.25,
    "gold": 1.375,
    "diamond": 1.5,
}

# Base ore per dig — rewards.BASE_ROLL_MAX (rebalanced 3 → 2 on 2026-06-22).
BASE_ROLL_MAX = 2

# Energy throttle — the owner's chosen frequency brake (utils/mining/energy.py):
# +1 energy / 10s = 360 digs / active hour. Operationally identical to a 10s
# dig interval for the sustained faucet, so the sim models it as that cooldown.
ENERGY_REGEN_PER_HOUR = 360
ENERGY_THROTTLE_S = 3600 / ENERGY_REGEN_PER_HOUR  # = 10.0s effective interval

MAX_DEPTH = 3  # utils/mining/world.py — SURFACE/CAVERN/DEEP/MAGMA (0..3)


def ore_weights_for_depth(depth: int) -> dict[str, float]:
    """Mirror of ``rewards.ore_weights_for_depth`` — deeper = richer odds."""
    d = max(0, depth)
    w = SURFACE_ORE_WEIGHTS
    return {
        "stone": max(0.5, w["stone"] - d),
        "bronze": max(0.5, w["bronze"] - 0.5 * d),
        "iron": w["iron"] + 0.5 * d,
        "silver": w["silver"] + 0.5 * d,
        "gold": w["gold"] + 0.5 * d,
        "diamond": w["diamond"] + 0.5 * d,
    }


# ---------------------------------------------------------------------------
# Economy benchmark — services/economy_helpers.py (the gated faucets).
# ---------------------------------------------------------------------------

# _DAILY_TIERS (label, min, max, weight). Expected value ≈ 1,692 coins/24h.
_DAILY_TIERS: list[tuple[int, int, int]] = [
    (500, 999, 45),
    (1000, 1999, 25),
    (2000, 2999, 15),
    (3000, 3999, 8),
    (4000, 4999, 5),
    (5000, 5000, 2),
]


def expected_daily() -> float:
    """Mean coins from one ``!daily`` claim (the casual player's daily faucet)."""
    total_w = sum(w for *_, w in _DAILY_TIERS)
    return sum((lo + hi) / 2 * w for lo, hi, w in _DAILY_TIERS) / total_w


WORK_COINS_PER_HOUR = 62.5  # tier-1 work pay ~50-75, once/hour (economy_helpers)


# ---------------------------------------------------------------------------
# Tunable configuration — the knobs the sweep searches. CURRENT = the live game.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MiningConfig:
    """A candidate mining configuration. ``CURRENT`` mirrors the live game."""

    name: str
    base_max: int  # amount = randint(1, base_max) before multipliers
    # per-tier tool multiplier applied to the base amount
    tool_mult: dict[str, float]
    # cell feature weights (NORMAL, RICH, BARREN, TREASURE) and their richness
    feature_weights: tuple[float, float, float, float]
    feature_richness: tuple[float, float, float, float]
    # the frequency brake — seconds a dig is locked out (0 = no cooldown today)
    dig_cooldown_s: float
    # ore sell values + depth weighting are gear-coupled → held fixed across the
    # sweep (changing them would desync the gear economy); kept here for clarity.
    ore_value: dict[str, int] = field(default_factory=lambda: dict(ORE_VALUE))

    def bonanza_rate(self) -> float:
        """Share of cells that are a RICH or TREASURE 'lucky strike'."""
        n, r, b, t = self.feature_weights
        return (r + t) / (n + r + b + t)


# The faucet BEFORE the 2026-06-22 rebalance — the imbalance the sim diagnosed
# (uncapped clicking, steep ×1-5 tools, 25% bonanza). Kept as the documented
# "before" so the diagnosis section stays reproducible.
PRE_REBALANCE = MiningConfig(
    name="PRE-REBALANCE (live #1282, the bug)",
    base_max=3,
    tool_mult={"none": 1.0, "pickaxe": 2.0, "iron": 3.0, "gold": 4.0, "diamond": 5.0},
    feature_weights=(60.0, 20.0, 15.0, 5.0),
    feature_richness=(1.0, 2.0, 0.5, 3.0),
    dig_cooldown_s=0.0,
)

# The CURRENT live config — the applied rebalance (#1286): smaller base roll,
# flat tool curve, 12% bonanza, AND the energy throttle (modeled as its ~10s
# effective dig interval). This is what the bot now does; the parity test pins
# every mirror to the live source.
CURRENT = MiningConfig(
    name="CURRENT (live, rebalanced + energy throttle)",
    base_max=BASE_ROLL_MAX,
    tool_mult=dict(TOOL_MULT),
    feature_weights=(70.0, 10.0, 18.0, 2.0),
    feature_richness=(1.0, 2.0, 0.5, 2.0),
    dig_cooldown_s=ENERGY_THROTTLE_S,
)


# ---------------------------------------------------------------------------
# Player profiles — "everyone": a fresh player through a fully-geared veteran.
# cadence_s = realistic seconds between clicks when ACTIVELY mining the button
# UI (open panel, click, await re-render); the effective dig interval is
# max(cadence_s, cooldown).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Profile:
    name: str
    tool: str
    depth: int


ACTIVE_CADENCE_S = 2.5  # a committed player clicking through the grid UI

PROFILES: list[Profile] = [
    Profile("Newcomer  (no tool, surface)", "none", 0),
    Profile("Casual    (pickaxe, cavern)", "pickaxe", 1),
    Profile("Regular   (iron pick, deep)", "iron", 2),
    Profile("Veteran   (diamond pick, magma)", "diamond", 3),
]


# ---------------------------------------------------------------------------
# Core dig model
# ---------------------------------------------------------------------------

_FEATURE_NAMES = ("NORMAL", "RICH", "BARREN", "TREASURE")


def _draw_ore_value(cfg: MiningConfig, depth: int, rng: random.Random) -> int:
    weights = ore_weights_for_depth(depth)
    ore = rng.choices(list(weights), weights=list(weights.values()), k=1)[0]
    return cfg.ore_value[ore]


def dig_coins(cfg: MiningConfig, prof: Profile, rng: random.Random) -> int:
    """Coins from selling the ore of a single dig under ``cfg`` for ``prof``."""
    # 1. base roll
    amount = rng.randint(1, cfg.base_max)
    # 2. tool multiplier
    amount *= cfg.tool_mult[prof.tool]
    # 3. cell feature richness (BARREN floors at 1 ore, like the real game)
    fi = rng.choices(range(4), weights=list(cfg.feature_weights), k=1)[0]
    richness = cfg.feature_richness[fi]
    amount = max(1, round(amount * richness))
    # 4. ore value (depth-weighted draw) → coins
    return amount * _draw_ore_value(cfg, prof.depth, rng)


@dataclass
class ProfileResult:
    profile: Profile
    coins_per_dig: float
    p95_dig: float  # spike size — a single lucky dig
    coins_per_hour: float  # at the config's effective dig interval
    interval_s: float


def simulate_profile(
    cfg: MiningConfig,
    prof: Profile,
    trials: int,
    rng: random.Random,
) -> ProfileResult:
    digs = [dig_coins(cfg, prof, rng) for _ in range(trials)]
    mean = statistics.mean(digs)
    p95 = sorted(digs)[min(len(digs) - 1, int(0.95 * len(digs)))]
    interval = max(ACTIVE_CADENCE_S, cfg.dig_cooldown_s)
    per_hour = mean * (3600.0 / interval)
    return ProfileResult(prof, mean, float(p95), per_hour, interval)


# ---------------------------------------------------------------------------
# Balance targets — the operational definition of "fun & playable for everyone"
# ---------------------------------------------------------------------------

# An active hour of mining should pay on the order of one daily claim — clearly
# worth doing (≈ 0.6-3 dailies/hr) but not trivializing the gated economy. The
# floor keeps a fresh player's hour meaningful; the ceiling keeps a maxed
# veteran from out-earning the whole rest of the economy in minutes.
TARGET_HOUR_LO = 1000.0  # ≈ 0.6 dailies / active hour
TARGET_HOUR_HI = 5000.0  # ≈ 3.0 dailies / active hour
# Tools + depth should matter, but a maxed veteran must not out-earn an
# absolute newcomer (no tool, surface) by a runaway margin — everyone stays in
# the game ("playable for everyone"). The structural floor on this ratio is the
# depth ore-value gain (≈1.7×, gear-coupled & fixed) × the tool-curve gap, so a
# value near 3.5× is the tightest a tool-curve change alone can reach.
MAX_VET_NEWCOMER_RATIO = 3.5
# Lucky strikes should feel special, not constant.
TARGET_BONANZA_LO = 0.08
TARGET_BONANZA_HI = 0.16


@dataclass
class Score:
    cfg: MiningConfig
    penalty: float  # hard target violation — drives the PASS/WARN verdict
    shaping: float  # tiny tie-breaker among equally-valid (penalty 0) configs
    results: list[ProfileResult]
    ratio: float

    @property
    def rank_key(self) -> tuple[float, float]:
        return (self.penalty, self.shaping)


def _band_penalty(value: float, lo: float, hi: float) -> float:
    """0 inside [lo, hi]; grows with relative distance outside it."""
    if value < lo:
        return (lo - value) / lo
    if value > hi:
        return (value - hi) / hi
    return 0.0


def score_config(cfg: MiningConfig, trials: int, rng: random.Random) -> Score:
    results = [simulate_profile(cfg, p, trials, rng) for p in PROFILES]
    per_hour = [r.coins_per_hour for r in results]
    newcomer, veteran = per_hour[0], per_hour[-1]
    ratio = veteran / newcomer if newcomer else 999.0

    penalty = 0.0
    # every profile's hourly faucet should sit in the target band
    for ph in per_hour:
        penalty += _band_penalty(ph, TARGET_HOUR_LO, TARGET_HOUR_HI)
    # bound the geared-vs-fresh gap
    penalty += max(0.0, ratio - MAX_VET_NEWCOMER_RATIO)
    # lucky-strike frequency
    penalty += 2.0 * _band_penalty(
        cfg.bonanza_rate(),
        TARGET_BONANZA_LO,
        TARGET_BONANZA_HI,
    )

    # Shaping: among configs that all satisfy the hard targets, prefer a snappier
    # cooldown (better feel), a newcomer hour near one daily, and a modest gap.
    daily = expected_daily()
    shaping = (
        0.30 * (cfg.dig_cooldown_s / 15.0)
        + 0.50 * abs(newcomer / daily - 1.0)
        + 0.20 * abs(ratio - 2.0)
    )
    return Score(cfg, penalty, shaping, results, ratio)


# ---------------------------------------------------------------------------
# Candidate configs for the sweep
# ---------------------------------------------------------------------------

# Tool-multiplier curves: CURRENT runs away (×1..×5); the alternatives compress
# the top so a veteran still out-mines a newcomer but within the playable bound.
_TOOL_CURVES: dict[str, dict[str, float]] = {
    "steep(1-5)": dict(TOOL_MULT),
    "compressed(1-3)": {
        "none": 1.0,
        "pickaxe": 1.5,
        "iron": 2.0,
        "gold": 2.5,
        "diamond": 3.0,
    },
    "gentle(1-2.5)": {
        "none": 1.0,
        "pickaxe": 1.4,
        "iron": 1.8,
        "gold": 2.2,
        "diamond": 2.5,
    },
    "flat(1-1.5)": {
        "none": 1.0,
        "pickaxe": 1.2,
        "iron": 1.3,
        "gold": 1.4,
        "diamond": 1.5,
    },
}

# Cell-feature mixes: CURRENT (25% bonanza, treasure ×3) → tempered/calm cut the
# bonanza rate into the target band and trim the treasure spike.
_FEATURE_SETS: dict[
    str,
    tuple[tuple[float, float, float, float], tuple[float, float, float, float]],
] = {
    "live(25% bonanza)": ((60.0, 20.0, 15.0, 5.0), (1.0, 2.0, 0.5, 3.0)),
    "tempered(15%)": ((66.0, 12.0, 19.0, 3.0), (1.0, 1.7, 0.6, 2.3)),
    "calm(12%)": ((70.0, 10.0, 18.0, 2.0), (1.0, 1.6, 0.6, 2.0)),
}

_COOLDOWNS = (4.0, 6.0, 8.0, 10.0, 12.0, 15.0)
_BASE_MAXES = (2, 3)


def candidate_configs() -> list[MiningConfig]:
    out: list[MiningConfig] = []
    for cd in _COOLDOWNS:
        for bm in _BASE_MAXES:
            for tname, tcurve in _TOOL_CURVES.items():
                for fname, (fw, fr) in _FEATURE_SETS.items():
                    out.append(
                        MiningConfig(
                            name=(f"cd={cd:g}s base=1-{bm} tool={tname} feat={fname}"),
                            base_max=bm,
                            tool_mult=dict(tcurve),
                            feature_weights=fw,
                            feature_richness=fr,
                            dig_cooldown_s=cd,
                        ),
                    )
    return out


def sweep(trials: int, seed: int) -> list[Score]:
    """Score every candidate (each on its own fresh RNG for determinism)."""
    scores: list[Score] = []
    for i, cfg in enumerate(candidate_configs()):
        scores.append(score_config(cfg, trials, random.Random(seed + 1 + i)))
    scores.sort(key=lambda s: s.rank_key)
    return scores


# ---------------------------------------------------------------------------
# Progression — digs (and active minutes) to afford each tool upgrade
# ---------------------------------------------------------------------------

# Buy prices — utils/mining/market.py (the coin sink).
TOOL_PRICES: list[tuple[str, int]] = [
    ("torch (10)", 10),
    ("pickaxe (25)", 25),
    ("lantern (40)", 40),
    ("iron pickaxe (60)", 60),
    ("gold pickaxe (140)", 140),
    ("diamond lantern (200)", 200),
    ("diamond pickaxe (320)", 320),
]


def progression(cfg: MiningConfig, prof: Profile, res: ProfileResult) -> list[str]:
    """Active minutes for ``prof`` to afford each upgrade at ``cfg``'s faucet."""
    coins_per_min = res.coins_per_hour / 60.0
    lines = []
    for label, price in TOOL_PRICES:
        mins = price / coins_per_min if coins_per_min else 999.0
        lines.append(f"      {label:<22} ~{mins:5.1f} active min")
    return lines


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _flag(ok: bool) -> str:
    return "PASS" if ok else "WARN"


def _report_config(
    title: str,
    cfg: MiningConfig,
    trials: int,
    rng: random.Random,
) -> Score:
    score = score_config(cfg, trials, rng)
    daily = expected_daily()
    print(f"\n{title}")
    print(f"    {cfg.name}")
    print(
        f"    bonanza cells = {cfg.bonanza_rate() * 100:.0f}%  ·  "
        f"dig cooldown = {cfg.dig_cooldown_s:g}s  ·  base roll = 1-{cfg.base_max}",
    )
    print(
        "    profile                            coins/dig  p95  coins/hr   dailies/hr",
    )
    for r in score.results:
        dailies = r.coins_per_hour / daily
        print(
            f"    {r.profile.name:<33} {r.coins_per_dig:8.1f} "
            f"{r.p95_dig:5.0f} {r.coins_per_hour:9.0f}   {dailies:5.1f}×",
        )
    print(
        f"    veteran/newcomer hourly ratio = {score.ratio:.1f}×  "
        f"(target ≤ {MAX_VET_NEWCOMER_RATIO:g}×)",
    )
    return score


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trials", type=int, default=6000, help="digs per profile.")
    ap.add_argument("--seed", type=int, default=42, help="RNG seed (determinism).")
    ap.add_argument(
        "--top",
        type=int,
        default=5,
        help="how many swept configs to list.",
    )
    args = ap.parse_args()
    rng = random.Random(args.seed)
    daily = expected_daily()

    print("=" * 74)
    print(
        f"Mining economy balance sim  (seed={args.seed}, trials={args.trials})",
    )
    print(
        f"Economy benchmark: !daily ≈ {daily:,.0f} coins/24h · "
        f"!work ≈ {WORK_COINS_PER_HOUR:g}/hr (gated).",
    )
    print(
        f"Targets: active mining {TARGET_HOUR_LO:,.0f}-{TARGET_HOUR_HI:,.0f} "
        f"coins/hr · vet/new ≤ {MAX_VET_NEWCOMER_RATIO:g}× · "
        f"bonanza {TARGET_BONANZA_LO * 100:.0f}-{TARGET_BONANZA_HI * 100:.0f}%.",
    )
    print("=" * 74)

    warns = 0

    # 1. The pre-rebalance faucet — the bug the sim diagnosed (over target).
    pre = _report_config(
        "[1] PRE-REBALANCE faucet — too large & too frequent (the bug)",
        PRE_REBALANCE,
        args.trials,
        rng,
    )
    worst = max(pre.results, key=lambda r: r.coins_per_hour)
    mins_to_daily = daily / (worst.coins_per_hour / 60.0)
    print(
        f"    → a '{worst.profile.name.split('(')[0].strip()}' earned a full !daily "
        f"({daily:,.0f}) in ~{mins_to_daily:.1f} active min; bonanza "
        f"{PRE_REBALANCE.bonanza_rate() * 100:.0f}%; gap {pre.ratio:.1f}× — "
        "confirmed the owner's read.",
    )

    # 1b. The CURRENT live faucet — rebalanced magnitude + the energy throttle.
    cur = _report_config(
        "[1b] CURRENT live faucet — applied rebalance + energy throttle",
        CURRENT,
        args.trials,
        rng,
    )
    over = [r for r in cur.results if r.coins_per_hour > TARGET_HOUR_HI]
    in_band = not over and cur.ratio <= MAX_VET_NEWCOMER_RATIO
    warns += not in_band
    print(
        f"    → energy regen ≈ {ENERGY_REGEN_PER_HOUR}/hr is the frequency brake "
        f"(no per-dig wait); faucet now {'IN BAND' if in_band else 'still off'}.  "
        f"{_flag(in_band)}",
    )

    # 2. Sweep candidate configs for the most balanced one.
    print("\n[2] Config sweep — searching for the most balanced configuration…")
    scores = sweep(max(1000, args.trials // 3), args.seed)
    print(f"    evaluated {len(scores)} configs against the targets. Top picks:")
    print(
        "    rank  penalty  new/hr  vet/hr  ratio  bonanza  config",
    )
    for i, s in enumerate(scores[: args.top], 1):
        ph = [r.coins_per_hour for r in s.results]
        print(
            f"    {i:>4}  {s.penalty:7.2f}  {ph[0]:6.0f}  {ph[-1]:6.0f}  "
            f"{s.ratio:4.1f}×  {s.cfg.bonanza_rate() * 100:5.0f}%  {s.cfg.name}",
        )

    best = scores[0]
    # 3. Detail the recommended config + its progression curve.
    rec = _report_config(
        "[3] RECOMMENDED config (lowest penalty)",
        best.cfg,
        args.trials,
        rng,
    )
    balanced = best.penalty < 0.5
    warns += not balanced
    print(f"    overall balance penalty = {best.penalty:.2f}  {_flag(balanced)}")

    print("\n[4] Progression at the recommended faucet (active minutes to afford):")
    for r in rec.results:
        print(f"    {r.profile.name}:")
        for line in progression(best.cfg, r.profile, r):
            print(line)

    # 5. Verdict + the concrete deltas vs the live game.
    print("\n[5] Recommended changes vs the live game:")
    deltas = _diff_configs(CURRENT, best.cfg)
    for d in deltas:
        print(f"    • {d}")

    print("\n" + "=" * 74)
    verdict = (
        "BALANCED CONFIG FOUND (no flags)"
        if warns == 0
        else f"REVIEW — {warns} warn flag(s) (the current game is unbalanced; "
        "apply the recommendation)"
    )
    print(f"VERDICT: {verdict}")
    print("=" * 74)
    return 0


def _diff_configs(a: MiningConfig, b: MiningConfig) -> list[str]:
    out: list[str] = []
    if a.dig_cooldown_s != b.dig_cooldown_s:
        out.append(
            f"ADD a per-dig cooldown of {b.dig_cooldown_s:g}s "
            f"(currently {a.dig_cooldown_s:g}s — the missing frequency brake).",
        )
    if a.base_max != b.base_max:
        out.append(f"base roll 1-{a.base_max} → 1-{b.base_max} ore.")
    if a.tool_mult != b.tool_mult:
        out.append(
            "compress the tool multiplier curve "
            f"{_curve_str(a.tool_mult)} → {_curve_str(b.tool_mult)} "
            "(keeps the geared/fresh gap playable).",
        )
    if a.feature_weights != b.feature_weights or (
        a.feature_richness != b.feature_richness
    ):
        out.append(
            f"retune cell features: bonanza {a.bonanza_rate() * 100:.0f}% → "
            f"{b.bonanza_rate() * 100:.0f}%, treasure richness "
            f"×{a.feature_richness[3]:g} → ×{b.feature_richness[3]:g}.",
        )
    if not out:
        out.append("none — the live config already meets the targets.")
    return out


def _curve_str(curve: dict[str, float]) -> str:
    order = ("none", "pickaxe", "iron", "gold", "diamond")
    return "×" + "/".join(f"{curve[k]:g}" for k in order)


if __name__ == "__main__":
    raise SystemExit(main())
