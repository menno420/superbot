"""The V-16 gear-set numbers authority (Q-0092) — sim-sane, monotonic, pinned.

The owner delegated the 30-item stat/economy tables to the build session
("full numbers authority": simulation-sane, monotonic per tier, documented).
These tests ARE that contract:

* **Monotonic** — within every family, each tier is strictly better than the
  one below (summed stats), and prices/values/durability rise with it.
* **Sim-sane** — a deterministic duel simulation over the real ``_Duel``
  combat math pins win-rate bands: mirror fights stay fair, a one-tier gear
  gap is an edge (not an auto-win), and full diamond vs bare is earned
  dominance.  Retuning the tables outside these bands fails CI — the Q-0087
  "simulation as the balance methodology" decision applied to gear.

Design rationale: docs/planning/gear-set-numbers-2026-06-11.md.
"""

from __future__ import annotations

import random
from dataclasses import astuple
from types import SimpleNamespace

from cogs.deathmatch_cog import BASE_ATTACK_DAMAGE, _Duel
from utils import equipment as eq
from utils.mining import items, market
from utils.mining.recipes import load_recipes

_FAMILIES = ("sword", "shield", "helmet", "chestplate", "leggings", "boots")


def _full_set(tier: str) -> dict[str, str]:
    return {slot: f"{tier} {fam}" for slot, fam in zip(eq.SET_SLOTS, _FAMILIES)}


def _power(item: str) -> int:
    return sum(astuple(eq.item_stats(item)))


# ---------------------------------------------------------------------------
# Monotonicity — every ladder strictly improves with tier
# ---------------------------------------------------------------------------


def test_every_family_ladder_is_strictly_stronger_per_tier():
    for family in _FAMILIES:
        ladder = [f"{tier} {family}" for tier in eq.TIER_ORDER]
        powers = [_power(item) for item in ladder]
        assert powers == sorted(set(powers)), (family, powers)


def test_starters_sit_strictly_below_bronze():
    assert _power("sword") < _power("bronze sword")
    assert _power("shield") < _power("bronze shield")


def test_per_tier_set_totals_rise_monotonically():
    damage, defense, health = [], [], []
    for tier in eq.TIER_ORDER:
        stats = eq.compute_stats(_full_set(tier))
        damage.append(stats.damage)
        defense.append(stats.defense)
        health.append(stats.max_health)
    assert damage == sorted(set(damage)), damage
    assert health == sorted(set(health)), health
    assert defense == sorted(defense), defense  # ties allowed, never a drop


def test_prices_values_and_durability_rise_with_tier():
    for family in _FAMILIES:
        ladder = [f"{tier} {family}" for tier in eq.TIER_ORDER]
        prices = [market.buy_price(i) for i in ladder]
        values = [items.item_value(i) for i in ladder]
        durability = [eq.max_durability(i) for i in ladder]
        assert None not in prices and prices == sorted(set(prices)), (family, prices)
        assert values == sorted(set(values)), (family, values)
        assert None not in durability and durability == sorted(durability), family


# ---------------------------------------------------------------------------
# Economy alignment — forge path + no-arbitrage
# ---------------------------------------------------------------------------


def test_every_set_item_is_forged_from_its_tier_ore():
    recipes = load_recipes()
    for tier in eq.TIER_ORDER:
        for family in _FAMILIES:
            name = f"{tier} {family}"
            assert name in recipes, f"{name!r} has no forge recipe"
            assert tier in recipes[name], (name, recipes[name])


def test_buying_always_costs_more_than_the_materials_sell_for():
    recipes = load_recipes()
    for tier in eq.TIER_ORDER:
        for family in _FAMILIES:
            name = f"{tier} {family}"
            material_value = sum(
                items.item_value(mat) * qty for mat, qty in recipes[name].items()
            )
            price = market.buy_price(name)
            assert price is not None and price > material_value, (
                f"{name!r}: shop {price} must exceed material value "
                f"{material_value} or crafting stops being the cheaper path"
            )


def test_every_wearing_item_is_repairable_via_the_shop_knob():
    # workshop.repair_base derives from GEAR_SHOP — an item that wears but
    # has no shop row would silently become unrepairable.
    missing = [n for n in eq.MAX_DURABILITY if market.buy_price(n) is None]
    assert not missing, missing


