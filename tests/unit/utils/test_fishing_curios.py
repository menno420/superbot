"""Curios — the cosmetic coral-carving collection (pure).

Pins the catalog/recipe numbers (docs/planning/fishing-coral-numbers-2026-07-01.md)
and the non-sellable TREASURE contract that keeps curios cosmetic (no coin faucet).
"""

from __future__ import annotations

from utils.fishing import curios
from utils.mining import items, market


def test_catalog_shape_and_ascending_coral_cost():
    keys = curios.CURIO_KEYS
    assert keys == ("coral shell", "coral seahorse", "coral idol", "coral leviathan")
    costs = [c.coral_cost for c in curios.CURIO_CATALOG]
    assert costs == sorted(costs)  # ascending — the Leviathan is the top trophy
    assert costs == [2, 4, 8, 16]  # pinned (numbers doc) — doubling long-tail


def test_leviathan_is_the_legendary_top_tier():
    # The 2026-07-01 second-tier extension: a Legendary curio at double the Idol's
    # coral cost and net-worth value, capping the collection long-tail.
    leviathan = curios.curio_by_key("coral leviathan")
    assert leviathan is not None
    assert leviathan.rarity == "Legendary"
    assert leviathan.coral_cost == 16
    assert curios.craftable_key_for("Coral Leviathan") == "coral leviathan"


def test_curio_by_key_resolves_and_rejects_unknown():
    assert curios.curio_by_key("coral idol").name == "Coral Idol"
    assert curios.curio_by_key("nope") is None
    assert curios.curio_by_key(None) is None
    assert curios.curio_by_key("") is None


def test_craftable_key_for_matches_key_or_display_name_case_insensitively():
    assert curios.craftable_key_for("coral idol") == "coral idol"
    assert curios.craftable_key_for("Coral Idol") == "coral idol"
    assert curios.craftable_key_for("CORAL SHELL") == "coral shell"
    assert curios.craftable_key_for("driftwood") is None
    assert curios.craftable_key_for("") is None


def test_collection_progress_counts_distinct_owned_curios():
    assert curios.collection_progress({}) == (0, 4)
    assert curios.collection_progress({"coral shell": 5}) == (1, 4)
    # a zero/negative qty is not "owned"
    assert curios.collection_progress({"coral shell": 0, "coral idol": 2}) == (1, 4)
    full = {item: 1 for item in curios.CURIO_ITEMS}
    assert curios.collection_progress(full) == (4, 4)


def test_every_curio_is_a_non_sellable_treasure_item():
    # Curios must be catalogued as TREASURE so the browser sorts them and — the
    # key contract — market.sell_price returns None (no coin faucet from a rare
    # cosmetic). This fails if a curio is ever miscatalogued as a RESOURCE.
    for curio in curios.CURIO_CATALOG:
        item = items.lookup(curio.item)
        assert item is not None, f"{curio.item} missing from items catalog"
        assert item.kind is items.ItemKind.TREASURE
        assert market.sell_price(curio.item) is None


def test_coral_material_is_not_sellable():
    # Coral is a crafting material, never a coin source (uncatalogued as a
    # sellable RESOURCE, mirroring the pearl).
    assert market.sell_price("coral") is None


def test_cost_text_is_human_readable():
    curio = curios.curio_by_key("coral seahorse")
    assert curios.cost_text(curio) == "4 🪸 coral"
