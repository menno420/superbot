"""Tests for the creature PvP battle engine (``utils.creatures.battle``).

The engine graduated the combat math from the Monte-Carlo playability sim
(``tools/game_sim/creature_battle_sim.py``) that validated the v1 ruleset
**PLAYABLE** before it touched ``disbot/``. These tests **re-validate the sim's
fairness gates inside the bot** so the runtime engine can't silently drift from
the design that was signed off:

* the **type chart is symmetric** (each element strong vs 2, weak vs 2),
* **equal-stat type balance** sits at ~50% (no element dominates),
* **normalized PvP is unbiased** (~50% once level is removed),
* **skill is rewarded but not absolute**, and the **status moves earn their slot**,
* **raw levels decide a 1v1** — the finding that motivates PvP level-normalization.

Every Monte-Carlo check uses a **fixed seed**, so the results are deterministic
(not flaky) and the bands below are generous around the locked values.
"""

from __future__ import annotations

import random
import statistics
from itertools import product

import pytest

from utils.creatures import battle as B
from utils.creatures.creature import CREATURES, Creature


def _synth(
    element: str, *, rarity: str = "Common", archetype: str = "balanced"
) -> Creature:
    """An equal-stats creature for a given element (isolates the *type chart*).

    Holding rarity + archetype constant means two synth creatures differ only by
    element, so a 1v1 between them measures the type matchup alone — not the
    stat spread of whichever catalog representative happened to be picked.
    """
    return Creature(
        name=f"{element}mon",
        element=element,
        rarity=rarity,
        archetype=archetype,
        emoji="x",
    )


@pytest.fixture(scope="module")
def by_element() -> dict[str, list[Creature]]:
    pool: dict[str, list[Creature]] = {}
    for c in CREATURES:
        pool.setdefault(c.element, []).append(c)
    return pool


# --------------------------------------------------------------------------- chart


def test_type_chart_is_symmetric() -> None:
    """Each element beats exactly 2 and loses to exactly 2; neutral vs itself + opposite."""
    for el in B.ELEMENT_CYCLE:
        strong = sum(B.effectiveness(el, d) > 1 for d in B.ELEMENT_CYCLE)
        weak = sum(B.effectiveness(el, d) < 1 for d in B.ELEMENT_CYCLE)
        neutral = sum(B.effectiveness(el, d) == 1 for d in B.ELEMENT_CYCLE)
        assert (strong, weak, neutral) == (2, 2, 2), el


def test_normal_ignores_the_type_chart() -> None:
    for d in B.ELEMENT_CYCLE:
        assert B.effectiveness(B.NORMAL_TYPE, d) == B.NEUTRAL_MULT


def test_effectiveness_unknown_element_is_neutral() -> None:
    """A malformed catalog element can never raise mid-battle — it falls back to 1.0."""
    assert B.effectiveness("Plasma", "Ember") == B.NEUTRAL_MULT
    assert B.effectiveness("Ember", "Plasma") == B.NEUTRAL_MULT


def test_type_chart_uses_canonical_cycle_not_catalog_order() -> None:
    """The chart is pinned to ELEMENT_CYCLE, independent of catalog first-seen order."""
    # Ember beats the next two on the cycle and loses to the previous two.
    assert B.effectiveness("Ember", "Tide") == B.STRONG_MULT
    assert B.effectiveness("Ember", "Bramble") == B.STRONG_MULT
    assert B.effectiveness("Ember", "Stone") == B.WEAK_MULT
    assert B.effectiveness("Ember", "Gust") == B.WEAK_MULT
    assert B.effectiveness("Ember", "Spark") == B.NEUTRAL_MULT  # opposite


# --------------------------------------------------------------------------- stats


def test_derive_stats_is_deterministic_and_budgeted() -> None:
    c = _synth("Ember", rarity="Rare", archetype="balanced")
    s1 = B.derive_stats(c)
    s2 = B.derive_stats(c)
    assert s1 == s2
    # Balanced split of the Rare budget — total lands on the budget (rounding aside).
    assert abs(s1.total - B.RARITY_BUDGET["Rare"]) <= 2
    assert s1.hp == s1.atk == s1.df == s1.spd  # balanced weights → equal split


def test_rarity_raises_the_stat_budget() -> None:
    common = B.derive_stats(_synth("Tide", rarity="Common")).total
    epic = B.derive_stats(_synth("Tide", rarity="Epic")).total
    assert epic > common


def test_archetype_shapes_the_spread() -> None:
    attacker = B.derive_stats(_synth("Spark", archetype="attacker"))
    tank = B.derive_stats(_synth("Spark", archetype="tank"))
    assert attacker.atk > tank.atk
    assert tank.df > attacker.df


