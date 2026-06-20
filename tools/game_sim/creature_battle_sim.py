#!/usr/bin/env python3.10
"""Creature catch + PvP-battle playability simulator (design tool, not runtime).

Why this exists
---------------
The owner is designing a Pokétwo-style monster game for SuperBot and wants to
*"see how playable it is"* **before** building it into ``disbot/`` — the same
"simulation-sane numbers" discipline the gear-set tuning used
(``docs/planning/gear-set-numbers-2026-06-11.md``). This script models the v1
ruleset with an **original creature roster** (no Pokémon IP — see the design
doc) and runs Monte-Carlo trials to answer the questions that decide whether the
game is fun and *fair* (not pay-to-win, per owner decision Q-0039).

v1 combat model (owner design, 2026-06-20)
------------------------------------------
- **6 elements** + a neutral **Normal** damage type (always ×1.0).
- **Teams of 6**, the standard being **one creature of each element** (the
  "6-mon team" convention).
- **4 moves per creature**: two *damage* — one **Normal** (reliable, ×1.0) and
  one **element/signature** (the type chart applies, ×1.5/×1.0/×0.67) — and two
  *status* (no damage): one **defensive** (raise own DEF) and one **offensive**
  (raise own ATK). The element move out-damages Normal vs neutral/weak targets,
  but Normal beats it vs a *resistant* target — so **move choice per matchup**
  is a skill lever, on top of when to spend a turn buffing.

What it checks
--------------
1. **Type balance** — does any element dominate?
2. **Raw-level dominance** — how deterministic is a level lead? (motivates the
   PvP level-normalization rule).
3. **Normalized PvP fairness** — equal-level 6v6 is unbiased (~50%).
4. **Skill impact** — does smart move-choice + setup beat random play?
5. **Status-move value** — do the non-damage moves add value without dominating?
6. **Catch grind** — encounters to a starter (3) and a full standard team (6).

It is **stdlib-only, deterministic** (``--seed``), and prints a verdict with
PASS/WARN flags. Nothing here is imported by the bot; it informs the design doc.

Run::

    python3.10 tools/game_sim/creature_battle_sim.py
    python3.10 tools/game_sim/creature_battle_sim.py --trials 4000 --seed 7

Provenance: added 2026-06-20 (owner request — "use a simulator to see how
playable it is"); move system added 2026-06-20 (owner design). Disposable design
tool — delete if the creature game is dropped or once its numbers are pinned into
the real subsystem.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections.abc import Callable
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

# "Normal" is a seventh DAMAGE type carried by every creature's reliable move.
# It is neutral against everything (no type chart) — the safe option a smart
# player falls back to when their element move would be resisted.
NORMAL_TYPE = "Normal"

STRONG_MULT = 1.5
WEAK_MULT = 0.67
NEUTRAL_MULT = 1.0


def effectiveness(attacker_type: str, defender_el: str) -> float:
    """Type multiplier of ``attacker_type`` (an element or Normal) vs ``defender_el``."""
    if attacker_type == NORMAL_TYPE:
        return NEUTRAL_MULT  # Normal damage ignores the type chart
    a = ELEMENTS.index(attacker_type)
    d = ELEMENTS.index(defender_el)
    delta = (d - a) % _N
    if delta in (1, 2):
        return STRONG_MULT  # attacker beats the next two
    if delta in (_N - 1, _N - 2):
        return WEAK_MULT  # attacker loses to the previous two
    return NEUTRAL_MULT  # the +3 opposite (and self) is neutral


# Stat budgets per rarity — higher rarity = bigger budget (rarer = stronger,
# but level + type + move choice still let a common counter an epic).
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
# Moves — 4 per creature: Normal damage, element damage, +DEF, +ATK
# ---------------------------------------------------------------------------

NORMAL_POWER = 9  # reliable, always ×1.0
ELEMENT_POWER = 12  # signature — higher base, but the type chart applies
BUFF_STEP = 0.25  # each status use shifts the stat +25% …
BUFF_CAP = 0.50  # … capped at +50% so buff-spam isn't degenerate
TEAM_SIZE = 6  # the "6-mon team" standard (one of each element)

# Original signature-move names per element (no Pokémon move IP).
_ELEMENT_MOVE = {
    "Ember": "Cinderlash",
    "Tide": "Tidal Crash",
    "Bramble": "Thorn Volley",
    "Spark": "Voltstrike",
    "Stone": "Boulder Smash",
    "Gust": "Galeforce",
}


@dataclass(frozen=True)
class Move:
    name: str
    kind: str  # "damage" | "buff"
    mtype: str  # damage type ("Normal" or an element); "" for buffs
    power: int  # damage moves only
    stat: str  # buff moves only: "atk" | "def"


def moves_for(species: Species) -> list[Move]:
    """The four v1 moves: Normal hit, element hit, defensive buff, offensive buff."""
    return [
        Move("Strike", "damage", NORMAL_TYPE, NORMAL_POWER, ""),
        Move(
            _ELEMENT_MOVE[species.element],
            "damage",
            species.element,
            ELEMENT_POWER,
            "",
        ),
        Move("Bulwark", "buff", "", 0, "def"),  # defensive non-damage (+DEF)
        Move("Onslaught", "buff", "", 0, "atk"),  # offensive non-damage (+ATK)
    ]


# ---------------------------------------------------------------------------
# Battle model — 6v6, turn-based, lead fights until it faints then next in
# ---------------------------------------------------------------------------

HP_PER_LVL = 0.06
OFF_PER_LVL = 0.035


@dataclass
class Mon:
    species: Species
    level: int
    cur_hp: int = field(init=False)
    atk_stage: float = field(default=0.0, init=False)  # additive buff, capped
    def_stage: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self.cur_hp = self.max_hp

    @property
    def max_hp(self) -> int:
        return round(self.species.hp * (1 + HP_PER_LVL * (self.level - 1)))

    @property
    def atk(self) -> float:
        return (
            self.species.atk
            * (1 + OFF_PER_LVL * (self.level - 1))
            * (1 + self.atk_stage)
        )

    @property
    def df(self) -> float:
        return (
            self.species.df
            * (1 + OFF_PER_LVL * (self.level - 1))
            * (1 + self.def_stage)
        )

    @property
    def spd(self) -> float:
        return self.species.spd * (1 + OFF_PER_LVL * (self.level - 1))

    def apply_buff(self, stat: str) -> None:
        if stat == "atk":
            self.atk_stage = min(BUFF_CAP, self.atk_stage + BUFF_STEP)
        else:
            self.def_stage = min(BUFF_CAP, self.def_stage + BUFF_STEP)


def move_damage(attacker: Mon, defender: Mon, move: Move, rng: random.Random) -> int:
    mult = effectiveness(move.mtype, defender.species.element)
    jitter = rng.uniform(0.85, 1.0)
    raw = (attacker.atk / max(1.0, defender.df)) * move.power * mult * jitter
    return max(1, round(raw))


def _expected_damage(attacker: Mon, defender: Mon, move: Move) -> float:
    """Jitter-free expected damage — used by the AI to compare moves."""
    if move.kind != "damage":
        return 0.0
    mult = effectiveness(move.mtype, defender.species.element)
    return (attacker.atk / max(1.0, defender.df)) * move.power * mult * 0.925


# --- Move-selection policies (the skill lever): (actor, target, rng) -> Move ---

Policy = Callable[[Mon, Mon, random.Random], Move]


def _best_damage_move(actor: Mon, target: Mon) -> Move:
    dmg = [m for m in moves_for(actor.species) if m.kind == "damage"]
    return max(dmg, key=lambda m: _expected_damage(actor, target, m))


def policy_best_damage(actor: Mon, target: Mon, rng: random.Random) -> Move:
    """Skilled *move choice*: pick the higher-damage of Normal vs element each turn."""
    return _best_damage_move(actor, target)


def policy_naive_element(actor: Mon, target: Mon, rng: random.Random) -> Move:
    """Always fire the signature element move, ignoring whether it is resisted."""
    return next(m for m in moves_for(actor.species) if m.mtype == actor.species.element)


def policy_random(actor: Mon, target: Mon, rng: random.Random) -> Move:
    """Pick any of the four moves at random (wastes turns on ill-timed buffs)."""
    return rng.choice(moves_for(actor.species))


def policy_setup(actor: Mon, target: Mon, rng: random.Random) -> Move:
    """Skilled move choice + ONE opening offensive buff when it is safe.

    Invests a single turn in +ATK when the actor is faster, healthy, hasn't
    buffed yet, and can't KO this turn — then attacks with the best move.
    """
    best = _best_damage_move(actor, target)
    if _expected_damage(actor, target, best) >= target.cur_hp:
        return best  # finish the kill, don't waste the turn
    if (
        actor.atk_stage == 0.0
        and actor.cur_hp >= 0.6 * actor.max_hp
        and actor.spd >= target.spd
    ):
        return next(m for m in moves_for(actor.species) if m.stat == "atk")
    return best


def _act(actor: Mon, target: Mon, policy: Policy, rng: random.Random) -> None:
    move = policy(actor, target, rng)
    if move.kind == "buff":
        actor.apply_buff(move.stat)
    else:
        target.cur_hp -= move_damage(actor, target, move, rng)


def battle(
    team_a: list[Mon],
    team_b: list[Mon],
    rng: random.Random,
    policy_a: Policy = policy_best_damage,
    policy_b: Policy = policy_best_damage,
) -> bool:
    """Return True if team A wins. Fresh HP copies are made by the caller."""
    ia = ib = 0
    guard = 0
    while ia < len(team_a) and ib < len(team_b):
        guard += 1
        if guard > 5000:  # pathological stall guard
            return sum(m.cur_hp for m in team_a) >= sum(m.cur_hp for m in team_b)
        a, b = team_a[ia], team_b[ib]
        # Faster acts first; an exact tie is a coin-flip, never a fixed A-edge.
        if a.spd > b.spd:
            order = [(a, b, policy_a), (b, a, policy_b)]
        elif b.spd > a.spd:
            order = [(b, a, policy_b), (a, b, policy_a)]
        elif rng.random() < 0.5:
            order = [(a, b, policy_a), (b, a, policy_b)]
        else:
            order = [(b, a, policy_b), (a, b, policy_a)]
        for actor, target, policy in order:
            if actor.cur_hp > 0 and target.cur_hp > 0:
                _act(actor, target, policy, rng)
        if a.cur_hp <= 0:
            ia += 1
        if b.cur_hp <= 0:
            ib += 1
    return ib >= len(team_b)


def _fresh(team: list[Mon]) -> list[Mon]:
    return [Mon(m.species, m.level) for m in team]


# ---------------------------------------------------------------------------
# Team construction + lead ordering (the other skill lever)
# ---------------------------------------------------------------------------


def standard_team(rng: random.Random, level: int) -> list[Mon]:
    """A 'one of each element' 6-mon team — the owner's standard composition."""
    return [Mon(rng.choice(BY_ELEMENT[el]), level) for el in ELEMENTS]


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
    """1v1 equal-level win-rate of each element averaged over all opponents.

    Both sides play *best move choice*, so this measures the type chart's fairness
    under skilled play (smart players soften resistances by using Normal).
    """
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
    normalization in PvP, NOT a tuning target to chase.
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
    """Win-rate of 'team A' across random *equal-level* standard 6v6s (target ~50%).

    Both teams are 'one of each element' at a flat level, both playing best move
    choice. With no structural side-bias the win-rate should sit near 50% — the
    sanity check that the engine is unbiased once level is removed.
    """
    w = 0
    for _ in range(trials):
        a = standard_team(rng, 25)
        b = standard_team(rng, 25)
        if battle(_fresh(a), _fresh(b), rng):
            w += 1
    return w / trials


