"""utils.fishing.fish — the species catalog integrity (pure, no harness)."""

from __future__ import annotations

import pytest

from utils.fishing import fish


def test_every_species_has_a_known_rarity():
    for s in fish.SPECIES:
        assert s.rarity in fish.RARITY_ROLL_WEIGHT


def test_value_and_weight_bands_are_well_formed():
    for s in fish.SPECIES:
        assert 0 < s.value_min <= s.value_max
        assert 0 < s.weight_min <= s.weight_max


def test_species_names_are_unique_and_lowercase():
    names = [s.name for s in fish.SPECIES]
    assert len(names) == len(set(names))
    assert all(n == n.lower() for n in names)


def test_every_rarity_tier_has_at_least_one_species():
    for rarity in fish.RARITY_ROLL_WEIGHT:
        assert fish.species_by_rarity(rarity), f"{rarity} has no species"


def test_value_bands_climb_with_rarity():
    order = ["common", "uncommon", "rare", "epic", "legendary"]
    floors = [
        min(s.value_min for s in fish.species_by_rarity(r)) for r in order
    ]
    assert floors == sorted(floors)


def test_species_by_name_is_case_insensitive_and_trims():
    assert fish.species_by_name("  SARDINE ") is fish.species_by_name("sardine")
    assert fish.species_by_name("sardine").name == "sardine"


def test_species_by_name_returns_none_for_unknown():
    assert fish.species_by_name("kraken") is None


@pytest.mark.parametrize("s", fish.SPECIES, ids=lambda s: s.name)
def test_every_species_carries_an_emoji(s):
    assert s.emoji
