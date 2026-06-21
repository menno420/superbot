"""The creature PvP battle engine — pure, deterministic combat (creature-game v1).

The runtime side of the [creature-game plan](docs/planning/creature-game-design-and-sim-2026-06-20.md)
§4 *Battle*: the **level-normalized 6v6 turn-based** PvP ruleset, graduated from the
Monte-Carlo playability simulator (``tools/game_sim/creature_battle_sim.py``) that
validated it **PLAYABLE** before any of it touched ``disbot/``. The sim's combat
math lives here now as the single runtime source of truth; the sim stays the
design/tuning tool.

Where this lives (a noted deviation from plan §4 wording)
---------------------------------------------------------
Plan §4 sketches ``services/creature_battle_engine.py``. This module is **pure
combat math** — no DB, no audit, no Discord, no IO — so it belongs in
``utils/creatures/`` beside its pure-domain siblings :mod:`utils.creatures.creature`
and :mod:`utils.creatures.encounters`, not the ``services/`` audited-write layer.
The ``services/`` seam enters only when a battle **persists a result / awards xp /
emits an audit event** (the later cog-wiring slice); even then the math stays here
and a thin service orchestrates the side effects.

The v1 ruleset (owner design, sim-validated)
---------------------------------------------
- **6 elements** arranged on a symmetric cycle (``ELEMENT_CYCLE``) so each is
  strong vs the next two (``1.5×``), weak vs the previous two (``0.67×``), neutral
  vs its opposite — plus a neutral **Normal** damage type (always ``1.0×``).
- **Stats are derived, not stored**: a creature's budget = ``RARITY_BUDGET[rarity]``
  split across HP/ATK/DEF/SPD by its archetype's weights (the "creature is a data
  row, not code" design — :mod:`utils.creatures.creature` carries only the catalog
  facets; battle stats derive here).
- **4 moves each**: a reliable **Normal** hit, a stronger **element** hit (the type
  chart applies), and two **self-buff** status moves (+DEF / +ATK, capped).
- **Teams of 6**, one of each element; the lead fights until it faints, then the
  next comes in; faster SPD acts first.
- **★ PvP normalizes to a flat level** (``NORMALIZED_LEVEL``). Raw levels make a
  1v1 deterministic (a +2 gap wins ~100%), which would make ranked PvP a
  grind/whale-fest — the **pay-to-win** outcome Q-0039 forbids. Flat-level PvP makes
  **types + team-building + ordering + move choice** decide, so it rewards *skill*,
  not *time spent*. (Raw levels still matter for PvE/collection prestige.)

Pure + stdlib-only and deterministic given a seeded :class:`random.Random`, so the
whole engine is unit-testable — and the test suite re-validates the sim's fairness
gates inside the bot.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field

from utils.creatures.creature import Creature

# ---------------------------------------------------------------------------
# Type chart — the canonical element cycle (NOT the catalog's first-seen order)
# ---------------------------------------------------------------------------

#: The six elements in their **canonical cyclic order**. The type chart is defined
#: by position on this cycle, so it must be a fixed design constant — never derived
#: from :data:`utils.creatures.creature.ELEMENTS` (which is catalog first-seen order
#: and would silently re-wire effectiveness if the catalog were reordered).
ELEMENT_CYCLE: tuple[str, ...] = ("Ember", "Tide", "Bramble", "Spark", "Stone", "Gust")
_N = len(ELEMENT_CYCLE)
_ELEMENT_INDEX: dict[str, int] = {el: i for i, el in enumerate(ELEMENT_CYCLE)}

#: A seventh DAMAGE type carried by every creature's reliable move — neutral vs
#: everything (it ignores the type chart). The safe fallback vs a resistant target.
NORMAL_TYPE = "Normal"

STRONG_MULT = 1.5
WEAK_MULT = 0.67
NEUTRAL_MULT = 1.0


def effectiveness(attack_type: str, defender_element: str) -> float:
    """Type multiplier of *attack_type* (an element or ``Normal``) vs *defender_element*.

    Normal ignores the chart (always ``1.0``). An element beats the next two on the
    cycle (``1.5``), loses to the previous two (``0.67``), and is neutral vs its
    opposite (``1.0``). Unknown elements fall back to neutral so a malformed catalog
    row can never raise mid-battle.
    """
    if attack_type == NORMAL_TYPE:
        return NEUTRAL_MULT
    a = _ELEMENT_INDEX.get(attack_type)
    d = _ELEMENT_INDEX.get(defender_element)
    if a is None or d is None:
        return NEUTRAL_MULT
    delta = (d - a) % _N
    if delta in (1, 2):
        return STRONG_MULT
    if delta in (_N - 1, _N - 2):
        return WEAK_MULT
    return NEUTRAL_MULT


# ---------------------------------------------------------------------------
# Stat derivation — budget (rarity) split by archetype weights
# ---------------------------------------------------------------------------

#: Total stat budget per rarity — rarer = stronger, but level + type + move choice
#: still let a Common counter an Epic. Graduated from the sim's ``RARITY_BUDGET``.
RARITY_BUDGET: dict[str, int] = {
    "Common": 200,
    "Uncommon": 230,
    "Rare": 260,
    "Epic": 300,
}
_DEFAULT_BUDGET = RARITY_BUDGET["Common"]

#: Archetype stat weights ``(hp, atk, def, spd)`` — the budget is split in these
#: proportions. Graduated verbatim from the sim's ``_roster`` archetype table.
ARCHETYPE_WEIGHTS: dict[str, tuple[float, float, float, float]] = {
    "attacker": (0.9, 1.3, 0.7, 1.1),
    "tank": (1.3, 0.8, 1.3, 0.6),
    "balanced": (1.0, 1.0, 1.0, 1.0),
    "speedster": (0.8, 1.2, 0.7, 1.3),
}
_DEFAULT_WEIGHTS = ARCHETYPE_WEIGHTS["balanced"]


@dataclass(frozen=True)
class BattleStats:
    """A creature's derived base battle stats (before level/buff scaling)."""

    hp: int
    atk: int
    df: int
    spd: int

    @property
    def total(self) -> int:
        return self.hp + self.atk + self.df + self.spd