def sim_skill_impact(rng: random.Random, trials: int) -> float:
    """Skilled (setup + type-aware lead) vs a realistic *beginner*, identical teams.

    Both sides field 'one of each element' at the same level. The skilled side
    orders its lead to counter the opponent and plays the setup policy (best move
    each turn + an opening +ATK). The beginner just spams their signature element
    move every turn (``policy_naive_element``) with a random lead — a plausible
    new player, not the random-buff strawman (which loses ~94% and overstates the
    gap). Counterplay must be rewarded, not absolute.
    """
    w = 0
    for _ in range(trials):
        a = standard_team(rng, 20)
        b = standard_team(rng, 20)
        rng.shuffle(b)
        skilled = order_type_aware(a, b[0])
        if battle(
            _fresh(skilled),
            _fresh(b),
            rng,
            policy_a=policy_setup,
            policy_b=policy_naive_element,
        ):
            w += 1
    return w / trials


def sim_status_value(rng: random.Random, trials: int) -> float:
    """Setup play vs pure best-damage (no buffs), identical standard teams.

    Isolates the value of the *status* moves: the setup side spends an opening
    turn on +ATK; the other only ever attacks. >50% means the non-damage moves
    earn their slot; well below ~75% means they are not degenerate.
    """
    w = 0
    for _ in range(trials):
        a = standard_team(rng, 20)
        b = standard_team(rng, 20)
        if battle(
            _fresh(a),
            _fresh(b),
            rng,
            policy_a=policy_setup,
            policy_b=policy_best_damage,
        ):
            w += 1
    return w / trials


