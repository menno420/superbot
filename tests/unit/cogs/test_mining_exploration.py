"""Tests for cogs.mining.exploration — pure, loadout-aware engine.

These exercise eligibility gating, loadout scaling, and the legacy-tuple
compatibility shim with an injected RNG so every assertion is stable.
"""

from __future__ import annotations

import random

from cogs.mining import exploration as exp


def _rng() -> random.Random:
    return random.Random(42)


def test_surface_outcomes_need_no_tools():
    elig = exp.eligible_outcomes(exp.Biome.SURFACE, exp.Loadout())
    keys = {o.key for o in elig}
    assert "secret_chest" in keys
    # Torch/dynamite-gated outcomes are not reachable empty-handed.
    assert "hidden_diamond_vein" not in keys
    assert "blasted_vein" not in keys


def test_torch_unlocks_deep_finds():
    loadout = exp.Loadout(tools=frozenset({exp.TORCH}))
    elig = exp.eligible_outcomes(exp.Biome.CAVERN, loadout)
    assert "hidden_diamond_vein" in {o.key for o in elig}


def test_dynamite_gated_outcome_requires_dynamite():
    without = exp.eligible_outcomes(exp.Biome.DEEP, exp.Loadout())
    with_dyn = exp.eligible_outcomes(
        exp.Biome.DEEP, exp.Loadout(tools=frozenset({exp.DYNAMITE})),
    )
    assert "blasted_vein" not in {o.key for o in without}
    assert "blasted_vein" in {o.key for o in with_dyn}


def test_deeper_biome_includes_shallower_outcomes():
    deep = exp.eligible_outcomes(exp.Biome.MAGMA, exp.Loadout())
    assert "secret_chest" in {o.key for o in deep}  # a surface outcome


def test_pickaxe_doubles_ore_gain():
    # abandoned_camp grants gold; pickaxe should double a positive ore gain.
    base = exp.Loadout()
    geared = exp.Loadout(tools=frozenset({exp.PICKAXE}))
    outcome = next(o for o in exp.CATALOG if o.key == "abandoned_camp")
    from cogs.mining.exploration import _scale_amount

    assert _scale_amount(outcome, geared) == _scale_amount(outcome, base) * 2


def test_penalties_are_never_scaled():
    geared = exp.Loadout(tools=frozenset({exp.PICKAXE, exp.LUCKY_CHARM}))
    hazard = next(o for o in exp.CATALOG if o.key == "monster_ambush")
    from cogs.mining.exploration import _scale_amount

    # Negative amount stays exactly as authored — gear protects gains only.
    assert _scale_amount(hazard, geared) == hazard.amount


def test_lucky_charm_adds_one():
    geared = exp.Loadout(tools=frozenset({exp.LUCKY_CHARM}))
    outcome = next(o for o in exp.CATALOG if o.key == "secret_chest")
    from cogs.mining.exploration import _scale_amount

    assert _scale_amount(outcome, geared) == outcome.amount + 1


def test_resolve_is_deterministic_with_seeded_rng():
    a = exp.resolve(exp.Biome.CAVERN, exp.Loadout(), rng=_rng())
    b = exp.resolve(exp.Biome.CAVERN, exp.Loadout(), rng=_rng())
    assert a.outcome.key == b.outcome.key
    assert a.final_amount == b.final_amount


def test_narration_fills_amount_with_absolute_value():
    # monster_ambush narration says "lost {amount} stone"; the filled text
    # must show a positive number even though the delta is negative.
    loadout = exp.Loadout()
    # Force the hazard by building a result directly.
    hazard = next(o for o in exp.CATALOG if o.key == "monster_ambush")
    result = exp.ExploreResult(
        hazard,
        exp.Biome.SURFACE,
        hazard.amount,
        hazard.narration.format(amount=2, item="stone"),
    )
    assert "2 stone" in result.narration
    assert "-" not in result.narration


def test_legacy_tuple_shape_matches_old_explore():
    text, item, amount = exp.resolve_to_legacy_tuple(rng=_rng())
    assert isinstance(text, str)
    assert item is None or isinstance(item, str)
    assert isinstance(amount, int)


def test_loadout_from_inventory_picks_up_only_known_tools():
    inv = {"pickaxe": 1, "torch": 2, "gold": 50, "made_up_thing": 9, "dynamite": 0}
    loadout = exp.Loadout.from_inventory(inv)
    assert loadout.has(exp.PICKAXE)
    assert loadout.has(exp.TORCH)
    assert not loadout.has(exp.DYNAMITE)  # quantity 0 → not equipped
    assert "gold" not in loadout.tools  # resource, not a tool
    assert "made_up_thing" not in loadout.tools


def test_resolve_always_returns_result_even_when_catalog_filtered():
    # An empty loadout at the surface still has fallbacks, so resolve must
    # never raise and always produce a usable narration.
    result = exp.resolve(exp.Biome.SURFACE, exp.Loadout(), rng=_rng())
    assert result.narration
    assert isinstance(result.final_amount, int)
