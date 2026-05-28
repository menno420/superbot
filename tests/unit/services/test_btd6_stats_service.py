"""Tests for btd6_stats_service against the real committed stats files."""

from __future__ import annotations

import pytest

from services import btd6_stats_service as svc


@pytest.fixture(autouse=True)
def _fresh_cache():
    svc.reset_cache()
    yield
    svc.reset_cache()


def test_loads_bomb_shooter():
    stats = svc.get_tower_stats("bomb_shooter")
    assert stats is not None
    assert stats.has_combat_stats
    assert stats.base_cost == 375
    assert stats.paragon_cost == 600000
    assert len(stats.upgrades) == 15
    assert stats.tier_codes()[0] == "000"
    assert len(stats.tier_codes()) == 16


def test_missing_tower_returns_none():
    assert svc.get_tower_stats("does_not_exist") is None


def test_normal_stats_base_bomb_shooter():
    stats = svc.get_tower_stats("bomb_shooter")
    ns = svc.normal_stats(stats.tier("000"))
    assert ns.damage == 1
    assert ns.damage_type == "Explosion"
    assert ns.cannot_pop == "Cannot damage Black"
    assert ns.pierce == 22
    assert ns.cooldown == 1.5
    assert ns.attack_range == 40
    assert ns.can_see_camo is False  # bomb can't see camo


def test_normal_stats_bloon_crush_flips_to_normal_and_stuns():
    stats = svc.get_tower_stats("bomb_shooter")
    ns = svc.normal_stats(stats.tier("500"))
    assert ns.damage == 24
    assert ns.damage_type == "Normal"
    assert any("Stun" in s for s in ns.specials)


def test_normal_stats_surfaces_moab_bonus_and_ability():
    stats = svc.get_tower_stats("bomb_shooter")
    ns = svc.normal_stats(stats.tier("040"))  # MOAB Assassin
    assert any("MOAB-Class" in s for s in ns.specials)
    assert any("Ability" in s for s in ns.specials)


def test_normal_stats_surfaces_income():
    # Druid: Spirit of the Forest (0-5-0) gives passive income.
    druid = svc.get_tower_stats("druid")
    ns = svc.normal_stats(druid.tier("050"))
    assert any("Income" in s for s in ns.specials)
    # Sniper: Supply Drop (0-4-0) drops a cash crate.
    sniper = svc.get_tower_stats("sniper_monkey")
    ns = svc.normal_stats(sniper.tier("040"))
    assert any("Cash crate" in s for s in ns.specials)


def test_economy_tower_has_costs_but_no_combat_stats():
    farm = svc.get_tower_stats("banana_farm")
    assert farm is not None
    assert farm.base_cost == 1250
    assert farm.has_combat_stats is False
    assert farm.tier_codes() == ()
