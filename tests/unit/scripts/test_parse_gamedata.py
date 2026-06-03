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
    *, name="Projectile", pierce=2.0, radius=2.0, damage: float | None = 1.0
) -> dict:
    behaviors: list[dict] = [
        {"$type": _t("TravelStraitModel"), "speed": 300.0, "lifespan": 0.25}
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
            }
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
        {"$type": _t("CreateProjectileOnContactModel"), "projectile": explosion}
    )
    attack = mod._clean_attack(_attack(shell), 0)
    names = [p["name"] for p in attack["projectiles"]]
    assert names == ["Projectile", "Explosion"]
    explosion_node = attack["projectiles"][1]
    assert explosion_node["damage"] == 1 and explosion_node["pierce"] == 22


def test_attack_name_strips_class_prefix_and_trailing_underscore(mod):
    attack = mod._clean_attack(_attack(_projectile()), 0)
    assert attack["name"] == "Attack"  # from "AttackModel_Attack_"


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
        {"$type": _t("PerRoundCashBonusTowerModel"), "cashPerRound": 4000.0}
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
        }
    ]
    _write(tdir / "TestTower.json", base)
    # a single crosspath state file
    _write(tdir / "TestTower-100.json", _tower_model(cost=200.0, tower_set=1))
    # the upgrade definition (path/tier are 0-indexed in the dump)
    _write(
        dump / "Upgrades" / "Big Darts.json",
        {"name": "Big Darts", "cost": 140, "xpCost": 0, "path": 0, "tier": 0},
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
    # upgrade resolved with 0-indexed → 1-indexed path/tier.
    assert p["upgrades"] == [
        {"path": 1, "tier": 1, "name": "Big Darts", "cost": 140, "xp": 0}
    ]


def test_validate_anchors(mod, tmp_path):
    dump = tmp_path / "dump"
    _write(dump / "Towers" / "DartMonkey" / "DartMonkey.json", _tower_model(cost=200.0))
    _write(
        dump / "Towers" / "SuperMonkey" / "SuperMonkey.json", _tower_model(cost=2500.0)
    )
    assert mod.validate_anchors(dump) == []
    # A moved anchor must fail loudly.
    _write(dump / "Towers" / "DartMonkey" / "DartMonkey.json", _tower_model(cost=999.0))
    assert mod.validate_anchors(dump)


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
    committed = [{"name": "Projectile", "r": 4}, {"name": "Frag"}, {"name": "Explosion"}]
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
    committed = {"projectiles": [{"name": "A", "pierce": 10}, {"name": "B", "pierce": 5}]}
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
