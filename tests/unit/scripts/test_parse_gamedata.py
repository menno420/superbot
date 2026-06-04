"""Tests for ``scripts/parse_gamedata.py`` — the BTD Mod Helper game-data mapper.

Hermetic: every fixture is a synthetic ``TowerModel``-shaped dict written to a
``tmp_path`` "dump" (no vendored 320 MB clone). The fixtures mirror the real
dump's ``behaviors[]`` ``$type`` shape (verified against ``DartMonkey`` /
``BombShooter`` / ``BananaFarm`` in the v55 dump) so they exercise the
behaviours walk, sub-projectile flattening, the enum maps, and upgrade
resolution.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "parse_gamedata.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("parse_gamedata_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# --- model-shape helpers (mirror the real $type-tagged dump) ----------------


def _t(cls: str) -> str:
    return f"Il2CppAssets.Scripts.Models.Towers.Behaviors.{cls}, Assembly-CSharp"


def _damage_model(damage: float, immune: int = 17) -> dict:
    return {
        "$type": _t("DamageModel"),
        "damage": damage,
        "maxDamage": 0.0,
        "immuneBloonProperties": immune,
        "distributeToChildren": True,
        "name": "DamageModel_",
    }


def _projectile(
    *,
    name="Projectile",
    pierce=2.0,
    radius=2.0,
    damage: float | None = 1.0,
) -> dict:
    behaviors: list[dict] = [
        {"$type": _t("TravelStraitModel"), "speed": 300.0, "lifespan": 0.25},
    ]
    if damage is not None:
        behaviors.insert(0, _damage_model(damage))
    return {
        "$type": _t("ProjectileModel"),
        "id": name,
        "name": f"ProjectileModel_{name}",
        "pierce": pierce,
        "maxPierce": 0.0,
        "radius": radius,
        "behaviors": behaviors,
    }


def _attack(projectile: dict, *, rate=0.95, rng=32.0, name="Attack") -> dict:
    return {
        "$type": _t("AttackModel"),
        "name": f"AttackModel_{name}_",
        "range": rng,
        "weapons": [
            {
                "$type": _t("WeaponModel"),
                "rate": rate,
                "ejectX": -0.8,
                "ejectY": 18.3,
                "ejectZ": 7.0,
                "projectile": projectile,
                "fireWithoutTarget": False,
                "fireBetweenRounds": False,
                "name": "WeaponModel_Weapon",
            },
        ],
    }


def _tower_model(*, cost=200.0, tower_set=1, area=(2,), attacks=None) -> dict:
    return {
        "$type": "Il2CppAssets.Scripts.Models.Towers.TowerModel, Assembly-CSharp",
        "cost": cost,
        "range": 32.0,
        "towerSet": tower_set,
        "areaTypes": list(area),
        "towerSelectionMenuThemeId": "Default",
        "footprint": {
            "$type": _t("CircleFootprintModel"),
            "radius": 6.0,
            "doesntBlockTowerPlacement": False,
            "name": "CircleFootprintModel_",
        },
        "targetTypes": [
            {"$type": "x.TargetType, Assembly-CSharp", "id": tt}
            for tt in ("First", "Last", "Close", "Strong")
        ],
        "upgrades": [],
        "behaviors": list(attacks or [_attack(_projectile())]),
    }


# --- pure walkers -----------------------------------------------------------


def test_clean_projectile_pulls_combat_numbers(mod):
    p = mod._clean_projectile(_projectile(damage=5.0, pierce=210.0))
    assert p["name"] == "Projectile"
    assert p["damage"] == 5
    assert p["pierce"] == 210
    assert p["speed"] == 300
    assert p["lifespan"] == 0.25
    # immuneBloonProperties 17 → Sharp / "Cannot damage Lead or frozen".
    assert p["damage_type"] == "Sharp"
    assert "Lead" in p["cannot_pop"]


def test_whole_floats_render_as_ints(mod):
    p = mod._clean_projectile(_projectile(damage=7.0, radius=12.0))
    assert p["damage"] == 7 and isinstance(p["damage"], int)
    assert p["radius"] == 12 and isinstance(p["radius"], int)


def test_sub_projectiles_are_flattened_as_siblings(mod):
    # A bomb: the thrown shell has no DamageModel; the explosion it spawns on
    # contact does. Both must surface as sibling projectiles (wiki parity).
    explosion = _projectile(name="Explosion", pierce=22.0, radius=12.0, damage=1.0)
    shell = _projectile(name="Projectile", pierce=1.0, radius=4.0, damage=None)
    shell["behaviors"].append(
        {"$type": _t("CreateProjectileOnContactModel"), "projectile": explosion},
    )
    attack = mod._clean_attack(_attack(shell), 0)
    names = [p["name"] for p in attack["projectiles"]]
    assert names == ["Projectile", "Explosion"]
    explosion_node = attack["projectiles"][1]
    assert explosion_node["damage"] == 1 and explosion_node["pierce"] == 22


def test_weapon_behavior_alternate_projectile_is_collected(mod):
    # The bomb's secondary cluster is fired by an AlternateProjectileModel on the
    # *weapon* (not weapon.projectile) — the old CreateProjectile-only walk
    # dropped it (and the real damage projectile of e.g. Psi).
    alt = _projectile(name="Secondary", pierce=5.0, damage=3.0)
    attack = _attack(_projectile(name="Primary", damage=1.0))
    attack["weapons"][0]["behaviors"] = [
        {"$type": _t("AlternateProjectileModel"), "projectile": alt},
    ]
    names = [p["name"] for p in mod._clean_attack(attack, 0)["projectiles"]]
    assert "Primary" in names and "Secondary" in names


def test_spawned_projectiles_detected_by_structure_under_any_field(mod):
    # ProjectileOverTimeModel holds its child under `projectileModel`, not
    # `projectile` — structural detection (by $type) must still find it.
    child = _projectile(name="OverTime", damage=2.0)
    behavior = {"$type": _t("ProjectileOverTimeModel"), "projectileModel": child}
    found = mod._spawned_projectiles(behavior)
    assert len(found) == 1 and found[0]["id"] == "OverTime"


def test_duplicate_projectiles_are_deduped(mod):
    # The same explosion reached via two spawn paths is emitted once (wiki parity).
    shell = _projectile(name="Projectile", damage=None)
    shell["behaviors"].append(
        {
            "$type": _t("CreateProjectileOnContactModel"),
            "projectile": _projectile(name="Explosion", pierce=22.0, damage=1.0),
        },
    )
    shell["behaviors"].append(
        {
            "$type": _t("CreateProjectileOnExpireModel"),
            "projectile": _projectile(name="Explosion", pierce=22.0, damage=1.0),
        },
    )
    names = [p["name"] for p in mod._clean_attack(_attack(shell), 0)["projectiles"]]
    assert names.count("Explosion") == 1


def test_attack_name_strips_class_prefix_and_trailing_underscore(mod):
    attack = mod._clean_attack(_attack(_projectile()), 0)
    assert attack["name"] == "Attack"  # from "AttackModel_Attack_"


def test_subtower_mapped_from_spawn_model(mod):
    # A minion spawned by a CreateTowerModel (inside an ability) is mapped like a
    # tier — its attacks/projectiles surface so "minion pierce" questions resolve.
    minion = _tower_model(
        attacks=[_attack(_projectile(name="Sting", damage=4.0, pierce=3.0))],
    )
    minion["name"] = "Hornet"
    host = _tower_model()
    host["behaviors"].append(
        {
            "$type": _t("AbilityModel"),
            "name": "AbilityModel_Ability",
            "behaviors": [
                {
                    "$type": _t("CreateTowerModel"),
                    "tower": minion,
                    "towerLifetime": 10.0,
                },
            ],
        },
    )
    tier = mod._map_tier(host)
    assert "subtowers" in tier
    sub = tier["subtowers"][0]
    assert sub["name"] == "Hornet"
    assert sub["lifespan"] == 10
    assert sub["attacks"][0]["projectiles"][0]["damage"] == 4


def test_subtower_does_not_recurse_into_nested_spawns(mod):
    # _find_spawn_models must not descend into a spawned tower's own spawns.
    inner = _tower_model()
    inner["name"] = "Inner"
    outer = _tower_model()
    outer["name"] = "Outer"
    outer["behaviors"].append({"$type": _t("CreateTowerModel"), "tower": inner})
    host = _tower_model()
    host["behaviors"].append({"$type": _t("CreateTowerModel"), "tower": outer})
    tier = mod._map_tier(host)
    assert [s["name"] for s in tier.get("subtowers", [])] == ["Outer"]  # not "Inner"


def test_subtower_name_strips_trailing_level(mod):
    assert mod._clean_subtower_name({"name": "MasquedMacaque 10"}) == "MasquedMacaque"
    assert mod._clean_subtower_name({"name": "Phoenix"}) == "Phoenix"
    assert mod._clean_subtower_name({"displayName": "Sun God", "name": "X"}) == "Sun God"


def test_tier_placement_target_and_footprint(mod):
    tier = mod._map_tier(_tower_model(area=(2,)))
    assert tier["placeableOnLand"] is True
    assert tier["placeableOnWater"] is False
    assert tier["footprintRadius"] == 6
    assert tier["range"] == 32
    assert tier["targetTypeFirst"] and tier["targetTypeStrong"]


def test_water_tower_placement(mod):
    tier = mod._map_tier(_tower_model(area=(1,)))
    assert tier["placeableOnWater"] is True
    assert tier["placeableOnLand"] is False


def test_tower_set_maps_to_category(mod):
    assert mod._TOWER_SET == {1: "primary", 2: "military", 4: "magic", 8: "support"}


def test_income_field_is_surfaced(mod):
    model = _tower_model()
    model["behaviors"].append(
        {"$type": _t("PerRoundCashBonusTowerModel"), "cashPerRound": 4000.0},
    )
    tier = mod._map_tier(model)
    assert tier["cashPerRound"] == 4000


# --- dump-level mapping (synthetic on tmp_path) -----------------------------


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _make_dump(tmp_path: Path) -> Path:
    dump = tmp_path / "dump"
    tdir = dump / "Towers" / "TestTower"
    base = _tower_model(cost=200.0, tower_set=1)
    base["upgrades"] = [
        {
            "$type": _t("UpgradePathModel"),
            "tower": "TestTower-100",
            "upgrade": "Big Darts",
        },
    ]
    _write(tdir / "TestTower.json", base)
    # a single crosspath state file
    _write(tdir / "TestTower-100.json", _tower_model(cost=200.0, tower_set=1))
    # the upgrade definition (path/tier are 0-indexed in the dump)
    _write(
        dump / "Upgrades" / "Big Darts.json",
        {
            "name": "Big Darts",
            "cost": 140,
            "xpCost": 0,
            "path": 0,
            "tier": 0,
            "LocsKey": "Big Darts",
        },
    )
    # game localization: upgrade display strings + descriptions
    _write(
        dump / "textTable.json",
        {"Big Darts": "Big Darts", "Big Darts Description": "Darts are bigger."},
    )
    return dump


def test_map_tower_end_to_end(mod, tmp_path):
    dump = _make_dump(tmp_path)
    res = mod.map_tower(dump, "test_tower", "Test Tower", "55.0")
    assert res.warnings == []
    p = res.payload
    assert p["tower_id"] == "test_tower"
    assert p["base_cost"] == 200
    assert p["category"] == "primary"
    assert p["game_version"] == "55.0"
    assert p["source"] == mod._SOURCE
    # base file → tier 000, plus the -100 state.
    assert set(p["tiers"]) == {"000", "100"}
    # upgrade resolved with 0-indexed → 1-indexed path/tier, plus the game's own
    # description resolved through its LocsKey.
    assert p["upgrades"] == [
        {
            "path": 1,
            "tier": 1,
            "name": "Big Darts",
            "cost": 140,
            "xp": 0,
            "description": "Darts are bigger.",
        },
    ]


def test_validate_anchors(mod, tmp_path):
    dump = tmp_path / "dump"
    _write(dump / "Towers" / "DartMonkey" / "DartMonkey.json", _tower_model(cost=200.0))
    _write(
        dump / "Towers" / "SuperMonkey" / "SuperMonkey.json",
        _tower_model(cost=2500.0),
    )
    assert mod.validate_anchors(dump) == []
    # A moved anchor must fail loudly.
    _write(dump / "Towers" / "DartMonkey" / "DartMonkey.json", _tower_model(cost=999.0))
    assert mod.validate_anchors(dump)


def test_overlay_refreshes_tier_range_but_not_projectile_stats(mod):
    # The safety property: tier-level scalars refresh, per-projectile stats do
    # NOT — projectile names aren't reliable keys across wiki/dump, so writing
    # them by name would scramble values (Druid base dart vs storm).
    committed = {
        "base_cost": 200,
        "category": "primary",
        "game_version": "54.0",
        "source": "bloonswiki.com",
        "tiers": {
            "030": {
                "range": 28,
                "attacks": [
                    {
                        "name": "Attack",
                        "projectiles": [
                            {"name": "Projectile", "damage": 1, "pierce": 2},
                        ],
                    },
                ],
            },
        },
    }
    mapped = {
        "base_cost": 200,
        "category": "primary",
        "tiers": {
            "030": {
                "range": 80,
                "attacks": [
                    {
                        "name": "Attack",
                        "projectiles": [
                            {"name": "BaseProjectile", "damage": 100, "pierce": 200},
                        ],
                    },
                ],
            },
        },
    }
    changes = mod.overlay_payload(committed, mapped, "55.0")
    assert committed["tiers"]["030"]["range"] == 80  # tier scalar refreshed
    proj = committed["tiers"]["030"]["attacks"][0]["projectiles"][0]
    assert proj["damage"] == 1 and proj["pierce"] == 2  # projectile LEFT CURATED
    assert committed["game_version"] == "55.0"
    assert "Mod Helper" in committed["source"]
    assert any("range" in c for c in changes)


def test_overlay_refreshes_upgrade_cost_xp_keyed_by_path_tier(mod):
    committed = {
        "tiers": {},
        "upgrades": [
            {"path": 3, "tier": 5, "name": "Flying Fortress", "cost": 85000, "xp": 0},
            {"path": 1, "tier": 1, "name": "Sharp", "cost": 100, "xp": 50},
        ],
    }
    mapped = {
        "tiers": {},
        "upgrades": [  # different order — must align by (path, tier), not index
            {"path": 1, "tier": 1, "cost": 100, "xp": 40},
            {"path": 3, "tier": 5, "cost": 90000, "xp": 0},
        ],
    }
    mod.overlay_payload(committed, mapped, "55.0")

    def up(path, tier):
        return next(
            u for u in committed["upgrades"] if (u["path"], u["tier"]) == (path, tier)
        )

    assert up(3, 5)["cost"] == 90000  # refreshed despite reversed order
    assert up(1, 1)["xp"] == 40
    assert up(3, 5)["name"] == "Flying Fortress"  # curated name preserved


def test_overlay_no_change_leaves_version_and_source(mod):
    committed = {
        "base_cost": 200,
        "category": "primary",
        "game_version": "54.0",
        "source": "w",
        "tiers": {},
    }
    changes = mod.overlay_payload(
        committed,
        {"base_cost": 200, "category": "primary", "tiers": {}},
        "55.0",
    )
    assert changes == []
    assert committed["game_version"] == "54.0"  # untouched when nothing moved


# --- name-preservation guard (step 2) ---------------------------------------


def test_collect_names_walks_nested_name_and_display_name(mod):
    payload = {
        "name": "Druid",
        "tiers": {
            "500": {
                "abilities": [{"displayName": "Ball Lightning"}],
                "attacks": [{"name": "Attack", "projectiles": [{"name": "Bolt"}]}],
            },
        },
    }
    names = mod.collect_names(payload)
    assert names["name"] == "Druid"
    assert names["tiers.500.abilities[0].displayName"] == "Ball Lightning"
    assert names["tiers.500.attacks[0].projectiles[0].name"] == "Bolt"


def test_name_downgrades_flags_emptied_name(mod):
    # PR-1.5 regression: a naïve refresh blanks "Arctic Wind" (dump zone name "").
    before = {"tiers.4.abilities[0].name": "Arctic Wind"}
    after = {"tiers.4.abilities[0].name": ""}
    bad = mod.name_downgrades(before, after)
    assert len(bad) == 1 and "Arctic Wind" in bad[0] and "emptied" in bad[0]


def test_name_downgrades_flags_curated_to_internal(mod):
    # PR-1.5 regression: "Reanimate" (editorial) → "Attack Necromancer" (model id).
    before = {"abilities[0].name": "Reanimate"}
    after = {"abilities[0].name": "Attack Necromancer"}
    bad = mod.name_downgrades(
        before, after, internal_names=frozenset({"Attack Necromancer"})
    )
    assert len(bad) == 1 and "internal model string" in bad[0]


def test_name_downgrades_flags_any_change_for_frozen_overlay(mod):
    before = {"name": "Reanimate"}
    after = {"name": "Something Else"}
    bad = mod.name_downgrades(before, after)  # no internal_names → "(changed)"
    assert len(bad) == 1 and "changed" in bad[0]


def test_name_downgrades_allows_preserved_and_newly_set_names(mod):
    before = {"name": "Druid", "blank": ""}
    after = {"name": "Druid", "blank": "Now Named", "added": "Fresh"}
    # equal curated name held; an empty→named upgrade and a brand-new name are
    # not downgrades.
    assert mod.name_downgrades(before, after) == []


def test_assert_names_preserved_raises_on_downgrade(mod):
    with pytest.raises(mod.NameDowngradeError) as exc:
        mod.assert_names_preserved({"a.name": "Arctic Wind"}, {"a.name": ""})
    assert "Arctic Wind" in str(exc.value)


def test_overlay_preserves_names_and_passes_guard(mod):
    # A normal numeric overlay touches no name → the guard is satisfied silently.
    committed = {
        "name": "Druid",
        "tiers": {
            "500": {
                "range": 28,
                "abilities": [{"name": "Reanimate"}],
                "attacks": [{"name": "Attack"}],
            },
        },
    }
    mapped = {"name": "Druid", "tiers": {"500": {"range": 80}}}
    mod.overlay_payload(committed, mapped, "55.0")
    assert committed["tiers"]["500"]["abilities"][0]["name"] == "Reanimate"
    assert committed["name"] == "Druid"


def test_ability_uses_game_display_name(mod):
    ability = {
        "$type": _t("AbilityModel"),
        "name": "AbilityModel_Ability",
        "displayName": "Cocktail of Fire",
        "cooldown": 15.0,
    }
    assert mod._clean_ability(ability, 0)["name"] == "Cocktail of Fire"


def test_ability_falls_back_to_internal_name_without_display_name(mod):
    ability = {"$type": _t("AbilityModel"), "name": "AbilityModel_Ability"}
    assert mod._clean_ability(ability, 0)["name"] == "Ability"


def test_pascal_name_mapping(mod):
    assert mod._pascal("Captain Churchill") == "CaptainChurchill"
    assert mod._pascal("Dart Monkey") == "DartMonkey"
    assert mod._pascal("Obyn Greenfoot") == "ObynGreenfoot"


# --- damage-modifier fidelity (the v55 "uniform 1.0" trap) ------------------


def _tag_mod(tag: str, *, additive: float = 0.0, multiplier: float = 1.0) -> dict:
    # The real bonus lives in `damageAddative` (sic); `damageMultiplier` is a
    # separate, almost-always-1.0 field.
    return {
        "$type": _t("DamageModifierForTagModel"),
        "tag": tag,
        "damageMultiplier": multiplier,
        "damageAddative": additive,
        "name": "DamageModifierForTagModel_",
    }


def test_tag_bonus_read_from_misspelled_additive_field(mod):
    # Ultra-Juggernaut Lead +20 is stored in `damageAddative`, not the multiplier.
    proj = _projectile()
    proj["behaviors"].append(_tag_mod("Lead", additive=20.0))
    cleaned = mod._clean_projectile(proj)
    assert cleaned["damageModifierForLead"] == 20


def test_neutral_modifier_not_emitted(mod):
    # additive 0 + multiplier 1 = no real bonus → emit nothing (don't overwrite
    # curated data with a no-op).
    proj = _projectile()
    proj["behaviors"].append(_tag_mod("Ceramic", additive=0.0, multiplier=1.0))
    cleaned = mod._clean_projectile(proj)
    assert "damageModifierForCeramic" not in cleaned


# --- fidelity audit ---------------------------------------------------------


def test_audit_equal_ignores_float_precision(mod):
    # The wiki rounds (0.3616); the dump is full precision (0.36160713).
    assert mod._audit_equal(0.3616, 0.36160713)
    assert mod._audit_equal(5, 5.0)
    assert not mod._audit_equal(28, 80)


def test_audit_equal_bools_compared_by_identity(mod):
    assert mod._audit_equal(True, True)
    assert not mod._audit_equal(True, False)
    # a bool is never "equal" to a number even when Python would say 1 == True.
    assert not mod._audit_equal(True, 1)


def test_align_named_pairs_by_name_not_index(mod):
    committed = [
        {"name": "Projectile", "r": 4},
        {"name": "Frag"},
        {"name": "Explosion"},
    ]
    mapped = [{"name": "Projectile", "r": 4}, {"name": "Explosion"}, {"name": "Frag"}]
    pairs = mod._align_named(committed, mapped)
    assert [n for n, _, _ in pairs] == ["Projectile", "Frag", "Explosion"]
    # the Explosion pair lines up across the two different orders
    _, c_expl, m_expl = next(p for p in pairs if p[0] == "Explosion")
    assert c_expl["name"] == m_expl["name"] == "Explosion"


def test_align_named_falls_back_on_duplicate_or_missing_names(mod):
    assert mod._align_named([{"name": "a"}, {"name": "a"}], [{"name": "a"}]) is None
    assert mod._align_named([{"x": 1}], [{"x": 2}]) is None


def test_walk_audit_tallies_named_alignment(mod):
    stats: dict = {}
    committed = {
        "projectiles": [{"name": "A", "pierce": 10}, {"name": "B", "pierce": 5}],
    }
    mapped = {"projectiles": [{"name": "B", "pierce": 5}, {"name": "A", "pierce": 7}]}
    mod._walk_audit(committed, mapped, "root", stats, "ctx")
    # A.pierce differs (10 vs 7), B.pierce matches → 1 diff / 2 total, despite
    # the reversed order.
    assert stats["pierce"].diffs == 1
    assert stats["pierce"].total == 2
    assert stats["pierce"].verdict == "SUSPECT"  # 50% > 20%


def test_field_stat_verdict_thresholds(mod):
    clean = mod._FieldStat(total=10, diffs=0)
    delta = mod._FieldStat(total=100, diffs=10)
    suspect = mod._FieldStat(total=100, diffs=50)
    assert clean.verdict == "CLEAN"
    assert delta.verdict == "DELTA"
    assert suspect.verdict == "SUSPECT"


def test_audit_upgrades_aligned_by_path_tier(mod):
    stats: dict = {}
    # Same upgrades, different list order — index diff would be all-phantom.
    committed = [
        {"path": 1, "tier": 1, "cost": 140},
        {"path": 2, "tier": 1, "cost": 200},
    ]
    mapped = [
        {"path": 2, "tier": 1, "cost": 200},
        {"path": 1, "tier": 1, "cost": 170},  # a real cost change
    ]
    mod._audit_upgrades(committed, mapped, stats, "rel")
    assert stats["cost"].diffs == 1  # only the (1,1) cost change, not a swap
    assert stats["cost"].total == 2


# --- upgrade description overlay (step 4) -----------------------------------


def test_apply_upgrade_descriptions_aligns_by_path_tier(mod):
    committed = {
        "upgrades": [
            {"path": 1, "tier": 1, "name": "Sharp Shots", "cost": 140},
            {"path": 3, "tier": 5, "name": "Crossbow Master", "cost": 60000},
        ],
    }
    mapped = {
        "upgrades": [  # reversed order + a description on each
            {"path": 3, "tier": 5, "description": "Rapid long-range crossbow."},
            {"path": 1, "tier": 1, "description": "Can pop 1 extra Bloon per shot."},
        ],
    }
    changes = mod.apply_upgrade_descriptions(committed, mapped)
    by = {(u["path"], u["tier"]): u for u in committed["upgrades"]}
    assert by[(1, 1)]["description"] == "Can pop 1 extra Bloon per shot."
    assert by[(3, 5)]["description"] == "Rapid long-range crossbow."
    assert by[(1, 1)]["name"] == "Sharp Shots"  # name untouched
    assert len(changes) == 2


def test_apply_upgrade_descriptions_skips_unmatched_and_empty(mod):
    committed = {
        "upgrades": [
            {"path": 1, "tier": 4, "name": "Operation: Dart Storm"},  # no mapped match
            {"path": 1, "tier": 1, "name": "Sharp"},
        ],
    }
    mapped = {
        "upgrades": [
            {"path": 1, "tier": 1, "description": ""},  # empty -> skip
        ],
    }
    changes = mod.apply_upgrade_descriptions(committed, mapped)
    assert changes == []
    assert "description" not in committed["upgrades"][0]
    assert "description" not in committed["upgrades"][1]


def test_apply_upgrade_descriptions_never_downgrades_a_name(mod):
    # A description write that somehow blanked a name must hard-stop (defence in
    # depth — the writer only touches `description`, but the guard proves it).
    committed = {"name": "Druid", "upgrades": []}
    mapped = {"upgrades": []}
    mod.apply_upgrade_descriptions(committed, mapped)  # no-op, name intact
    assert committed["name"] == "Druid"


# --- hero per-level description overlay (step 4b) ---------------------------


def test_apply_hero_descriptions_aligns_by_level(mod):
    committed = {
        "levels": {
            "1": {"level": 1, "range": 30},
            "11": {"level": 11, "range": 35},
        },
    }
    mapped = {
        "levels": {
            "1": {"description": "Curses Bloons with dark voodoo power."},
            "11": {"description": "Increases pierce of reanimated Bloons by 50%."},
            "12": {"description": "unmatched level — ignored"},
        },
    }
    changes = mod.apply_hero_descriptions(committed, mapped)
    assert committed["levels"]["1"]["description"].startswith("Curses Bloons")
    assert "50%" in committed["levels"]["11"]["description"]
    assert committed["levels"]["1"]["range"] == 30  # stats untouched
    assert len(changes) == 2


def test_apply_hero_descriptions_skips_empty(mod):
    committed = {"levels": {"1": {"level": 1}}}
    mapped = {"levels": {"1": {"description": ""}}}
    assert mod.apply_hero_descriptions(committed, mapped) == []
    assert "description" not in committed["levels"]["1"]


def test_apply_upgrade_descriptions_texttable_fallback_by_curated_name(mod):
    # The 2 cards the mapper under-emits: fall back to the game's
    # "<curated name> Description" when the mapped payload has none.
    committed = {"upgrades": [{"path": 1, "tier": 4, "name": "Operation: Dart Storm"}]}
    mapped = {"upgrades": []}  # mapper emitted nothing for this node
    tt = {"Operation: Dart Storm Description": "Shoots 16 darts per volley."}
    changes = mod.apply_upgrade_descriptions(committed, mapped, tt)
    assert committed["upgrades"][0]["description"] == "Shoots 16 darts per volley."
    assert len(changes) == 1
    # An editorial name not in the textTable stays empty (never invented).
    c2 = {"upgrades": [{"path": 3, "tier": 5, "name": "Reanimate"}]}
    assert mod.apply_upgrade_descriptions(c2, {"upgrades": []}, tt) == []
    assert "description" not in c2["upgrades"][0]
