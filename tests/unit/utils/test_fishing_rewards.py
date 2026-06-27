"""utils.fishing.rewards — the level-gated catch roll (seed-deterministic)."""

from __future__ import annotations

import random

from utils.fishing import fish
from utils.fishing.rewards import (
    BONUS_CATCH_CHANCE,
    roll_bonus_catch,
    roll_catch,
)


def test_roll_is_deterministic_for_a_fixed_seed():
    a = roll_catch(3, random.Random(42))
    b = roll_catch(3, random.Random(42))
    assert a == b


def test_roll_only_yields_fish_within_the_unlocked_band():
    for level in range(1, fish.MAX_LEVEL + 1):
        cap = fish.max_size_rank_for_level(level)
        rng = random.Random(level)
        for _ in range(300):
            catch = roll_catch(level, rng)
            assert catch is not None
            assert catch.species.size_rank <= cap


def test_level_1_can_only_catch_the_three_smallest():
    rng = random.Random(7)
    seen = {roll_catch(1, rng).species.size_rank for _ in range(400)}
    assert seen <= {1, 2, 3}


def test_higher_levels_can_reach_bigger_fish():
    rng = random.Random(11)
    seen = {roll_catch(fish.MAX_LEVEL, rng).species.size_rank for _ in range(3000)}
    # With enough rolls at max level, a large fish should appear.
    assert max(seen) > fish.FISH_PER_LEVEL


def test_smaller_fish_are_more_common_than_bigger_ones():
    rng = random.Random(99)
    from collections import Counter

    counts = Counter(roll_catch(fish.MAX_LEVEL, rng).species.size_rank for _ in range(8000))
    # The smallest fish should out-appear the largest (inverse-size weighting).
    assert counts[1] > counts[len(fish.SPECIES)]


def test_roll_returns_none_when_no_species_unlocked(monkeypatch):
    monkeypatch.setattr(
        "utils.fishing.rewards.unlocked_species",
        lambda level, venue="shore": [],
    )
    assert roll_catch(1) is None


def test_rarity_pull_biases_toward_bigger_fish():
    """A higher rarity_pull should raise the average size of the catch."""
    import random as _random

    from utils.fishing.rewards import roll_catch

    def avg_size(pull):
        rng = _random.Random(123)
        sizes = [
            roll_catch(7, rng, rarity_pull=pull).species.size_rank  # type: ignore[union-attr]
            for _ in range(4000)
        ]
        return sum(sizes) / len(sizes)

    base = avg_size(1.0)
    pulled = avg_size(1.7)
    assert pulled > base  # the rod knob makes catches bigger, on average


def test_rarity_pull_below_one_is_clamped_to_neutral():
    """Pull < 1 must not *penalise* big fish — it clamps to the base weighting."""
    import random as _random

    from utils.fishing.rewards import roll_catch

    def avg_size(pull):
        rng = _random.Random(7)
        sizes = [
            roll_catch(7, rng, rarity_pull=pull).species.size_rank  # type: ignore[union-attr]
            for _ in range(2000)
        ]
        return sum(sizes) / len(sizes)

    # 0.5 clamps to 1.0 → same distribution as neutral (same seed → same draws).
    assert avg_size(0.5) == avg_size(1.0)


def test_fish_items_sell_for_their_size_rank():
    """Paced fishing → generous sell value ≈ size_rank (the PR4 rebalance)."""
    from utils.fishing.fish import SPECIES
    from utils.mining.items import lookup

    for s in SPECIES:
        item = lookup(s.name)
        assert item is not None
        assert item.value == s.size_rank  # 1…21, up from the old 1…7


def test_roll_yields_only_the_requested_venues_fish():
    """A deepwater cast can only ever produce deepwater (boat-only) species."""
    rng = random.Random(3)
    deep_names = {s.name for s in fish.species_for_venue("deepwater")}
    for _ in range(500):
        catch = roll_catch(fish.MAX_LEVEL, rng, venue="deepwater")
        assert catch is not None
        assert catch.species.venue == "deepwater"
        assert catch.species.name in deep_names


def test_shore_and_deepwater_rolls_draw_from_disjoint_pools():
    rng = random.Random(11)
    shore = {roll_catch(fish.MAX_LEVEL, rng, venue="shore").species.name for _ in range(400)}
    deep = {roll_catch(fish.MAX_LEVEL, rng, venue="deepwater").species.name for _ in range(400)}
    assert shore.isdisjoint(deep)


# ---------------------------------------------------------------------------
# the lucky-double-catch bonus (extra craft fodder, with PR #1515)
# ---------------------------------------------------------------------------


def test_bonus_catch_chance_stays_a_treat_not_the_norm():
    # The bonus must feel lucky, never a baseline doubling of fishing output.
    assert 0.0 < BONUS_CATCH_CHANCE <= 0.25


def test_roll_bonus_catch_is_deterministic_for_a_fixed_seed():
    assert roll_bonus_catch(random.Random(7)) == roll_bonus_catch(random.Random(7))


def test_roll_bonus_catch_fires_at_about_the_configured_rate():
    rng = random.Random(123)
    hits = sum(roll_bonus_catch(rng) for _ in range(20_000))
    rate = hits / 20_000
    # within a generous band of the configured chance (seeded, so stable)
    assert abs(rate - BONUS_CATCH_CHANCE) < 0.02