def sim_catch_grind(
    rng: random.Random,
    trials: int,
    team_size: int = 3,
) -> dict[int, float]:
    """Mean encounters to catch ``team_size`` creatures at player levels 1/3/5.

    Catch chance = rarity base * (1 + 0.04*(player_level-1)), clamped ≤ 0.95.
    Each encounter draws a random species (rarity-weighted toward common).
    """
    rarity_weight = {"Common": 0.5, "Uncommon": 0.28, "Rare": 0.16, "Epic": 0.06}
    rarities = list(rarity_weight)
    weights = list(rarity_weight.values())
    out: dict[int, float] = {}
    for plevel in (1, 3, 5):
        totals: list[int] = []
        for _ in range(trials):
            caught = 0
            enc = 0
            while caught < team_size and enc < 1000:
                enc += 1
                rar = rng.choices(rarities, weights)[0]
                chance = min(0.95, RARITY_CATCH_BASE[rar] * (1 + 0.04 * (plevel - 1)))
                if rng.random() < chance:
                    caught += 1
            totals.append(enc)
        out[plevel] = statistics.mean(totals)
    return out


def sim_standard_team_grind(rng: random.Random, trials: int) -> dict[int, float]:
    """Mean encounters to catch one of *each* element (the standard 6-mon team).

    A coupon-collector-style grind: you need all six elements, and a catch can
    fail. This is the 'assemble your full competitive team' horizon, distinct
    from the quick 3-mon starter above.
    """
    out: dict[int, float] = {}
    for plevel in (1, 5):
        totals: list[int] = []
        for _ in range(trials):
            have: set[str] = set()
            enc = 0
            while len(have) < _N and enc < 2000:
                enc += 1
                sp = rng.choice(ROSTER)
                chance = min(
                    0.95,
                    RARITY_CATCH_BASE[sp.rarity] * (1 + 0.04 * (plevel - 1)),
                )
                if rng.random() < chance:
                    have.add(sp.element)
            totals.append(enc)
        out[plevel] = statistics.mean(totals)
    return out