def derive_stats(creature: Creature) -> BattleStats:
    """Derive HP/ATK/DEF/SPD for *creature* from its rarity budget + archetype.

    Deterministic and pure — the same creature always yields the same stats, so the
    catalog stays "a data row, not code" while battle stats stay reproducible.
    """
    budget = RARITY_BUDGET.get(creature.rarity, _DEFAULT_BUDGET)
    hp_w, atk_w, df_w, spd_w = ARCHETYPE_WEIGHTS.get(
        creature.archetype,
        _DEFAULT_WEIGHTS,
    )
    total = hp_w + atk_w + df_w + spd_w
    return BattleStats(
        hp=round(budget * hp_w / total),
        atk=round(budget * atk_w / total),
        df=round(budget * df_w / total),
        spd=round(budget * spd_w / total),
    )


# ---------------------------------------------------------------------------
# Moves — 4 per creature: Normal damage, element damage, +DEF buff, +ATK buff
# ---------------------------------------------------------------------------

NORMAL_POWER = 9  # reliable, always ×1.0
ELEMENT_POWER = 12  # signature — higher base, but the type chart applies
BUFF_STEP = 0.25  # each status use shifts the stat +25% …
BUFF_CAP = 0.50  # … capped at +50% so buff-spam isn't degenerate
TEAM_SIZE = 6  # the "6-mon team" standard (one of each element)

#: Original signature-move display names per element (no Pokémon move IP).
ELEMENT_MOVE_NAME: dict[str, str] = {
    "Ember": "Cinderlash",
    "Tide": "Tidal Crash",
    "Bramble": "Thorn Volley",
    "Spark": "Voltstrike",
    "Stone": "Boulder Smash",
    "Gust": "Galeforce",
}

# Move "kinds".
DAMAGE = "damage"
BUFF = "buff"


@dataclass(frozen=True)
class Move:
    """One move. Damage moves carry a type + power; buff moves carry a target stat."""

    name: str
    kind: str  # DAMAGE | BUFF
    mtype: str  # damage type (NORMAL_TYPE or an element); "" for buffs
    power: int  # damage moves only
    stat: str  # buff moves only: "atk" | "def"


def moves_for(creature: Creature) -> list[Move]:
    """The four v1 moves: Normal hit, element hit, defensive buff, offensive buff."""
    element_move = ELEMENT_MOVE_NAME.get(creature.element, f"{creature.element} Strike")
    return [
        Move("Strike", DAMAGE, NORMAL_TYPE, NORMAL_POWER, ""),
        Move(element_move, DAMAGE, creature.element, ELEMENT_POWER, ""),
        Move("Bulwark", BUFF, "", 0, "def"),  # defensive (+DEF)
        Move("Onslaught", BUFF, "", 0, "atk"),  # offensive (+ATK)
    ]


# ---------------------------------------------------------------------------
# Combatant — a creature instantiated into a battle at a level, with live state
# ---------------------------------------------------------------------------

HP_PER_LVL = 0.06
OFF_PER_LVL = 0.035

#: The flat level every creature is normalized to in ranked PvP (the anti-P2W
#: rule). The exact value is cosmetic — the engine is symmetric in level — but a
#: round, clearly "high" number reads as an even, fully-grown matchup.
NORMALIZED_LEVEL = 50


