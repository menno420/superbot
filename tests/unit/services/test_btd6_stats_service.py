"""Tests for btd6_stats_service against the real committed stats files."""

from __future__ import annotations

import pytest

from services import btd6_stats_service as svc
from utils.btd6 import tier_codes


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
    codes = stats.tier_codes()
    # The 16 single-path tiers come first (in canonical order), then crosspaths.
    assert codes[:16] == tier_codes.SINGLE_PATH_CODES
    assert len(codes) > 16  # crosspath tiers are now reconstructed and kept


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


def test_paragon_abilities_load_named_with_cooldowns():
    mp = svc.get_paragon_stats("magus_perfectus")
    assert [a.name for a in mp.abilities] == ["Phoenix Explosion", "Arcane Metamorphosis"]
    assert mp.abilities[0].kind == "activated"
    assert mp.abilities[0].cooldown == 40
    assert "Phoenix Rebirth" in mp.abilities[0].description  # internal-name note kept
    # Apex Plasma Master genuinely has no activated ability — curated as empty.
    assert svc.get_paragon_stats("apex_plasma_master").abilities == ()


def test_every_paragon_has_curated_abilities_with_real_names():
    # The curated file must cover every paragon and never leave a generic name:
    # the stats module had four unnamed 'Ability' nodes (Glaive Dominus, Goliath
    # Doomship, Nautic Siege Core, Navarch) which must now carry real names.
    ids = set(svc.list_paragon_ids())
    assert set(svc._abilities()) == ids  # exactly the 13 paragons, no stray ids
    for pid in (
        "glaive_dominus",
        "goliath_doomship",
        "nautic_siege_core",
        "navarch_of_the_seas",
        "herald_of_everfrost",  # was prose-only, no abilities at all before
        "root_of_all_nature",
    ):
        abilities = svc.get_paragon_stats(pid).abilities
        assert abilities, pid
        assert all(a.name and a.name != "Ability" for a in abilities), pid


def test_normal_stats_excludes_reanimated_minions_for_prince_of_darkness():
    # Prince of Darkness (wizard 0-0-5) fires reanimated "MOAB"/"BFB" projectiles
    # (40/100 dmg). Those are minions, not the tower's hit, so the headline must
    # not report 100 — it reports the highest own-attack projectile instead.
    stats = svc.get_tower_stats("wizard_monkey")
    ns = svc.normal_stats(stats.tier("005"))
    assert ns.damage == 2  # the Reanimate hit, not the reanimated BFB's 100
    assert ns.pierce == 1
    assert ns.cooldown == 0.275


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


# --- crosspaths (reconstructed) + back-compat ---------------------------------


def test_crosspaths_for_returns_tier_crosspaths():
    stats = svc.get_tower_stats("bomb_shooter")
    cps = stats.crosspaths_for("200")
    # Crosspaths built on path-1 tier-2 (all present for Bomb Shooter).
    assert set(cps) >= {"201", "202", "210", "220"}
    assert all(tier_codes.digits(c)[0] == 2 for c in cps)
    assert all(tier_codes.is_crosspath(c) for c in cps)


def test_crosspaths_for_base_or_crosspath_is_empty():
    stats = svc.get_tower_stats("bomb_shooter")
    assert stats.crosspaths_for("000") == ()  # base has none
    assert stats.crosspaths_for("220") == ()  # not a single-path code


def test_old_style_16_tier_file_back_compat():
    # Beast Handler's module exposes no crosspath deltas — a real 16-tier file.
    # The service must degrade gracefully, not assume crosspath data exists.
    bh = svc.get_tower_stats("beast_handler")
    assert bh is not None and bh.has_combat_stats
    assert bh.tier_codes()[0] == "000"
    assert bh.crosspaths_for("100") == ()


def test_normal_stats_works_on_a_crosspath_node():
    stats = svc.get_tower_stats("bomb_shooter")
    node = stats.tier("202")
    assert node is not None
    ns = svc.normal_stats(node)  # must not crash on a crosspath tier
    assert ns.damage is not None


# --- heroes: per-level stats for the ~6 heroes with a bloonswiki module ------


def test_loads_quincy_hero_stats():
    stats = svc.get_hero_stats("quincy")
    assert stats is not None
    assert stats.has_combat_stats
    assert stats.base_cost == 540
    assert len(stats.level_codes()) == 20
    assert stats.level_codes()[0] == "1"
    assert stats.level_codes()[-1] == "20"


def test_hero_without_module_returns_none():
    # Obyn attacks in-game, but bloonswiki has no stats module for him, so
    # there is no committed file — must degrade to None, not a crash.
    assert svc.get_hero_stats("obyn_greenfoot") is None
    assert svc.get_hero_stats("does_not_exist") is None


def test_hero_level_progression_uses_normal_stats():
    stats = svc.get_hero_stats("quincy")
    # normal_stats consumes a hero level node exactly like a tower tier.
    l1 = svc.normal_stats(stats.level("1"))
    l20 = svc.normal_stats(stats.level("20"))
    assert l1.pierce == 3
    assert l20.pierce == 9  # pierce climbs with level
    assert l20.cooldown < l1.cooldown  # attacks faster at max level
    assert l20.can_see_camo is True  # Quincy gains camo detection by level 20


def test_paragon_stats_at_degree_is_nonlinear_and_reports_both_dps():
    pid = svc.resolve_paragon("Goliath Doomship")
    assert pid == "goliath_doomship"
    s = svc.paragon_stats_at_degree(pid, 65)
    # Cooldown follows the sqrt curve, NOT linear interpolation (~0.49s).
    assert abs(s.cooldown - 0.4215) < 0.001
    # Goliath has 3 damaging attacks, so total DPS >> main-attack DPS.
    assert s.attack_count == 3
    assert s.main_dps < s.total_dps
    assert abs(s.main_dps - 1181.4) < 0.5
    # Degree-100 jump: damage = base*2 + 10 (not the linear trend).
    base = svc.paragon_stats_at_degree(pid, 1).damage
    assert svc.paragon_stats_at_degree(pid, 100).damage == round(base * 2 + 10, 1)


def test_degree_for_target_dps_uses_total_not_main():
    pid = svc.resolve_paragon("Ace")  # Goliath Doomship via its tower
    # Total DPS is already ~2273 at degree 1, so 1000 DPS is reached immediately.
    assert svc.degree_for_target_dps(pid, 1000) == 1
    # Unreachable target returns None.
    assert svc.degree_for_target_dps(pid, 9_999_999) is None


def test_resolve_paragon_by_name_and_tower():
    assert svc.resolve_paragon("Magus Perfectus") == "magus_perfectus"
    assert svc.resolve_paragon("wizard") == "magus_perfectus"
    assert svc.resolve_paragon("Monkey Ace") == "goliath_doomship"
    assert svc.resolve_paragon("not a tower") is None