# ---------------------------------------------------------------------------
# Sim-sanity — the duel bands (deterministic, real combat math)
# ---------------------------------------------------------------------------


def test_full_diamond_defense_stays_below_the_base_attack():
    # The flat-reduction formula cliffs when defense reaches the base attack:
    # every bare hit would floor at 1.  Pin the headroom.
    stats = eq.compute_stats(_full_set("diamond"))
    assert stats.defense < BASE_ATTACK_DAMAGE, stats.defense


def _duel_p1_winrate(
    p1_gear: dict[str, str],
    p2_gear: dict[str, str],
    *,
    n: int = 400,
) -> float:
    """Share of *n* always-attack duels won by player 1 (seeded, alternating
    first mover so first-strike advantage cancels out)."""
    rng_seed = 1234
    random.seed(rng_seed)
    p1 = SimpleNamespace(id=1, display_name="One")
    p2 = SimpleNamespace(id=2, display_name="Two")
    wins = 0
    for round_no in range(n):
        duel = _Duel(
            p1,
            p2,
            p1_stats=eq.compute_stats(p1_gear),
            p2_stats=eq.compute_stats(p2_gear),
        )
        attacker, defender = (
            (p1, p2) if round_no % 2 == 0 else (p2, p1)
        )  # alternate who strikes first
        while duel.player1_hp > 0 and duel.player2_hp > 0:
            duel.attack(attacker.id, defender.id)
            attacker, defender = defender, attacker
        if duel.player2_hp <= 0:
            wins += 1
    return wins / n


def test_mirror_fight_is_fair():
    rate = _duel_p1_winrate(_full_set("iron"), _full_set("iron"))
    assert 0.40 <= rate <= 0.60, rate


def test_a_single_piece_tier_gap_is_an_edge_not_a_decision():
    # Measured WITHOUT set bonuses in play (both sides one piece short of a
    # set): one piece a tier up tilts the fight, it must not decide it.
    for slot, upgrade in (
        (eq.WEAPON, "silver sword"),
        (eq.CHESTPLATE, "silver chestplate"),
        (eq.BOOTS, "silver boots"),
    ):
        base = _full_set("iron")
        del base[eq.HELMET]  # no helmet → no set bonus on either side
        upgraded = dict(base)
        upgraded[slot] = upgrade
        rate = _duel_p1_winrate(upgraded, base)
        # Always-attack amplifies small edges (real play adds defend timing);
        # the contract is "favoured, never guaranteed".
        assert 0.50 <= rate <= 0.85, (upgrade, rate)


def test_one_full_set_tier_gap_wins_decisively():
    # A complete set one tier higher (six pieces + bonus) is a major
    # investment — it should win clearly, but never become a guaranteed
    # stomp the simulation can't distinguish from a bug.
    for lower, higher in zip(eq.TIER_ORDER, eq.TIER_ORDER[1:]):
        rate = _duel_p1_winrate(_full_set(higher), _full_set(lower))
        assert 0.75 <= rate <= 0.995, (lower, higher, rate)


def test_breaking_a_complete_set_for_one_higher_piece_is_a_downgrade():
    # The intentional collection breakpoint: the same-tier bonus outweighs a
    # single next-tier piece, so "upgrade by batches" is the design.  The
    # Gear panel warns ("⚠ breaks set bonus") and best_loadout is set-aware
    # because of exactly this dynamic.
    broken = _full_set("iron")
    broken[eq.CHESTPLATE] = "silver chestplate"
    rate = _duel_p1_winrate(broken, _full_set("iron"))
    assert rate < 0.50, rate


def test_full_diamond_vs_bare_is_earned_dominance():
    rate = _duel_p1_winrate(_full_set("diamond"), {})
    assert rate >= 0.90, rate


def test_bare_vs_bare_unchanged_by_the_set_model():
    # The historical 100 HP / 15-damage duel must be untouched.
    duel = _Duel(
        SimpleNamespace(id=1, display_name="One"),
        SimpleNamespace(id=2, display_name="Two"),
    )
    assert duel.player1_max_hp == duel.player2_max_hp == 100
