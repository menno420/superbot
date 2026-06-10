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


def test_economy_tower_has_costs_and_tiers_but_no_attacks():
    # Since the Q-0067 cutover the Farm has full game-native tiers (abilities,
    # buffs, income) — but its nominal banana "attack" is suppressed, so no
    # tier carries combat numbers.
    farm = svc.get_tower_stats("banana_farm")
    assert farm is not None
    assert farm.base_cost == 1250
    assert farm.has_combat_stats is True
    assert farm.tier_codes()[0] == "000"
    base = svc.normal_stats(farm.tier("000"))
    assert base.damage is None and base.cooldown is None
    assert all(t.get("attacks") == [] for t in farm.tiers.values())


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
    # No committed file is 16-tier any more (the cutover gave Beast Handler its
    # full 64, incl. dual-beast crosspaths) — keep the degrade path pinned with
    # a synthetic single-path-only stats object.
    import dataclasses

    bh = svc.get_tower_stats("beast_handler")
    assert bh is not None and bh.has_combat_stats
    assert bh.tier_codes()[0] == "000"
    assert "320" in bh.tiers  # dual-beast crosspaths are real data now
    sparse = dataclasses.replace(
        bh,
        tiers={c: t for c, t in bh.tiers.items() if not tier_codes.is_crosspath(c)},
    )
    assert sparse.crosspaths_for("100") == ()


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


def test_unknown_hero_returns_none():
    # A hero id with no committed stats file degrades to None, not a crash.
    assert svc.get_hero_stats("does_not_exist") is None


def test_game_data_closed_the_obyn_stats_gap():
    # Obyn attacks in-game but bloonswiki never had a stats module for him; the
    # BTD Mod Helper game-data export does, so he now has per-level stats.
    stats = svc.get_hero_stats("obyn_greenfoot")
    assert stats is not None
    assert stats.level("1") is not None


def test_hero_level_progression_uses_normal_stats():
    stats = svc.get_hero_stats("quincy")
    # normal_stats consumes a hero level node exactly like a tower tier.
    l1 = svc.normal_stats(stats.level("1"))
    l20 = svc.normal_stats(stats.level("20"))
    assert l1.pierce == 3
    assert l20.pierce == 9  # pierce climbs with level
    assert l20.cooldown < l1.cooldown  # attacks faster at max level
    assert l20.can_see_camo is True  # Quincy gains camo detection by level 20


def test_paragon_stats_at_degree_gives_nonlinear_per_attack_breakdown():
    pid = svc.resolve_paragon("Goliath Doomship")
    assert pid == "goliath_doomship"
    s = svc.paragon_stats_at_degree(pid, 65)
    # Authoritative breakdown: 3 attacks, each with its real projectiles — the
    # main bomb keeps BOTH its direct projectile AND its explosion (the exact
    # components that a single "DPS" number hides).
    assert len(s.attacks) == 3
    main = s.attacks[0]
    # Game-native names since the cutover: the direct hit is "MainProjectile"
    # (200), the explosion is "Projectile" (300).
    assert {p[0] for p in main.projectiles} >= {"MainProjectile", "Projectile"}
    # Cooldown is the sqrt curve, NOT linear interpolation (~0.49s).
    assert abs(main.cooldown - 0.4215) < 0.001
    # rough_dps is only an estimate (sum of all projectiles / cooldown), > 0.
    assert s.rough_dps > 0
    # Degree-100 jump: a projectile's damage = base*2 + 10, not a linear trend.
    d1 = svc.paragon_stats_at_degree(pid, 1).attacks[0].projectiles[0][1]
    d100 = svc.paragon_stats_at_degree(pid, 100).attacks[0].projectiles[0][1]
    assert d100 == round(d1 * 2 + 10, 1)


def test_rough_attack_dps_sums_all_projectiles_and_is_none_for_economy():
    # Goliath's main bomb = 200 (direct) + 300 (explosion) per shot, so the rough
    # DPS counts both, not just the highest.
    goliath = svc.get_paragon_stats("goliath_doomship").base["attacks"]
    main_only = svc.main_projectile_stats(goliath, 1)[0] / 0.66  # explosion / cd
    rough = svc.rough_attack_dps(goliath[:1], 1)  # just the main attack
    assert rough > main_only  # summing both projectiles beats the single highest
    # No damaging attack (e.g. an economy tower's tier) -> None.
    assert svc.rough_attack_dps([]) is None


def test_resolve_paragon_by_name_and_tower():
    assert svc.resolve_paragon("Magus Perfectus") == "magus_perfectus"
    assert svc.resolve_paragon("wizard") == "magus_perfectus"
    assert svc.resolve_paragon("Monkey Ace") == "goliath_doomship"
    assert svc.resolve_paragon("not a tower") is None
