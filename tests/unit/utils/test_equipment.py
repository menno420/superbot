"""Tests for utils.equipment — pure, cross-game gear→stats model."""

from __future__ import annotations

from dataclasses import fields

from utils import equipment as eq


def test_slots_are_the_five_character_slots():
    assert eq.SLOTS == (eq.TOOL, eq.LIGHT, eq.CHARM, eq.WEAPON, eq.ARMOR)


def test_slot_for_known_items():
    assert eq.slot_for("pickaxe") == eq.TOOL
    assert eq.slot_for("iron pickaxe") == eq.TOOL
    assert eq.slot_for("torch") == eq.LIGHT
    assert eq.slot_for("lantern") == eq.LIGHT
    assert eq.slot_for("lucky charm") == eq.CHARM


def test_combat_gear_slots_and_stats():
    assert eq.slot_for("sword") == eq.WEAPON
    assert eq.slot_for("iron sword") == eq.WEAPON
    assert eq.slot_for("shield") == eq.ARMOR
    assert eq.slot_for("armor") == eq.ARMOR
    assert eq.item_stats("sword").damage == 3
    assert eq.item_stats("iron sword").damage == 6
    shield = eq.item_stats("shield")
    assert (shield.defense, shield.max_health) == (2, 10)
    body = eq.item_stats("armor")
    assert (body.defense, body.max_health) == (4, 20)


def test_compute_stats_mixes_mining_and_combat_gear():
    # A character equips mining AND combat gear at once; stats sum across all
    # five slots into one neutral block that each game reads its subset of.
    equipped = {
        eq.TOOL: "iron pickaxe",
        eq.LIGHT: "lantern",
        eq.WEAPON: "iron sword",
        eq.ARMOR: "armor",
    }
    stats = eq.compute_stats(equipped)
    assert stats.mining_power == 4
    assert stats.depth_access == 2
    assert stats.damage == 6
    assert stats.defense == 4
    assert stats.max_health == 20


def test_slot_for_is_case_insensitive():
    assert eq.slot_for("Iron Pickaxe") == eq.TOOL


def test_slot_for_unknown_is_none():
    assert eq.slot_for("gold") is None
    assert eq.slot_for("made up thing") is None


def test_is_equippable():
    assert eq.is_equippable("lantern")
    assert not eq.is_equippable("stone")


def test_item_stats_values():
    assert eq.item_stats("pickaxe").mining_power == 2
    assert eq.item_stats("iron pickaxe").mining_power == 4
    lantern = eq.item_stats("lantern")
    assert lantern.light_radius == 2
    assert lantern.depth_access == 2
    charm = eq.item_stats("lucky charm")
    assert charm.luck == 1
    assert charm.loot_bonus == 1


def test_item_stats_unknown_is_zero():
    assert eq.item_stats("gold") == eq.EffectiveStats()


def test_compute_stats_sums_equipped():
    equipped = {eq.TOOL: "iron pickaxe", eq.LIGHT: "lantern", eq.CHARM: "lucky charm"}
    stats = eq.compute_stats(equipped)
    assert stats.mining_power == 4
    assert stats.light_radius == 2
    assert stats.depth_access == 2
    assert stats.luck == 1
    assert stats.loot_bonus == 1


def test_compute_stats_empty_is_zero():
    assert eq.compute_stats({}) == eq.EffectiveStats()


def test_effectivestats_add():
    a = eq.EffectiveStats(mining_power=2, luck=1)
    b = eq.EffectiveStats(mining_power=3, light_radius=1)
    assert a + b == eq.EffectiveStats(mining_power=5, luck=1, light_radius=1)


def test_describe_stats_only_nonzero_in_order():
    stats = eq.EffectiveStats(mining_power=4, loot_bonus=1)
    assert eq.describe_stats(stats) == [("Mining power", 4), ("Loot bonus", 1)]


def test_describe_stats_empty():
    assert eq.describe_stats(eq.EffectiveStats()) == []


def test_stat_labels_match_dataclass_fields():
    field_names = {f.name for f in fields(eq.EffectiveStats)}
    assert set(eq.STAT_LABELS) == field_names