def test_unknown_rarity_archetype_fall_back() -> None:
    weird = Creature("X", "Ember", "Mythic", "wizard", "x")
    s = B.derive_stats(weird)  # must not raise
    assert s.total > 0


# --------------------------------------------------------------------------- moves


def test_moves_for_is_the_four_move_kit() -> None:
    moves = B.moves_for(_synth("Gust"))
    assert len(moves) == 4
    kinds = sorted(m.kind for m in moves)
    assert kinds == sorted([B.DAMAGE, B.DAMAGE, B.BUFF, B.BUFF])
    dmg = [m for m in moves if m.kind == B.DAMAGE]
    assert {m.mtype for m in dmg} == {B.NORMAL_TYPE, "Gust"}
    assert {m.stat for m in moves if m.kind == B.BUFF} == {"atk", "def"}


def test_element_move_out_powers_normal_at_base() -> None:
    assert B.ELEMENT_POWER > B.NORMAL_POWER


# --------------------------------------------------------------------------- combatant


def test_level_scales_hp_and_offense() -> None:
    c = _synth("Stone")
    low = B.Combatant(c, 1)
    high = B.Combatant(c, 50)
    assert high.max_hp > low.max_hp
    assert high.atk > low.atk
    assert high.spd > low.spd


def test_buffs_are_capped() -> None:
    m = B.Combatant(_synth("Ember"), 10)
    base = m.atk
    for _ in range(10):  # spam +ATK well past the cap
        m.apply_buff("atk")
    assert m.atk == pytest.approx(base * (1 + B.BUFF_CAP))


def test_buff_does_not_change_max_hp() -> None:
    m = B.Combatant(_synth("Ember"), 10)
    hp = m.max_hp
    m.apply_buff("def")
    assert m.max_hp == hp


# --------------------------------------------------------------------------- resolution


def test_resolve_battle_has_a_winner_and_a_log() -> None:
    rng = random.Random(1)
    a = B.build_team([_synth(el) for el in B.ELEMENT_CYCLE], B.NORMALIZED_LEVEL)
    b = B.build_team([_synth(el) for el in B.ELEMENT_CYCLE], B.NORMALIZED_LEVEL)
    out = B.resolve_battle(a, b, rng=rng)
    assert out.winner in ("a", "b")
    assert out.events
    # The losing team's last combatant is fainted.
    loser_last = a[-1] if out.winner == "b" else b[-1]
    assert loser_last.fainted
    # Every "faint" event leaves its target at 0 HP.
    assert all(e.target_hp_left == 0 for e in out.events if e.faint)


def test_resolve_battle_is_deterministic_for_a_seed() -> None:
    def play() -> B.BattleOutcome:
        rng = random.Random(99)
        a = B.build_team([_synth(el) for el in B.ELEMENT_CYCLE], 30)
        b = B.build_team([_synth(el) for el in reversed(B.ELEMENT_CYCLE)], 30)
        return B.resolve_battle(a, b, rng=rng)

    first, second = play(), play()
    assert first.winner == second.winner
    assert first.events == second.events


def test_super_effective_hits_harder_than_resisted(
    by_element: dict[str, list[Creature]],
) -> None:
    """A strong matchup out-damages a resisted one for the same attacker (averaged jitter)."""
    rng = random.Random(3)
    attacker = B.Combatant(_synth("Ember", rarity="Epic"), 50)
    strong_t = B.Combatant(_synth("Tide"), 50)  # Ember > Tide
    resist_t = B.Combatant(_synth("Stone"), 50)  # Ember < Stone
    el_move = next(m for m in B.moves_for(attacker.creature) if m.mtype == "Ember")
    strong = statistics.mean(
        B.move_damage(attacker, strong_t, el_move, rng) for _ in range(400)
    )
    resisted = statistics.mean(
        B.move_damage(attacker, resist_t, el_move, rng) for _ in range(400)
    )
    assert strong > resisted


def test_standard_team_is_one_of_each_available_element(
    by_element: dict[str, list[Creature]],
) -> None:
    rng = random.Random(5)
    team = B.standard_team(CREATURES, rng)
    assert len(team) == len(B.ELEMENT_CYCLE)
    assert {m.element for m in team} == set(B.ELEMENT_CYCLE)
    assert all(m.level == B.NORMALIZED_LEVEL for m in team)


def test_standard_team_from_partial_pool_is_smaller_but_legal() -> None:
    rng = random.Random(5)
    pool = [c for c in CREATURES if c.element in ("Ember", "Tide")]
    team = B.standard_team(pool, rng)
    assert {m.element for m in team} == {"Ember", "Tide"}


