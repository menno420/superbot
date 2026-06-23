"""utils.fishing.fish — the size-ranked catalog + level bands (owner Q-0175)."""

from __future__ import annotations

from utils.fishing import fish


def test_shore_catalog_loads_exactly_21_fish():
    # The original 21 size-ranked fish stay the SHORE catalog (Q-0175 §5 venue
    # split — deepwater fish are additive, so SPECIES is now larger).
    assert len(fish.species_for_venue(fish.SHORE_VENUE)) == 21


def test_shore_catalog_is_sorted_by_size_rank_1_to_21():
    ranks = [s.size_rank for s in fish.species_for_venue(fish.SHORE_VENUE)]
    assert ranks == list(range(1, 22))


def test_seven_levels_times_three_covers_the_shore_catalog():
    assert fish.MAX_LEVEL * fish.FISH_PER_LEVEL == len(
        fish.species_for_venue(fish.SHORE_VENUE),
    )


def test_names_are_unique_and_lowercase():
    names = [s.name for s in fish.SPECIES]
    assert len(names) == len(set(names))
    assert all(n == n.lower() for n in names)


def test_level_1_unlocks_the_three_smallest():
    cap = fish.max_size_rank_for_level(1)
    assert cap == 3
    unlocked = fish.unlocked_species(1)
    assert [s.size_rank for s in unlocked] == [1, 2, 3]


def test_each_level_unlocks_three_more():
    for level in range(1, fish.MAX_LEVEL + 1):
        assert fish.max_size_rank_for_level(level) == 3 * level


def test_max_level_unlocks_everything_on_shore():
    shore_n = len(fish.species_for_venue(fish.SHORE_VENUE))
    assert fish.max_size_rank_for_level(fish.MAX_LEVEL) == fish.venue_size_cap(
        fish.SHORE_VENUE,
    )
    assert len(fish.unlocked_species(fish.MAX_LEVEL)) == shore_n


def test_level_band_clamps_above_max_level():
    # A level beyond MAX never exceeds the venue's own size cap.
    assert fish.max_size_rank_for_level(99) == fish.venue_size_cap(fish.SHORE_VENUE)


def test_level_zero_or_negative_treated_as_level_one():
    assert fish.max_size_rank_for_level(0) == 3
    assert fish.max_size_rank_for_level(-5) == 3


def test_species_by_name_is_case_insensitive_and_trims():
    assert fish.species_by_name("  MINNOW ") is fish.species_by_name("minnow")
    assert fish.species_by_name("minnow").size_rank == 1


def test_species_by_name_returns_none_for_unknown():
    assert fish.species_by_name("kraken") is None


def test_every_species_carries_an_emoji():
    assert all(s.emoji for s in fish.SPECIES)


# ---------------------------------------------------------------------------
# Venue split (Q-0175 §5) — shore vs deepwater (boat-only) pools
# ---------------------------------------------------------------------------


def test_species_carry_a_venue_defaulting_to_shore():
    # Every loaded species has a venue; the original 21 default to shore.
    assert all(s.venue in ("shore", "deepwater") for s in fish.SPECIES)
    assert all(s.venue == "shore" for s in fish.species_for_venue("shore"))


def test_deepwater_pool_is_non_empty_and_separate_from_shore():
    shore = fish.species_for_venue("shore")
    deep = fish.species_for_venue("deepwater")
    assert deep, "deepwater venue has no fish"
    assert set(s.name for s in shore).isdisjoint(s.name for s in deep)
    # SPECIES is the union of both venues.
    assert len(fish.SPECIES) == len(shore) + len(deep)


def test_shore_fishing_only_ever_yields_shore_fish():
    for level in range(1, fish.MAX_LEVEL + 1):
        assert all(s.venue == "shore" for s in fish.unlocked_species(level, "shore"))


def test_deepwater_fishing_only_ever_yields_deepwater_fish():
    for level in range(1, fish.MAX_LEVEL + 1):
        assert all(
            s.venue == "deepwater" for s in fish.unlocked_species(level, "deepwater")
        )


def test_venue_size_cap_matches_the_pools_largest_rank():
    for v in ("shore", "deepwater"):
        pool = fish.species_for_venue(v)
        assert fish.venue_size_cap(v) == max(s.size_rank for s in pool)


def test_unknown_venue_yields_an_empty_pool_and_zero_cap():
    assert fish.species_for_venue("lava") == []
    assert fish.venue_size_cap("lava") == 0
    assert fish.max_size_rank_for_level(7, "lava") == 0
    assert fish.unlocked_species(7, "lava") == []
