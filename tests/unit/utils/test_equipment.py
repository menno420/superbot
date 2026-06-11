"""Tests for utils.equipment — pure, cross-game gear→stats model."""

from __future__ import annotations

from dataclasses import fields

from utils import equipment as eq


def test_slots_are_the_nine_character_slots():
    assert eq.SLOTS == (
        eq.TOOL,
        eq.LIGHT,
        eq.CHARM,
        eq.WEAPON,
        eq.SHIELD,
        eq.HELMET,
        eq.CHESTPLATE,
        eq.LEGGINGS,
        eq.BOOTS,
    )
    # The set slots are exactly the six combat slots, in SLOTS order.
    assert eq.SET_SLOTS == (
        eq.WEAPON,
        eq.SHIELD,
        eq.HELMET,
        eq.CHESTPLATE,
        eq.LEGGINGS,
        eq.BOOTS,
    )


def test_slot_for_known_items():
    assert eq.slot_for("pickaxe") == eq.TOOL
    assert eq.slot_for("iron pickaxe") == eq.TOOL
    assert eq.slot_for("torch") == eq.LIGHT
    assert eq.slot_for("lantern") == eq.LIGHT
    assert eq.slot_for("lucky charm") == eq.CHARM


def test_combat_gear_slots_and_stats():
    assert eq.slot_for("sword") == eq.WEAPON
    assert eq.slot_for("iron sword") == eq.WEAPON
    assert eq.slot_for("shield") == eq.SHIELD
    assert eq.slot_for("iron chestplate") == eq.CHESTPLATE
    assert eq.slot_for("gold helmet") == eq.HELMET
    assert eq.slot_for("bronze leggings") == eq.LEGGINGS
    assert eq.slot_for("silver boots") == eq.BOOTS
    # Pre-set anchors preserved (iron/diamond sword predate the set model).
    assert eq.item_stats("sword").damage == 3
    assert eq.item_stats("iron sword").damage == 6
    assert eq.item_stats("diamond sword").damage == 10
    shield = eq.item_stats("shield")
    assert (shield.defense, shield.max_health) == (2, 10)


def test_compute_stats_mixes_mining_and_combat_gear():
    # A character equips mining AND combat gear at once; stats sum across the
    # slots into one neutral block that each game reads its subset of.
    equipped = {
        eq.TOOL: "iron pickaxe",
        eq.LIGHT: "lantern",
        eq.WEAPON: "iron sword",
        eq.CHESTPLATE: "iron chestplate",
    }
    stats = eq.compute_stats(equipped)
    assert stats.mining_power == 4
    assert stats.depth_access == 2
    assert stats.damage == 6
    assert stats.defense == 2
    assert stats.max_health == 8


def test_gear_tier_and_tier_index():
    assert eq.gear_tier("bronze sword") == "bronze"
    assert eq.gear_tier("diamond chestplate") == "diamond"
    assert eq.gear_tier("sword") is None  # starter — untiered
    assert eq.gear_tier("iron pickaxe") is None  # mining gear — not a set slot
    assert eq.gear_tier("made up thing") is None
    assert [eq.tier_index(t) for t in eq.TIER_ORDER] == [1, 2, 3, 4, 5]


def _full_set(tier: str) -> dict[str, str]:
    families = ("sword", "shield", "helmet", "chestplate", "leggings", "boots")
    return {slot: f"{tier} {fam}" for slot, fam in zip(eq.SET_SLOTS, families)}


def test_full_same_tier_set_grants_the_bonus():
    equipped = _full_set("bronze")
    assert eq.active_set_tier(equipped) == "bronze"
    bonus = eq.set_bonus(equipped)
    assert (bonus.damage, bonus.max_health) == (
        eq.SET_BONUS_DAMAGE_PER_TIER,
        eq.SET_BONUS_HEALTH_PER_TIER,
    )
    # compute_stats applies it on top of the per-item sum.
    items_only = sum(
        (eq.item_stats(i) for i in equipped.values()),
        eq.EffectiveStats(),
    )
    total = eq.compute_stats(equipped)
    assert total.damage == items_only.damage + bonus.damage
    assert total.max_health == items_only.max_health + bonus.max_health
    assert total.defense == items_only.defense  # defense is never in the bonus


def test_mixed_tier_or_partial_set_has_no_bonus():
    mixed = _full_set("diamond")
    mixed[eq.BOOTS] = "gold boots"
    assert eq.active_set_tier(mixed) is None
    assert eq.set_bonus(mixed) == eq.EffectiveStats()
    partial = _full_set("iron")
    del partial[eq.HELMET]
    assert eq.active_set_tier(partial) is None
    # A starter in a set slot breaks the set too.
    starter = _full_set("iron")
    starter[eq.WEAPON] = "sword"
    assert eq.active_set_tier(starter) is None


def test_set_progress_counts_the_leading_tier():
    mixed = _full_set("diamond")
    mixed[eq.BOOTS] = "gold boots"
    assert eq.set_progress(mixed) == ("diamond", 5)
    assert eq.set_progress({}) is None
    assert eq.set_progress({eq.TOOL: "pickaxe"}) is None


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
