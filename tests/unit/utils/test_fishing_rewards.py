"""utils.fishing.rewards — the catch roll (seed-deterministic, pure)."""

from __future__ import annotations

import random
from collections import Counter

from utils.fishing import fish
from utils.fishing.rewards import _weighted_tier_table, roll_catch


def test_roll_is_deterministic_for_a_fixed_seed():
    a = roll_catch(random.Random(42))
    b = roll_catch(random.Random(42))
    assert a == b


def test_roll_value_and_weight_fall_inside_the_species_bands():
    rng = random.Random(7)
    for _ in range(500):
        catch = roll_catch(rng)
        s = catch.species
        assert s.value_min <= catch.value <= s.value_max
        assert s.weight_min <= catch.weight <= s.weight_max


def test_roll_only_yields_catalog_species():
    rng = random.Random(1)
    known = {s.name for s in fish.SPECIES}
    for _ in range(300):
        assert roll_catch(rng).species.name in known


def test_common_fish_dominate_without_a_rod():
    rng = random.Random(99)
    rarities = Counter(roll_catch(rng).species.rarity for _ in range(4000))
    assert rarities["common"] > rarities["uncommon"] > 0
    # Legendary should be vanishingly rare on the base table.
    assert rarities["common"] > rarities.get("legendary", 0) * 20


def test_rod_bonus_shifts_weight_off_common_toward_rarer_tiers():
    base = _weighted_tier_table(0)
    boosted = _weighted_tier_table(3)
    assert boosted["common"] < base["common"]
    assert boosted["rare"] > base["rare"]
    # The total weight is conserved (we only redistribute).
    assert round(sum(base.values()), 6) == round(sum(boosted.values()), 6)


def test_rod_bonus_never_excludes_commons():
    boosted = _weighted_tier_table(100)
    assert boosted["common"] >= 1.0


def test_zero_bonus_is_the_base_table_unchanged():
    assert _weighted_tier_table(0) == dict(fish.RARITY_ROLL_WEIGHT)
