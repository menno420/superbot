"""Fishing bait catalog — pure-data invariants (Q-0175 §4)."""

from __future__ import annotations

from utils.fishing import bait as bait_mod


def test_catalog_is_non_empty_with_unique_keys():
    assert bait_mod.BAIT_CATALOG
    keys = [b.key for b in bait_mod.BAIT_CATALOG]
    assert len(keys) == len(set(keys))  # no duplicate keys
    assert bait_mod.BAIT_KEYS == tuple(keys)  # keys mirror the shelf order


def test_every_bait_is_a_meaningful_consumable_sink():
    for bait in bait_mod.BAIT_CATALOG:
        # Knobs never penalise: rarity_pull ≥ 1 compounds onto the rod, bite_speed
        # ≤ 1 (and > 0) only shortens the wait; bounded charges + a positive price
        # make it a real consumable coin sink, and it must improve ≥ 1 knob.
        assert bait.rarity_pull >= 1.0
        assert 0.0 < bait.bite_speed <= 1.0
        assert bait.charges > 0
        assert bait.price > 0
        assert bait.rarity_pull > 1.0 or bait.bite_speed < 1.0


def test_both_knob_families_and_a_combo_are_on_the_shelf():
    rarity_only = [
        b for b in bait_mod.BAIT_CATALOG if b.rarity_pull > 1.0 and b.bite_speed == 1.0
    ]
    speed_only = [
        b for b in bait_mod.BAIT_CATALOG if b.bite_speed < 1.0 and b.rarity_pull == 1.0
    ]
    combo = [
        b for b in bait_mod.BAIT_CATALOG if b.rarity_pull > 1.0 and b.bite_speed < 1.0
    ]
    assert rarity_only and speed_only and combo  # the orthogonal shelf design


def test_pricier_bait_is_stronger_within_each_pure_knob_family():
    # Cross-family price isn't comparable (different knobs), but within a pure
    # family a pricier pack must be at least as strong.
    rarity = sorted(
        (
            b
            for b in bait_mod.BAIT_CATALOG
            if b.rarity_pull > 1.0 and b.bite_speed == 1.0
        ),
        key=lambda b: b.price,
    )
    assert [b.rarity_pull for b in rarity] == sorted(b.rarity_pull for b in rarity)
    speed = sorted(
        (
            b
            for b in bait_mod.BAIT_CATALOG
            if b.bite_speed < 1.0 and b.rarity_pull == 1.0
        ),
        key=lambda b: b.price,
    )
    # lower bite_speed = faster, so pricier ⇒ non-increasing bite_speed
    assert [b.bite_speed for b in speed] == sorted(
        (b.bite_speed for b in speed), reverse=True
    )


def test_effect_text_describes_only_the_knobs_a_bait_turns():
    rarity = bait_mod.bait_by_key("worm")  # ×1.25 rarity, neutral speed
    speed = bait_mod.bait_by_key("minnow")  # neutral rarity, 0.80 speed
    combo = bait_mod.bait_by_key("feast")  # both
    assert bait_mod.effect_text(rarity) == "×1.25 rarity"
    assert bait_mod.effect_text(speed) == "−20% wait"
    assert "rarity" in bait_mod.effect_text(combo) and "wait" in bait_mod.effect_text(
        combo
    )
    # a hypothetical neutral bait reads honestly rather than claiming a knob
    neutral = bait_mod.Bait("x", "X", "🧪", rarity_pull=1.0, charges=1, price=1)
    assert bait_mod.effect_text(neutral) == "no effect"


def test_bait_by_key_resolves_known_and_rejects_unknown():
    first = bait_mod.BAIT_CATALOG[0]
    assert bait_mod.bait_by_key(first.key) is first
    assert bait_mod.bait_by_key("nope") is None
    assert bait_mod.bait_by_key("") is None
    assert bait_mod.bait_by_key(None) is None


# ---------------------------------------------------------------------------
# Craft recipes — turn small caught fish into bait (catch→bait loop)
# ---------------------------------------------------------------------------


def test_every_recipe_targets_a_real_craftable_bait():
    for key, recipe in bait_mod.CRAFT_RECIPES.items():
        assert recipe.bait_key == key  # the map key matches the recipe's own key
        assert bait_mod.bait_by_key(key) is not None  # produces a real bait
        assert recipe.fish_count > 0
        assert recipe.max_size_rank > 0


def test_craftable_keys_mirror_shelf_order_and_skip_uncraftable():
    # CRAFTABLE_KEYS is the shelf-ordered subset that has a recipe.
    assert bait_mod.CRAFTABLE_KEYS == tuple(
        b.key for b in bait_mod.BAIT_CATALOG if b.key in bait_mod.CRAFT_RECIPES
    )
    # The premium combo stays a pure coin sink (not craftable).
    assert "feast" not in bait_mod.CRAFT_RECIPES


def test_pricier_craftable_bait_costs_more_or_larger_fish():
    # A stronger/pricier craftable pack should never be cheaper to craft than a
    # weaker one — recipe cost rises with the bait's coin price (a monotone sink).
    ordered = sorted(
        (bait_mod.bait_by_key(k) for k in bait_mod.CRAFTABLE_KEYS),
        key=lambda b: b.price,
    )
    costs = [
        (
            bait_mod.craft_recipe(b.key).fish_count,
            bait_mod.craft_recipe(b.key).max_size_rank,
        )
        for b in ordered
    ]
    # both dimensions are non-decreasing as price rises
    assert costs == sorted(costs)


def test_craft_recipe_resolves_known_and_rejects_uncraftable():
    assert bait_mod.craft_recipe("worm") is bait_mod.CRAFT_RECIPES["worm"]
    assert bait_mod.craft_recipe("feast") is None  # coin-only premium
    assert bait_mod.craft_recipe("nope") is None
    assert bait_mod.craft_recipe("") is None
    assert bait_mod.craft_recipe(None) is None


def test_recipe_text_reads_human():
    assert (
        bait_mod.recipe_text(bait_mod.BaitRecipe("worm", 3, 3)) == "3 fish (size ≤ 3)"
    )


def test_craftable_key_for_matches_key_or_name_case_insensitively():
    assert bait_mod.craftable_key_for("worm") == "worm"
    assert bait_mod.craftable_key_for("  WORM  ") == "worm"
    assert bait_mod.craftable_key_for("Worm Bait") == "worm"
    assert bait_mod.craftable_key_for("shimmer lure") == "lure"
    # not craftable / unknown / empty → None
    assert bait_mod.craftable_key_for("feast") is None
    assert bait_mod.craftable_key_for("Royal Feast") is None
    assert bait_mod.craftable_key_for("nope") is None
    assert bait_mod.craftable_key_for("") is None
    assert bait_mod.craftable_key_for(None) is None