@dataclass
class Combatant:
    """A creature in battle: derived stats + level scaling + live HP/buff state."""

    creature: Creature
    level: int
    stats: BattleStats = field(init=False)
    cur_hp: int = field(init=False)
    atk_stage: float = field(default=0.0, init=False)  # additive buff, capped
    def_stage: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        self.stats = derive_stats(self.creature)
        self.cur_hp = self.max_hp

    @property
    def name(self) -> str:
        return self.creature.name

    @property
    def element(self) -> str:
        return self.creature.element

    @property
    def max_hp(self) -> int:
        return round(self.stats.hp * (1 + HP_PER_LVL * (self.level - 1)))

    @property
    def atk(self) -> float:
        return (
            self.stats.atk * (1 + OFF_PER_LVL * (self.level - 1)) * (1 + self.atk_stage)
        )

    @property
    def df(self) -> float:
        return (
            self.stats.df * (1 + OFF_PER_LVL * (self.level - 1)) * (1 + self.def_stage)
        )

    @property
    def spd(self) -> float:
        return self.stats.spd * (1 + OFF_PER_LVL * (self.level - 1))

    @property
    def fainted(self) -> bool:
        return self.cur_hp <= 0

    def apply_buff(self, stat: str) -> None:
        if stat == "atk":
            self.atk_stage = min(BUFF_CAP, self.atk_stage + BUFF_STEP)
        else:
            self.def_stage = min(BUFF_CAP, self.def_stage + BUFF_STEP)


def move_damage(
    attacker: Combatant,
    defender: Combatant,
    move: Move,
    rng: random.Random,
) -> int:
    """Damage *attacker* deals *defender* with *move* (>=1), including 0.85–1.0 jitter."""
    mult = effectiveness(move.mtype, defender.element)
    jitter = rng.uniform(0.85, 1.0)
    raw = (attacker.atk / max(1.0, defender.df)) * move.power * mult * jitter
    return max(1, round(raw))


def expected_damage(attacker: Combatant, defender: Combatant, move: Move) -> float:
    """Jitter-free expected damage of *move* — the policies use it to compare moves."""
    if move.kind != DAMAGE:
        return 0.0
    mult = effectiveness(move.mtype, defender.element)
    return (attacker.atk / max(1.0, defender.df)) * move.power * mult * 0.925


# ---------------------------------------------------------------------------
# Move-selection policies — the skill lever: (actor, target, rng) -> Move
# ---------------------------------------------------------------------------

Policy = Callable[[Combatant, Combatant, random.Random], Move]


def _best_damage_move(actor: Combatant, target: Combatant) -> Move:
    dmg = [m for m in moves_for(actor.creature) if m.kind == DAMAGE]
    return max(dmg, key=lambda m: expected_damage(actor, target, m))


def policy_best_damage(actor: Combatant, target: Combatant, rng: random.Random) -> Move:
    """Skilled *move choice*: the higher-damage of Normal vs element each turn."""
    return _best_damage_move(actor, target)


def policy_naive_element(
    actor: Combatant,
    target: Combatant,
    rng: random.Random,
) -> Move:
    """A beginner: always fire the signature element move, even when resisted."""
    for m in moves_for(actor.creature):
        if m.mtype == actor.element:
            return m
    return moves_for(actor.creature)[0]


def policy_random(actor: Combatant, target: Combatant, rng: random.Random) -> Move:
    """Pick any of the four moves at random (wastes turns on ill-timed buffs)."""
    return rng.choice(moves_for(actor.creature))


def policy_setup(actor: Combatant, target: Combatant, rng: random.Random) -> Move:
    """Skilled move choice + ONE opening +ATK when it is safe.

    Invests a single turn in +ATK when the actor is faster, healthy, hasn't buffed
    yet, and can't KO this turn — then attacks with the best move.
    """
    best = _best_damage_move(actor, target)
    if expected_damage(actor, target, best) >= target.cur_hp:
        return best  # finish the kill, don't waste the turn
    if (
        actor.atk_stage == 0.0
        and actor.cur_hp >= 0.6 * actor.max_hp
        and actor.spd >= target.spd
    ):
        for m in moves_for(actor.creature):
            if m.stat == "atk":
                return m
    return best


# ---------------------------------------------------------------------------
# Battle resolution — structured, replayable turn-by-turn log
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BattleEvent:
    """One resolved action, enough for a cog to render a readable battle log.

    *side* is ``"a"``/``"b"`` (the acting team). For a buff, *damage* is 0 and
    *effectiveness* is 1.0; *target_hp_left* is the defender's HP after the action
    (the actor's own HP for a self-buff). *faint* marks the action that KO'd the
    defender.
    """

    turn: int
    side: str
    actor: str
    move: str
    kind: str
    target: str
    damage: int = 0
    effectiveness: float = NEUTRAL_MULT
    target_hp_left: int = 0
    faint: bool = False


