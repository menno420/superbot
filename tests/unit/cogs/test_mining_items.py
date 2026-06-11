"""Tests for utils.mining.items — pure item taxonomy."""

from __future__ import annotations

from utils.mining import items


def test_classify_known_kinds():
    assert items.classify("gold") is items.ItemKind.RESOURCE
    assert items.classify("pickaxe") is items.ItemKind.TOOL
    assert items.classify("dynamite") is items.ItemKind.CONSUMABLE
    assert items.classify("stone hut") is items.ItemKind.STRUCTURE
    assert items.classify("lucky charm") is items.ItemKind.TREASURE


def test_classify_unknown_defaults_to_resource():
    assert items.classify("mystery_dust") is items.ItemKind.RESOURCE


def test_classify_is_case_insensitive():
    assert items.classify("GOLD") is items.ItemKind.RESOURCE
    assert items.classify("PickAxe") is items.ItemKind.TOOL


def test_tool_predicates():
    assert items.is_tool("pickaxe")
    assert not items.is_tool("gold")
    assert items.is_consumable("torch")
    assert not items.is_consumable("pickaxe")


def test_tool_tier_and_value():
    # Resource tiers renumbered when bronze/silver joined the ladder
    # (stone 1 < bronze 2 < iron 3 < silver 4 < gold 5 < diamond 6).
    assert items.tool_tier("diamond") == 6
    assert items.tool_tier("unknown") == 0
    assert items.item_value("diamond") > items.item_value("stone")
    assert items.item_value("unknown") == 1


def test_total_value_sums_and_ignores_nonpositive():
    inv = {"gold": 2, "diamond": 1, "stone": 0, "unknown": 3}
    expected = (
        items.item_value("gold") * 2
        + items.item_value("diamond") * 1
        + items.item_value("unknown") * 3
    )
    assert items.total_value(inv) == expected


def test_next_tool_upgrade_ladder():
    assert items.next_tool_upgrade("pickaxe") == "iron pickaxe"
    assert items.next_tool_upgrade("iron pickaxe") == "gold pickaxe"
    assert items.next_tool_upgrade("gold pickaxe") == "diamond pickaxe"
    assert items.next_tool_upgrade("diamond pickaxe") is None  # top of ladder
    assert items.next_tool_upgrade("lantern") == "diamond lantern"
    assert items.next_tool_upgrade("torch") == "lantern"
    assert items.next_tool_upgrade("gold") is None  # not on a ladder


def test_sort_inventory_orders_by_kind_then_value():
    inv = {"diamond throne": 1, "gold": 3, "torch": 2, "pickaxe": 1, "stone": 5}
    ordered = [name for name, _ in items.sort_inventory(inv)]
    # resources first (gold before stone by value), then tool, consumable,
    # then structure last.
    assert ordered.index("gold") < ordered.index("stone")
    assert ordered.index("stone") < ordered.index("pickaxe")
    assert ordered.index("pickaxe") < ordered.index("torch")
    assert ordered[-1] == "diamond throne"


def test_sort_inventory_drops_zero_quantities():
    inv = {"gold": 0, "stone": 2}
    assert items.sort_inventory(inv) == [("stone", 2)]


def test_summarize_inventory_groups_by_kind_in_display_order():
    inv = {
        "diamond": 2,  # resource (high value)
        "stone": 5,  # resource
        "pickaxe": 1,  # tool
        "dynamite": 3,  # consumable
        "stone hut": 1,  # structure
        "lucky charm": 1,  # treasure
        "gone": 0,  # dropped (zero qty)
    }
    sections = items.summarize_inventory(inv)
    assert [kind for kind, _ in sections] == [
        items.ItemKind.RESOURCE,
        items.ItemKind.TOOL,
        items.ItemKind.CONSUMABLE,
        items.ItemKind.STRUCTURE,
        items.ItemKind.TREASURE,
    ]
    # Resources ordered by value desc: diamond (12) before stone (1).
    assert sections[0][1] == [("diamond", 2), ("stone", 5)]
    # Zero-qty item is dropped entirely.
    all_names = {name for _, rows in sections for name, _ in rows}
    assert "gone" not in all_names


def test_summarize_inventory_empty():
    assert items.summarize_inventory({}) == []


def test_summarize_inventory_only_present_kinds_appear():
    sections = items.summarize_inventory({"iron": 4})
    assert [kind for kind, _ in sections] == [items.ItemKind.RESOURCE]
    assert sections[0][1] == [("iron", 4)]