def sample_battle_log(rng: random.Random) -> list[str]:
    """A readable 1v1 (setup vs best-damage) so the owner can eyeball the feel."""
    a = Mon(BY_ELEMENT["Ember"][0], 12)
    b = Mon(BY_ELEMENT["Bramble"][1], 12)  # Ember > Bramble (a strong matchup)
    log = [
        f"{a.species.name} (Ember L12, {a.max_hp}hp) vs "
        f"{b.species.name} (Bramble L12, {b.max_hp}hp)",
    ]
    turn = 0
    while a.cur_hp > 0 and b.cur_hp > 0 and turn < 40:
        turn += 1
        first, fp, second, sp = (
            (a, policy_setup, b, policy_best_damage)
            if a.spd >= b.spd
            else (b, policy_best_damage, a, policy_setup)
        )
        for actor, policy, target in ((first, fp, second), (second, sp, first)):
            if actor.cur_hp <= 0 or target.cur_hp <= 0:
                continue
            move = policy(actor, target, rng)
            if move.kind == "buff":
                actor.apply_buff(move.stat)
                log.append(
                    f"  T{turn}: {actor.species.name} uses {move.name} (+{move.stat})",
                )
            else:
                dmg = move_damage(actor, target, move, rng)
                target.cur_hp -= dmg
                eff = effectiveness(move.mtype, target.species.element)
                tag = (
                    " super-effective!"
                    if eff > 1
                    else (" resisted." if eff < 1 else "")
                )
                log.append(
                    f"  T{turn}: {actor.species.name} uses {move.name} → "
                    f"{dmg} dmg{tag} ({max(0, target.cur_hp)}hp left)",
                )
        if a.cur_hp <= 0:
            log.append(f"  {a.species.name} faints — {b.species.name} wins.")
        elif b.cur_hp <= 0:
            log.append(f"  {b.species.name} faints — {a.species.name} wins.")
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
    print(
        f"Roster: {len(ROSTER)} creatures · {_N} elements + Normal · "
        f"4 moves each · teams of {TEAM_SIZE}",
    )
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

    # 2. Raw-level dominance (INFORMATIONAL — motivates the normalization rule)
    print("\n[2] Raw-level dominance — higher-level win-rate vs gap (same element)")
    lf = sim_level_fairness(rng, args.trials)
    for gap, wr in lf:
        print(f"    +{gap:>2} levels → {wr * 100:5.1f}% win")
    gap2 = dict(lf).get(2, 1.0)
    print(f"    → a +2 gap already wins {gap2 * 100:.0f}%: raw levels DECIDE 1v1s.")
    print(
        "    → DESIGN RULE: PvP normalizes to a flat level (informational, not a flag).",
    )

    # 2b. Normalized fairness (the rule in action — a pass/fail gate)
    nf = sim_normalized_fairness(rng, args.trials)
    unbiased = 0.45 <= nf <= 0.55
    warns += not unbiased
    print("\n[2b] Normalized PvP — team-A win-rate, equal-level standard 6v6")
    print(f"    {nf * 100:.1f}%  (target 45–55%, unbiased engine)  {_flag(unbiased)}")

    # 3. Skill impact — smart move-choice + setup + lead order vs a beginner
    print("\n[3] Skill impact — setup + type-aware lead vs beginner (element-spam)")
    si = sim_skill_impact(rng, args.trials)
    good = 0.52 <= si <= 0.80  # rewarded, but not absolute
    warns += not good
    print(f"    skilled win-rate = {si * 100:.1f}%  (target 52–80%)  {_flag(good)}")

    # 3b. Status-move value — setup vs pure best-damage (no buffs)
    print("\n[3b] Status-move value — opening +ATK setup vs damage-only play")
    sv = sim_status_value(rng, args.trials)
    healthy = 0.50 <= sv <= 0.72  # earns its slot, not degenerate
    warns += not healthy
    print(f"    setup win-rate = {sv * 100:.1f}%  (target 50–72%)  {_flag(healthy)}")

    # 4. Catch grind — starter (3) and full standard team (one of each element)
    print("\n[4] Catch grind — encounters to a team")
    cg = sim_catch_grind(rng, args.trials // 4 or 1, team_size=3)
    for plevel, mean in cg.items():
        print(f"    starter (3): player L{plevel}: {mean:.1f} encounters")
    stg = sim_standard_team_grind(rng, args.trials // 4 or 1)
    for plevel, mean in stg.items():
        print(
            f"    full team (one of each element): player L{plevel}: {mean:.1f} encounters",
        )
    grind_ok = cg.get(1, 99) <= 12  # a fresh player gets a starter team in a sitting
    warns += not grind_ok
    print(f"    fresh player ≤ ~12 encounters for a 3-mon starter?  {_flag(grind_ok)}")

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
