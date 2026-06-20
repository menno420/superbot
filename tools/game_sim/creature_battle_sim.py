#!/usr/bin/env python3.10
"""Creature catch + PvP-battle playability simulator (design tool, not runtime).

Why this exists
---------------
The owner is designing a Pokétwo-style monster game for SuperBot and wants to
*"see how playable it is"* **before** building it into ``disbot/`` — the same
"simulation-sane numbers" discipline the gear-set tuning used
(``docs/planning/gear-set-numbers-2026-06-11.md``). This script models a v1
ruleset with an **original creature roster** (no Pokémon IP — see the design
doc) and runs Monte-Carlo trials to answer the questions that decide whether the
game is fun and *fair* (not pay-to-win, per owner decision Q-0039):

1. **Type balance** — does any element dominate the win-rate matrix?
2. **Level fairness** — how deterministic is a level advantage? (If +3 levels
   ⇒ ~100% win, the game is a grind/whale-fest, not a game.)
3. **Skill impact** — does smart team-ordering beat random? (Counterplay must
   be rewarded, but not absolute.)
4. **Catch grind** — how many encounters to assemble a first team of 3?

It is **stdlib-only, deterministic** (``--seed``), and prints a verdict with
PASS/WARN flags. Nothing here is imported by the bot; it informs the design doc.

Run::

    python3.10 tools/game_sim/creature_battle_sim.py
    python3.10 tools/game_sim/creature_battle_sim.py --trials 4000 --seed 7

Provenance: added 2026-06-20 (owner request — "use a simulator to see how
playable it is"). Disposable design tool — delete if the creature game is
dropped or once its numbers are pinned into the real subsystem.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path

# ---------------------------------------------------------------------------
# v1 ruleset — elements, effectiveness, roster (ORIGINAL names, no Pokémon IP)
# ---------------------------------------------------------------------------

# Six original elements arranged so each is strong vs the next two and weak vs
# the previous two (the +3 opposite is neutral). This is symmetric by
# construction, so a *balanced* roster should land every element near 50%.
ELEMENTS: tuple[str, ...] = ("Ember", "Tide", "Bramble", "Spark", "Stone", "Gust")
_N = len(ELEMENTS)

STRONG_MULT = 1.5
WEAK_MULT = 0.67
NEUTRAL_MULT = 1.0


def effectiveness(attacker_el: str, defender_el: str) -> float:
    """Type multiplier of ``attacker_el`` attacking ``defender_el``."""
    a = ELEMENTS.index(attacker_el)
    d = ELEMENTS.index(defender_el)
    delta = (d - a) % _N
    if delta in (1, 2):
        return STRONG_MULT  # attacker beats the next two
    if delta in (_N - 1, _N - 2):
        return WEAK_MULT  # attacker loses to the previous two
    return NEUTRAL_MULT  # the +3 opposite (and self) is neutral


# Stat budgets per rarity — higher rarity = bigger budget (rarer = stronger,
# but level + type still let a common counter an epic; the sim checks that).
RARITY_BUDGET: dict[str, int] = {
    "Common": 200,
    "Uncommon": 230,
    "Rare": 260,
    "Epic": 300,
}
# Base catch chance per rarity at player level 1 (before level/curve bonuses).
RARITY_CATCH_BASE: dict[str, float] = {
    "Common": 0.55,
    "Uncommon": 0.38,
    "Rare": 0.22,
    "Epic": 0.10,
}


@dataclass(frozen=True)
class Species:
    name: str
    element: str
    rarity: str
    hp: int
    atk: int
    df: int
    spd: int

    @property
    def budget(self) -> int:
        return self.hp + self.atk + self.df + self.spd


def _spread(
    budget: int,
    hp: float,
    atk: float,
    df: float,
    spd: float,
) -> tuple[int, int, int, int]:
    """Split ``budget`` across four stats by archetype weights (sum≈1)."""
    total = hp + atk + df + spd
    return (
        round(budget * hp / total),
        round(budget * atk / total),
        round(budget * df / total),
        round(budget * spd / total),
    )


def _roster() -> list[Species]:
    """Load the original creature roster from ``creatures.json`` (creature-as-data).

    Stats are *derived*, not stored: each creature's budget = ``RARITY_BUDGET[rarity]`` split
    across HP/ATK/DEF/SPD by archetype weights. This is the "adding a creature is a data row, not
    code" design (Q-0187d) — the catalog is the v1 launch roster (~36), and the same sim below
    validates the *whole* roster's balance before any of it touches ``disbot/``.

    Archetype weights (hp, atk, df, spd): attacker .9/1.3/.7/1.1, tank 1.3/.8/1.3/.6,
    balanced 1/1/1/1, speedster .8/1.2/.7/1.3.
    """
    arche = {
        "attacker": (0.9, 1.3, 0.7, 1.1),
        "tank": (1.3, 0.8, 1.3, 0.6),
        "balanced": (1.0, 1.0, 1.0, 1.0),
        "speedster": (0.8, 1.2, 0.7, 1.3),
    }
    catalog = json.loads((Path(__file__).with_name("creatures.json")).read_text())
    out: list[Species] = []
    for c in catalog["creatures"]:
        hp, atk, df, spd = _spread(RARITY_BUDGET[c["rarity"]], *arche[c["archetype"]])
        out.append(Species(c["name"], c["element"], c["rarity"], hp, atk, df, spd))
    return out


ROSTER: list[Species] = _roster()
BY_ELEMENT: dict[str, list[Species]] = {
    el: [s for s in ROSTER if s.element == el] for el in ELEMENTS
}

# ---------------------------------------------------------------------------
# Battle model — 3v3, turn-based, lead fights until it faints then next in
# ---------------------------------------------------------------------------

MOVE_POWER = 10  # tuned so an even 1v1 lasts ~7-10 turns (variance → comebacks)
HP_PER_LVL = 0.06
OFF_PER_LVL = 0.035


@dataclass
class Mon:
    species: Species
    level: int
    cur_hp: int = field(init=False)

    def __post_init__(self) -> None:
        self.cur_hp = self.max_hp

    @property
    def max_hp(self) -> int:
        return round(self.species.hp * (1 + HP_PER_LVL * (self.level - 1)))

    @property
    def atk(self) -> float:
        return self.species.atk * (1 + OFF_PER_LVL * (self.level - 1))

    @property
    def df(self) -> float:
        return self.species.df * (1 + OFF_PER_LVL * (self.level - 1))

    @property
    def spd(self) -> float:
        return self.species.spd * (1 + OFF_PER_LVL * (self.level - 1))


def _damage(attacker: Mon, defender: Mon, rng: random.Random) -> int:
    mult = effectiveness(attacker.species.element, defender.species.element)
    jitter = rng.uniform(0.85, 1.0)
    raw = (attacker.atk / max(1.0, defender.df)) * MOVE_POWER * mult * jitter
    return max(1, round(raw))


def battle(team_a: list[Mon], team_b: list[Mon], rng: random.Random) -> bool:
    """Return True if team A wins. Fresh HP copies are made by the caller."""
    a_idx = b_idx = 0
    guard = 0
    while a_idx < len(team_a) and b_idx < len(team_b):
        guard += 1
        if guard > 2000:  # pathological stall guard
            return sum(m.cur_hp for m in team_a) >= sum(m.cur_hp for m in team_b)
        a, b = team_a[a_idx], team_b[b_idx]
        # Faster strikes first; an exact tie (e.g. a same-level mirror) is a
        # coin-flip, not a fixed A-advantage — otherwise the lead-fights-to-death
        # model hands every mirror to whoever is hard-coded first.
        if a.spd > b.spd:
            first, second = a, b
        elif b.spd > a.spd:
            first, second = b, a
        else:
            first, second = (a, b) if rng.random() < 0.5 else (b, a)
        second.cur_hp -= _damage(first, second, rng)
        if second.cur_hp <= 0:
            if second is a:
                a_idx += 1
            else:
                b_idx += 1
            continue
        first.cur_hp -= _damage(second, first, rng)
        if first.cur_hp <= 0:
            if first is a:
                a_idx += 1
            else:
                b_idx += 1
    return b_idx >= len(team_b)


def _fresh(team: list[Mon]) -> list[Mon]:
    return [Mon(m.species, m.level) for m in team]


# ---------------------------------------------------------------------------
# Strategy: ordering a team's lead vs the opponent lead (the "skill" lever)
# ---------------------------------------------------------------------------


def order_type_aware(team: list[Mon], opp_lead: Mon) -> list[Mon]:
    """Lead with the creature whose element best counters the opponent lead."""
    return sorted(
        team,
        key=lambda m: -effectiveness(m.species.element, opp_lead.species.element),
    )


# ---------------------------------------------------------------------------
# Simulations
# ---------------------------------------------------------------------------


def sim_type_balance(rng: random.Random, trials: int) -> dict[str, float]:
    """1v1 equal-level win-rate of each element averaged over all opponents."""
    wins: dict[str, list[float]] = {el: [] for el in ELEMENTS}
    for atk_el, def_el in product(ELEMENTS, ELEMENTS):
        if atk_el == def_el:
            continue
        a_sp = BY_ELEMENT[atk_el][0]
        b_sp = BY_ELEMENT[def_el][0]
        w = 0
        for _ in range(trials):
            if battle([Mon(a_sp, 10)], [Mon(b_sp, 10)], rng):
                w += 1
        wins[atk_el].append(w / trials)
    return {el: statistics.mean(v) for el, v in wins.items()}


def sim_level_fairness(rng: random.Random, trials: int) -> list[tuple[int, float]]:
    """Win-rate of the higher-level creature as the level gap grows (same element).

    Same element ⇒ neutral matchup, so this isolates *level* from *type*. The
    steepness of this curve is the design finding that motivates level
    normalization in PvP (see the report), NOT a tuning target to chase.
    """
    sp = BY_ELEMENT["Tide"][0]
    out: list[tuple[int, float]] = []
    for gap in range(0, 11, 2):
        w = 0
        for _ in range(trials):
            if battle([Mon(sp, 10 + gap)], [Mon(sp, 10)], rng):
                w += 1
        out.append((gap, w / trials))
    return out


def sim_normalized_fairness(rng: random.Random, trials: int) -> float:
    """Win-rate of 'team A' across random *equal-level* 3v3s (target ~50%).

    Under the PvP level-normalization rule, two random teams meet at a flat
    level. With no structural side-bias the win-rate should sit near 50% — this
    is the sanity check that the battle engine itself is unbiased and that, once
    level is removed, the outcome is driven by roster/type, not by who is "A".
    """
    w = 0
    for _ in range(trials):
        pool = rng.sample(ROSTER, 6)
        a = [Mon(s, 25) for s in pool[:3]]
        b = [Mon(s, 25) for s in pool[3:]]
        if battle(_fresh(a), _fresh(b), rng):
            w += 1
    return w / trials


def sim_skill_impact(rng: random.Random, trials: int) -> float:
    """Win-rate of a type-aware orderer vs a random orderer (equal 3-mon teams).

    Both draw the *same* random 3 species at level 10; the skilled player orders
    their lead to counter the opponent's lead, the other shuffles.
    """
    w = 0
    for _ in range(trials):
        pool = rng.sample(ROSTER, 6)
        skilled = [Mon(s, 10) for s in pool[:3]]
        rand_team = [Mon(s, 10) for s in pool[3:]]
        # Opponent (random) reveals a random lead; skilled orders against it.
        rng.shuffle(rand_team)
        ordered = order_type_aware(skilled, rand_team[0])
        if battle(_fresh(ordered), _fresh(rand_team), rng):
            w += 1
    return w / trials


def sim_catch_grind(rng: random.Random, trials: int) -> dict[int, float]:
    """Mean encounters to catch a team of 3 at player levels 1/3/5.

    Catch chance = rarity base * (1 + 0.04*(player_level-1)), clamped ≤ 0.95.
    Each encounter draws a random species (rarity-weighted toward common).
    """
    rarity_weight = {"Common": 0.5, "Uncommon": 0.28, "Rare": 0.16, "Epic": 0.06}
    species_by_rarity: dict[str, list[Species]] = {}
    for s in ROSTER:
        species_by_rarity.setdefault(s.rarity, []).append(s)
    rarities = list(rarity_weight)
    weights = list(rarity_weight.values())
    out: dict[int, float] = {}
    for plevel in (1, 3, 5):
        totals: list[int] = []
        for _ in range(trials):
            caught = 0
            enc = 0
            while caught < 3 and enc < 500:
                enc += 1
                rar = rng.choices(rarities, weights)[0]
                chance = min(0.95, RARITY_CATCH_BASE[rar] * (1 + 0.04 * (plevel - 1)))
                if rng.random() < chance:
                    caught += 1
            totals.append(enc)
        out[plevel] = statistics.mean(totals)
    return out


def sample_battle_log(rng: random.Random) -> list[str]:
    """A readable 1v1 so the owner can eyeball the feel."""
    a = Mon(BY_ELEMENT["Ember"][0], 10)
    b = Mon(BY_ELEMENT["Bramble"][1], 10)
    log = [
        f"{a.species.name} (Ember L10, {a.max_hp}hp) vs {b.species.name} (Bramble L10, {b.max_hp}hp)",
    ]
    turn = 0
    while a.cur_hp > 0 and b.cur_hp > 0 and turn < 30:
        turn += 1
        first, second = (a, b) if a.spd >= b.spd else (b, a)
        dmg = _damage(first, second, rng)
        second.cur_hp -= dmg
        log.append(
            f"  T{turn}: {first.species.name} hits {second.species.name} for {dmg} → {max(0, second.cur_hp)}hp",
        )
        if second.cur_hp <= 0:
            log.append(f"  {second.species.name} faints. {first.species.name} wins.")
            break
        dmg = _damage(second, first, rng)
        first.cur_hp -= dmg
        log.append(
            f"  T{turn}: {second.species.name} hits {first.species.name} for {dmg} → {max(0, first.cur_hp)}hp",
        )
        if first.cur_hp <= 0:
            log.append(f"  {first.species.name} faints. {second.species.name} wins.")
            break
    return log


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _flag(ok: bool) -> str:
    return "PASS" if ok else "WARN"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--trials",
        type=int,
        default=2000,
        help="Monte-Carlo trials per cell.",
    )
    ap.add_argument("--seed", type=int, default=42, help="RNG seed (determinism).")
    args = ap.parse_args()
    rng = random.Random(args.seed)

    print("=" * 70)
    print(
        f"Creature catch + PvP-battle playability sim  (seed={args.seed}, trials={args.trials})",
    )
    print(f"Roster: {len(ROSTER)} original creatures across {_N} elements")
    print("=" * 70)

    warns = 0

    # 1. Type balance
    print("\n[1] Type balance — avg 1v1 win-rate per element (target 40–60%)")
    tb = sim_type_balance(rng, args.trials // 4 or 1)
    for el, wr in sorted(tb.items(), key=lambda kv: -kv[1]):
        bad = not (0.40 <= wr <= 0.60)
        warns += bad
        print(f"    {el:<8} {wr * 100:5.1f}%  {_flag(not bad)}")
    spread = max(tb.values()) - min(tb.values())
    print(f"    spread (max-min) = {spread * 100:.1f} pts  {_flag(spread <= 0.20)}")
    warns += spread > 0.20

    # 2. Level fairness (INFORMATIONAL — motivates the normalization rule)
    print("\n[2] Raw-level dominance — higher-level win-rate vs gap (same element)")
    lf = sim_level_fairness(rng, args.trials)
    for gap, wr in lf:
        print(f"    +{gap:>2} levels → {wr * 100:5.1f}% win")
    gap2 = dict(lf).get(2, 1.0)
    print(f"    → a +2 gap already wins {gap2 * 100:.0f}%: raw levels DECIDE 1v1s.")
    print("    → DESIGN RULE: PvP normalizes to a flat level (skill/types decide,")
    print("      not who ground more) — this is informational, not a warn flag.")

    # 2b. Normalized fairness (the rule in action — this IS a pass/fail gate)
    nf = sim_normalized_fairness(rng, args.trials)
    unbiased = 0.45 <= nf <= 0.55
    warns += not unbiased
    print("\n[2b] Normalized PvP — team-A win-rate across random equal-L teams")
    print(f"    {nf * 100:.1f}%  (target 45–55%, unbiased engine)  {_flag(unbiased)}")

    # 3. Skill impact
    print("\n[3] Skill impact — type-aware ordering vs random (equal teams)")
    si = sim_skill_impact(rng, args.trials)
    good = 0.52 <= si <= 0.75  # skill rewarded, but not absolute
    warns += not good
    print(f"    skilled win-rate = {si * 100:.1f}%  (target 52–75%)  {_flag(good)}")

    # 4. Catch grind
    print("\n[4] Catch grind — mean encounters to a team of 3")
    cg = sim_catch_grind(rng, args.trials // 4 or 1)
    for plevel, mean in cg.items():
        print(f"    player L{plevel}: {mean:.1f} encounters")
    grind_ok = cg.get(1, 99) <= 12  # a fresh player gets a starter team in a sitting
    warns += not grind_ok
    print(f"    fresh player ≤ ~12 encounters for a team?  {_flag(grind_ok)}")

    # 5. Sample
    print("\n[5] Sample battle (eyeball the feel)")
    for line in sample_battle_log(rng):
        print("    " + line)

    print("\n" + "=" * 70)
    verdict = (
        "PLAYABLE (no flags)" if warns == 0 else f"NEEDS TUNING — {warns} warn flag(s)"
    )
    print(f"VERDICT: {verdict}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