@dataclass(frozen=True)
class BattleOutcome:
    """The result of :func:`resolve_battle`: which side won + the full event log."""

    winner: str  # "a" | "b"
    events: tuple[BattleEvent, ...]

    @property
    def a_won(self) -> bool:
        return self.winner == "a"


_STALL_GUARD = 5000


def _ordered_actors(
    a: Combatant,
    b: Combatant,
    policy_a: Policy,
    policy_b: Policy,
    rng: random.Random,
) -> list[tuple[str, Combatant, Combatant, Policy]]:
    """Faster SPD acts first; an exact tie is a coin-flip, never a fixed A-edge."""
    side_a = ("a", a, b, policy_a)
    side_b = ("b", b, a, policy_b)
    if a.spd > b.spd:
        return [side_a, side_b]
    if b.spd > a.spd:
        return [side_b, side_a]
    return [side_a, side_b] if rng.random() < 0.5 else [side_b, side_a]


def resolve_battle(
    team_a: Sequence[Combatant],
    team_b: Sequence[Combatant],
    *,
    rng: random.Random,
    policy_a: Policy = policy_best_damage,
    policy_b: Policy = policy_best_damage,
) -> BattleOutcome:
    """Run a 6v6 (or N-vN) battle to completion and return the winner + event log.

    The lead of each team fights until it faints, then the next comes in. Mutates
    the passed combatants' battle state (HP/buffs) — callers that reuse a roster
    should build fresh combatants (see :func:`fresh_team`).
    """
    events: list[BattleEvent] = []
    ia = ib = 0
    turn = 0
    guard = 0
    team_a = list(team_a)
    team_b = list(team_b)
    while ia < len(team_a) and ib < len(team_b):
        guard += 1
        if guard > _STALL_GUARD:  # pathological stall guard (never hit at v1 numbers)
            a_hp = sum(m.cur_hp for m in team_a[ia:])
            b_hp = sum(m.cur_hp for m in team_b[ib:])
            return BattleOutcome("a" if a_hp >= b_hp else "b", tuple(events))
        turn += 1
        a, b = team_a[ia], team_b[ib]
        for side, actor, target, policy in _ordered_actors(
            a,
            b,
            policy_a,
            policy_b,
            rng,
        ):
            if actor.fainted or target.fainted:
                continue
            move = policy(actor, target, rng)
            if move.kind == BUFF:
                actor.apply_buff(move.stat)
                events.append(
                    BattleEvent(
                        turn=turn,
                        side=side,
                        actor=actor.name,
                        move=move.name,
                        kind=BUFF,
                        target=actor.name,
                        target_hp_left=actor.cur_hp,
                    ),
                )
            else:
                dmg = move_damage(actor, target, move, rng)
                target.cur_hp -= dmg
                events.append(
                    BattleEvent(
                        turn=turn,
                        side=side,
                        actor=actor.name,
                        move=move.name,
                        kind=DAMAGE,
                        target=target.name,
                        damage=dmg,
                        effectiveness=effectiveness(move.mtype, target.element),
                        target_hp_left=max(0, target.cur_hp),
                        faint=target.fainted,
                    ),
                )
        if a.fainted:
            ia += 1
        if b.fainted:
            ib += 1
    return BattleOutcome("a" if ib >= len(team_b) else "b", tuple(events))


# ---------------------------------------------------------------------------
# Team construction
# ---------------------------------------------------------------------------


def build_team(creatures: Iterable[Creature], level: int) -> list[Combatant]:
    """Instantiate *creatures* into combatants at *level* (order preserved)."""
    return [Combatant(c, level) for c in creatures]


def fresh_team(team: Sequence[Combatant]) -> list[Combatant]:
    """A clean copy of *team* (same creatures + levels, full HP, no buffs).

    For replaying the same roster across trials without HP/buff carryover.
    """
    return [Combatant(m.creature, m.level) for m in team]


def standard_team(
    pool: Sequence[Creature],
    rng: random.Random,
    *,
    level: int = NORMALIZED_LEVEL,
) -> list[Combatant]:
    """A 'one of each element' 6-mon team drawn from *pool* (the owner's standard).

    Picks one random creature per :data:`ELEMENT_CYCLE` element that *pool* covers,
    at the (normalized) *level*. Elements the pool can't cover are simply absent, so
    a partial collection yields a smaller — but legal — team.
    """
    team: list[Combatant] = []
    for el in ELEMENT_CYCLE:
        options = [c for c in pool if c.element == el]
        if options:
            team.append(Combatant(rng.choice(options), level))
    return team


def order_type_aware(
    team: Sequence[Combatant],
    opponent_lead: Combatant,
) -> list[Combatant]:
    """Reorder *team* to lead with whoever best counters *opponent_lead* (skill lever)."""
    return sorted(
        team,
        key=lambda m: -effectiveness(m.element, opponent_lead.element),
    )
