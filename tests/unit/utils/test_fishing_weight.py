"""utils.fishing.weight — per-catch weight roll (seed-deterministic, monotonic)."""

from __future__ import annotations

import random

from utils.fishing import fish
from utils.fishing.weight import nominal_weight, roll_weight


def _species(rank: int) -> fish.FishSpecies:
    return fish.FishSpecies(name=f"fish{rank}", size_rank=rank, emoji="🐟")


def test_roll_is_deterministic_for_a_fixed_seed():
    s = _species(5)
    assert roll_weight(s, random.Random(42)) == roll_weight(s, random.Random(42))


def test_nominal_weight_grows_with_size_rank():
    weights = [nominal_weight(_species(r)) for r in range(1, 22)]
    # Strictly increasing — a bigger-ranked fish is always heavier on average.
    assert all(b > a for a, b in zip(weights, weights[1:]))


def test_smallest_fish_is_light_and_largest_is_a_trophy():
    assert nominal_weight(_species(1)) < 1.0  # a few hundred grams
    assert nominal_weight(_species(21)) > 20.0  # a real haul


def test_roll_stays_within_the_bounded_spread():
    s = _species(10)
    nominal = nominal_weight(s)
    rng = random.Random(7)
    for _ in range(2000):
        w = roll_weight(s, rng)
        # Bounded by the spread factors (0.65 … 1.55), never below the 0.01 floor.
        assert 0.01 <= w <= nominal * 1.55 + 0.01


def test_repeat_catches_of_one_species_vary():
    s = _species(8)
    rng = random.Random(99)
    seen = {roll_weight(s, rng) for _ in range(50)}
    # Per-catch variation is the whole point — a trophy must be beatable.
    assert len(seen) > 1


def test_a_real_catalog_species_rolls_a_positive_weight():
    if fish.SPECIES:
        w = roll_weight(fish.SPECIES[0], random.Random(1))
        assert w > 0
