"""Item taxonomy — the shared 3-layer grouping (Category → Type → Variant).

One source of truth for both the recipe browser (craft) and the market (buy).
"""

from __future__ import annotations

from utils.mining import taxonomy as tx


def test_base_type_is_the_last_word():
    assert tx.base_type("iron sword") == "sword"
    assert tx.base_type("diamond pickaxe") == "pickaxe"
    assert tx.base_type("torch") == "torch"


def test_category_of_maps_slot_then_kind():
    assert tx.category_of("iron sword") == "Weapons"
    assert tx.category_of("iron shield") == "Weapons"  # shields are combat gear
    assert tx.category_of("iron helmet") == "Armour"
    assert tx.category_of("iron pickaxe") == "Tools"
    assert tx.category_of("lantern") == "Tools"
    assert tx.category_of("stone hut") == "Structures"


def test_grouped_orders_variants_by_rarity():
    names = ["diamond sword", "sword", "iron sword", "bronze sword"]
    assert tx.grouped(names)["sword"] == [
        "sword",
        "bronze sword",
        "iron sword",
        "diamond sword",
    ]


def test_types_by_category_orders_armour_head_to_toe():
    names = ["iron boots", "iron helmet", "iron leggings", "iron chestplate"]
    assert tx.types_by_category(names)["Armour"] == [
        "helmet",
        "chestplate",
        "leggings",
        "boots",
    ]


def test_weapons_lists_swords_before_shields():
    weapons = tx.types_by_category(["iron shield", "iron sword"])["Weapons"]
    assert weapons.index("sword") < weapons.index("shield")


def test_ordered_categories_follows_display_order():
    names = ["stone hut", "iron sword", "iron helmet", "iron pickaxe"]
    assert tx.ordered_categories(names) == ["Weapons", "Armour", "Tools", "Structures"]