def test_fresh_team_resets_state() -> None:
    rng = random.Random(2)
    team = B.build_team([_synth(el) for el in B.ELEMENT_CYCLE], 40)
    team[0].cur_hp = 1
    team[0].apply_buff("atk")
    clone = B.fresh_team(team)
    assert clone[0].cur_hp == clone[0].max_hp
    assert clone[0].atk_stage == 0.0


# --------------------------------------------------------------------------- fairness gates
# Re-validating the sim's signed-off design numbers inside the runtime engine.
# Each uses a fixed seed → deterministic; the bands are generous around the
# locked values, not tight targets to chase.


def test_equal_stat_type_balance_is_even() -> None:
    """With stats held equal, no element wins materially more than 50% (chart is fair)."""
    rng = random.Random(42)
    wins: dict[str, list[float]] = {el: [] for el in B.ELEMENT_CYCLE}
    for atk_el, def_el in product(B.ELEMENT_CYCLE, B.ELEMENT_CYCLE):
        if atk_el == def_el:
            continue
        w = sum(
            B.resolve_battle(
                [B.Combatant(_synth(atk_el), 10)],
                [B.Combatant(_synth(def_el), 10)],
                rng=rng,
            ).a_won
            for _ in range(300)
        )
        wins[atk_el].append(w / 300)
    rates = {el: statistics.mean(v) for el, v in wins.items()}
    assert all(0.45 <= r <= 0.55 for r in rates.values()), rates
    assert (max(rates.values()) - min(rates.values())) < 0.05  # locked spread ~1.3 pts


def test_normalized_pvp_is_unbiased(by_element: dict[str, list[Creature]]) -> None:
    """Equal-level standard 6v6 sits near 50% — the engine has no structural side bias."""
    rng = random.Random(42)
    w = 0
    for _ in range(500):
        a = B.standard_team(CREATURES, rng)
        b = B.standard_team(CREATURES, rng)
        if B.resolve_battle(B.fresh_team(a), B.fresh_team(b), rng=rng).a_won:
            w += 1
    assert 0.43 <= w / 500 <= 0.57  # locked ~48.8%


def test_skill_is_rewarded_but_not_absolute(
    by_element: dict[str, list[Creature]],
) -> None:
    """Setup + type-aware lead beats a beginner clearly (>~55%) yet never dominates."""
    rng = random.Random(42)
    w = 0
    for _ in range(500):
        a = B.standard_team(CREATURES, rng, level=20)
        b = B.standard_team(CREATURES, rng, level=20)
        rng.shuffle(b)
        skilled = B.order_type_aware(a, b[0])
        if B.resolve_battle(
            B.fresh_team(skilled),
            B.fresh_team(b),
            rng=rng,
            policy_a=B.policy_setup,
            policy_b=B.policy_naive_element,
        ).a_won:
            w += 1
    assert 0.55 <= w / 500 <= 0.82  # locked ~69.4%


def test_status_moves_earn_their_slot(by_element: dict[str, list[Creature]]) -> None:
    """An opening +ATK setup beats pure best-damage (>50%) without being degenerate."""
    rng = random.Random(42)
    w = 0
    for _ in range(500):
        a = B.standard_team(CREATURES, rng, level=20)
        b = B.standard_team(CREATURES, rng, level=20)
        if B.resolve_battle(
            B.fresh_team(a),
            B.fresh_team(b),
            rng=rng,
            policy_a=B.policy_setup,
            policy_b=B.policy_best_damage,
        ).a_won:
            w += 1
    assert 0.50 <= w / 500 <= 0.72  # locked ~59.6%


def test_raw_levels_decide_a_1v1(by_element: dict[str, list[Creature]]) -> None:
    """A +2 level gap wins ~100% — the finding that motivates PvP normalization.

    Same creature both sides isolates *level* from *type*; the steep curve is why
    ranked PvP normalizes to a flat level (anti-pay-to-win, Q-0039).
    """
    species = by_element["Tide"][0]
    rng = random.Random(42)
    higher = sum(
        B.resolve_battle(
            [B.Combatant(species, 12)], [B.Combatant(species, 10)], rng=rng
        ).a_won
        for _ in range(500)
    )
    assert higher / 500 > 0.90  # locked 100%

    rng = random.Random(7)
    even = sum(
        B.resolve_battle(
            [B.Combatant(species, 10)], [B.Combatant(species, 10)], rng=rng
        ).a_won
        for _ in range(500)
    )
    assert 0.40 <= even / 500 <= 0.60  # same level → coin-flip
