"""utils.creatures.creature — the original creature catalog (Q-0187)."""

from __future__ import annotations

from utils.creatures import creature


def test_catalog_loads_exactly_36_creatures():
    assert len(creature.CREATURES) == 36


def test_six_elements_each_with_six_creatures():
    from collections import Counter

    by_element = Counter(c.element for c in creature.CREATURES)
    assert len(by_element) == 6
    assert all(count == 6 for count in by_element.values())


def test_names_are_unique():
    names = [c.name for c in creature.CREATURES]
    assert len(names) == len(set(names))


def test_every_creature_has_a_known_rarity():
    assert all(c.rarity in creature.RARITY_ORDER for c in creature.CREATURES)


def test_every_creature_carries_an_emoji():
    assert all(c.emoji for c in creature.CREATURES)


def test_rarer_creatures_are_harder_to_catch_and_rarer_to_meet():
    # The catch/encounter weights are monotonic in the rarity order.
    catch = [creature.RARITY_CATCH_BASE[r] for r in creature.RARITY_ORDER]
    meet = [creature.RARITY_ENCOUNTER_WEIGHT[r] for r in creature.RARITY_ORDER]
    assert catch == sorted(catch, reverse=True)
    assert meet == sorted(meet, reverse=True)


def test_creature_by_name_is_case_insensitive_and_trims():
    sample = creature.CREATURES[0]
    assert creature.creature_by_name(f"  {sample.name.upper()} ") is sample


def test_creature_by_name_returns_none_for_unknown():
    assert creature.creature_by_name("Charizard") is None


def test_elements_tuple_matches_the_catalog():
    assert set(creature.ELEMENTS) == {c.element for c in creature.CREATURES}


def test_creature_names_lists_every_creature():
    assert creature.creature_names() == [c.name for c in creature.CREATURES]


def test_creature_catch_base_and_encounter_weight_properties():
    sample = next(c for c in creature.CREATURES if c.rarity == "Epic")
    assert sample.catch_base == creature.RARITY_CATCH_BASE["Epic"]
    assert sample.encounter_weight == creature.RARITY_ENCOUNTER_WEIGHT["Epic"]
