"""Tests for utils.mining.exploration — pure, loadout-aware engine.

These exercise eligibility gating, loadout scaling, and the legacy-tuple
compatibility shim with an injected RNG so every assertion is stable.
"""

from __future__ import annotations

import random

from utils.mining import exploration as exp


def _rng() -> random.Random:
    return random.Random(42)


def test_biome_order_is_canonical_depth_mapping():
    # BIOME_ORDER is the shallow→deep ordering; _BIOME_DEPTH derives from it so
    # the index of a biome equals its integer depth.  utils.mining.world reuses
    # BIOME_ORDER, so this is the single source of truth for both modules.
    assert len(exp.BIOME_ORDER) == len(exp.Biome)
    for depth, biome in enumerate(exp.BIOME_ORDER):
        assert exp._BIOME_DEPTH[biome] == depth


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
        exp.Biome.DEEP,
        exp.Loadout(tools=frozenset({exp.DYNAMITE})),
    )
    assert "blasted_vein" not in {o.key for o in without}
    assert "blasted_vein" in {o.key for o in with_dyn}


def test_deeper_biome_includes_shallower_outcomes():
    deep = exp.eligible_outcomes(exp.Biome.MAGMA, exp.Loadout())
    assert "secret_chest" in {o.key for o in deep}  # a surface outcome


def test_mining_power_doubles_ore_gain():
    # abandoned_camp grants gold; mining_power 2 (a pickaxe) doubles a positive
    # ore gain, and 4 (an iron pickaxe) triples it.
    from utils.mining.exploration import _scale_amount
    from utils.equipment import EffectiveStats

    outcome = next(o for o in exp.CATALOG if o.key == "abandoned_camp")
    base = _scale_amount(outcome, EffectiveStats())
    assert _scale_amount(outcome, EffectiveStats(mining_power=2)) == base * 2
    assert _scale_amount(outcome, EffectiveStats(mining_power=4)) == base * 3


def test_penalties_are_never_scaled():
    from utils.mining.exploration import _scale_amount
    from utils.equipment import EffectiveStats

    hazard = next(o for o in exp.CATALOG if o.key == "monster_ambush")
    # Negative amount stays exactly as authored — gear protects gains only.
    assert (
        _scale_amount(hazard, EffectiveStats(mining_power=4, loot_bonus=1))
        == hazard.amount
    )


def test_loot_bonus_adds_flat_extra():
    from utils.mining.exploration import _scale_amount
    from utils.equipment import EffectiveStats

    # secret_chest gives wood (not ore): loot_bonus still adds a flat +1.
    outcome = next(o for o in exp.CATALOG if o.key == "secret_chest")
    assert _scale_amount(outcome, EffectiveStats(loot_bonus=1)) == outcome.amount + 1


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


def test_explore_from_state_returns_legacy_tuple_shape():
    text, item, amount = exp.explore_from_state({}, {}, rng=_rng())
    assert isinstance(text, str) and text
    assert item is None or isinstance(item, str)
    assert isinstance(amount, int)


def test_explore_from_state_maps_equipped_gear_and_threads_stats():
    # Equipped slots map to the catalog's capability tokens (TOOL→PICKAXE,
    # LIGHT→TORCH, CHARM→LUCKY_CHARM); dynamite is read from inventory; and the
    # equipped stats are threaded — so the helper equals resolving directly with
    # that loadout + computed stats under an identically seeded RNG.
    from utils import equipment

    equipped = {
        equipment.TOOL: "iron pickaxe",
        equipment.LIGHT: "lantern",
        equipment.CHARM: "lucky charm",
    }
    inv = {"dynamite": 1, "gold": 4}
    got = exp.explore_from_state(
        equipped, inv, biome=exp.Biome.CAVERN, rng=random.Random(7)
    )
    expected = exp.resolve(
        exp.Biome.CAVERN,
        exp.Loadout(
            tools=frozenset({exp.PICKAXE, exp.TORCH, exp.LUCKY_CHARM, exp.DYNAMITE}),
        ),
        stats=equipment.compute_stats(equipped),
        rng=random.Random(7),
    ).to_legacy_tuple()
    assert got == expected


def test_light_slot_satisfies_deep_find_gate():
    # Regression: a lantern (not a literal "torch") in the LIGHT slot must
    # unlock the torch-gated deep finds — the old ownership check missed it.
    from utils import equipment

    assert exp._SLOT_TO_TOKEN[equipment.LIGHT] == exp.TORCH


def test_explore_from_state_default_biome_is_surface():
    from utils import equipment

    equipped = {equipment.TOOL: "pickaxe"}
    default = exp.explore_from_state(equipped, {}, rng=random.Random(3))
    explicit = exp.explore_from_state(
        equipped, {}, biome=exp.Biome.SURFACE, rng=random.Random(3)
    )
    assert default == explicit
