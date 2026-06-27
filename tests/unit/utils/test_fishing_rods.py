"""fishing rod ladder — the pure domain (knobs, clamping, the price/knob curve)."""

from __future__ import annotations

from utils.fishing import rods


def test_ladder_is_five_tiers_starter_to_diamond():
    assert len(rods.ROD_LADDER) == 5
    assert rods.ROD_LADDER[0].tier == 0
    assert rods.STARTER is rods.ROD_LADDER[0]
    assert rods.MAX_TIER == 4
    # tiers are 0..4 in order
    assert [r.tier for r in rods.ROD_LADDER] == [0, 1, 2, 3, 4]


def test_starter_rod_is_free_and_neutral():
    starter = rods.STARTER
    assert starter.price == 0
    assert starter.window_bonus == 0.0
    assert starter.bite_speed == 1.0
    assert starter.rarity_pull == 1.0
    assert starter.escape_resist == 0.0
    assert starter.premature_grace == 0.0  # the bare rod never forgives an early reel


def test_knobs_and_price_improve_monotonically_up_the_ladder():
    ladder = rods.ROD_LADDER
    # each step strictly improves every knob (window↑, bite faster, pull↑, resist↑,
    # grace↑)
    assert all(
        a.window_bonus < b.window_bonus for a, b in zip(ladder, ladder[1:])
    )
    assert all(a.bite_speed > b.bite_speed for a, b in zip(ladder, ladder[1:]))
    assert all(a.rarity_pull < b.rarity_pull for a, b in zip(ladder, ladder[1:]))
    assert all(
        a.escape_resist < b.escape_resist for a, b in zip(ladder, ladder[1:])
    )
    assert all(
        a.premature_grace < b.premature_grace for a, b in zip(ladder, ladder[1:])
    )
    # and costs more (the price curve)
    assert all(a.price < b.price for a, b in zip(ladder, ladder[1:]))


def test_premature_grace_stays_a_probability_across_the_ladder():
    # the grace knob is a 0…1 chance — never out of range on any rung
    assert all(0.0 <= r.premature_grace <= 1.0 for r in rods.ROD_LADDER)


def test_rod_for_tier_clamps_out_of_range():
    assert rods.rod_for_tier(-5) is rods.STARTER
    assert rods.rod_for_tier(0) is rods.ROD_LADDER[0]
    assert rods.rod_for_tier(4) is rods.ROD_LADDER[4]
    assert rods.rod_for_tier(99) is rods.ROD_LADDER[4]  # clamp to top


def test_next_rod_walks_up_then_stops_at_the_top():
    assert rods.next_rod(0) is rods.ROD_LADDER[1]
    assert rods.next_rod(3) is rods.ROD_LADDER[4]
    assert rods.next_rod(4) is None  # already diamond
    assert rods.next_rod(99) is None


# ---------------------------------------------------------------------------
# the fish → rod craft shelf (the non-coin earn path, follow-up to #1508)
# ---------------------------------------------------------------------------


def test_a_recipe_exists_for_every_non_starter_tier_and_none_for_the_starter():
    # buy_rod / craft_rod craft the *next* tier up, so each rung 1..MAX needs a
    # recipe; the starter (tier 0) is free and uncraftable.
    assert rods.rod_recipe(0) is None
    for tier in range(1, rods.MAX_TIER + 1):
        recipe = rods.rod_recipe(tier)
        assert recipe is not None
        assert recipe.tier == tier
    assert set(rods.ROD_RECIPES) == set(range(1, rods.MAX_TIER + 1))


def test_craft_cost_climbs_monotonically_up_the_ladder():
    recipes = [rods.ROD_RECIPES[t] for t in range(1, rods.MAX_TIER + 1)]
    # more fish AND a more permissive size cap for each rung up
    assert all(a.fish_count < b.fish_count for a, b in zip(recipes, recipes[1:]))
    assert all(
        a.max_size_rank <= b.max_size_rank for a, b in zip(recipes, recipes[1:])
    )
    # every cost is a positive number of fish
    assert all(r.fish_count > 0 for r in recipes)


def test_rod_recipe_text_reads_friendly():
    assert rods.rod_recipe_text(rods.rod_recipe(1)) == "10 fish (size ≤ 6)"
