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
    assert (
        mod._clean_subtower_name({"displayName": "Sun God", "name": "X"}) == "Sun God"
    )


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


def test_map_powers_extracts_named_skips_hidden(mod, tmp_path):
    dump = tmp_path / "dump"
    _write(
        dump / "Powers" / "MonkeyBoost.json",
        {
            "$type": _t("MonkeyBoostPower"),
            "PowerId": "MonkeyBoost",
            "Cost": 100,
            "quantity": 1,
            "canBeActivatedBetweenRounds": False,
        },
    )
    # a hidden/event power with no textTable name → skipped, not surfaced raw
    _write(
        dump / "Powers" / "SpookyCreature.json",
        {"$type": _t("Pow"), "PowerId": "SpookyCreature", "Cost": 50},
    )
    _write(
        dump / "textTable.json",
        {
            "MonkeyBoost": "Monkey Boost",
            "MonkeyBoost Description": "Attack faster <sup>TM</sup>",
        },
    )
    rows, warnings = mod.map_powers(dump, "55.1")
    assert [r["id"] for r in rows] == ["monkey_boost"]  # SpookyCreature dropped
    row = rows[0]
    assert row["canonical"] == "Monkey Boost"
    assert row["monkey_money_cost"] == 100
    # tags are stripped, inner text (the TM, the words) is kept.
    assert row["description"] == "Attack faster TM"


def test_map_powers_fills_placeholder_and_extracts_effect(mod, tmp_path):
    dump = tmp_path / "dump"
    _write(
        dump / "Powers" / "MonkeyBoost.json",
        {
            "$type": _t("MonkeyBoostPower"),
            "PowerId": "MonkeyBoost",
            "Cost": 100,
            "behaviors": [
                {"$type": _t("MonkeyBoostModel"), "rateScale": 0.5, "duration": 15.0},
            ],
        },
    )
    _write(
        dump / "textTable.json",
        {
            "MonkeyBoost": "Monkey Boost",
            "MonkeyBoost Description": "All towers attack twice as fast for {0} seconds.",
        },
    )
    row = mod.map_powers(dump, "55.1")[0][0]
    # structured factor extracted from the dump effect model
    assert row["effect"] == {"rate_scale": 0.5, "duration_seconds": 15}
    # the {0} window is filled from that same value (the player-facing form)
    assert row["description"] == "All towers attack twice as fast for 15 seconds."


def test_map_powers_pct_fill_renders_scale_as_percent(mod, tmp_path):
    dump = tmp_path / "dump"
    _write(
        dump / "Powers" / "Thrive.json",
        {
            "$type": _t("ThrivePower"),
            "PowerId": "Thrive",
            "Cost": 70,
            "behaviors": [{"$type": _t("ThriveModel"), "cashScale": 1.25}],
        },
    )
    _write(
        dump / "textTable.json",
        {"Thrive": "Thrive", "Thrive Description": "Increase cash by {0}% this round."},
    )
    row = mod.map_powers(dump, "55.1")[0][0]
    assert row["effect"] == {"cash_scale": 1.25}
    # 1.25 scale → "25" (the % is already in the text), not "1.25" or "125".
    assert row["description"] == "Increase cash by 25% this round."


def test_map_geraldo_items_decodes_name_cost_and_meta(mod, tmp_path):
    dump = tmp_path / "dump"
    # The name/description key off the model's locsId via "<locsId> name" /
    # "<locsId> description"; an item whose name string is missing is skipped.
    _write(
        dump / "GeraldoItems" / "GenieBottle.json",
        {
            "$type": _t("GeraldoItemModel"),
            "name": "GenieBottle",
            "locsId": "Genie bottle",
            "cost": 2500,
            "levelUnlockedAt": 12,
            "startingQuantity": 1,
            "maxQuantity": 2,
            "roundsToReplenish": 5,
            "amountToReplenish": 1,
            "canBeActivatedBetweenRounds": True,
        },
    )
    _write(
        dump / "GeraldoItems" / "HiddenThing.json",
        {"$type": _t("GeraldoItemModel"), "name": "HiddenThing", "locsId": "missing"},
    )
    _write(
        dump / "textTable.json",
        {
            "Genie bottle name": "Genie Bottle",
            "Genie bottle description": "Summon a Genie Monkey<br>for a while!",
        },
    )
    rows, warnings = mod.map_geraldo_items(dump, "55.1")
    assert [r["id"] for r in rows] == ["genie_bottle"]  # HiddenThing skipped + warned
    assert any("HiddenThing" in w for w in warnings)
    row = rows[0]
    assert row["canonical"] == "Genie Bottle"
    assert row["description"] == "Summon a Genie Monkeyfor a while!"  # tags stripped
    assert row["cost"] == 2500 and row["unlock_level"] == 12
    assert row["starting_quantity"] == 1 and row["max_quantity"] == 2
    assert row["rounds_to_replenish"] == 5 and row["amount_to_replenish"] == 1
    assert row["between_rounds"] is True


def test_map_geraldo_items_extracts_structured_effect(mod, tmp_path):
    dump = tmp_path / "dump"
    # Sharpening Stone's named behaviour model carries the effect numbers; the
    # mapper reads them into a structured `effect` (values from the dump).
    _write(
        dump / "GeraldoItems" / "SharpeningStone.json",
        {
            "$type": _t("GeraldoItemModel"),
            "name": "SharpeningStone",
            "locsId": "Sharpening stone",
            "cost": 200,
            "levelUnlockedAt": 5,
            "behaviorModels": [
                {
                    "$type": "x.SharpeningStoneBehaviorModel, Assembly-CSharp",
                    "pierceIncrease": 1.0,
                    "rounds": 10,
                },
            ],
        },
    )
    # A projectile item with no named effect model stays description-only.
    _write(
        dump / "GeraldoItems" / "BladeTrap.json",
        {
            "$type": _t("GeraldoItemModel"),
            "name": "BladeTrap",
            "locsId": "Blade trap",
            "cost": 650,
            "levelUnlockedAt": 7,
            "behaviorModels": [{"$type": "x.GeraldoCreateProjectileModel, A"}],
        },
    )
    _write(
        dump / "textTable.json",
        {
            "Sharpening stone name": "Sharpening Stone",
            "Sharpening stone description": "Sharper than ever!",
            "Blade trap name": "Blade Trap",
            "Blade trap description": "Whirling blades!",
        },
    )
    rows = {r["id"]: r for r in mod.map_geraldo_items(dump, "55.1")[0]}
    assert rows["sharpening_stone"]["effect"] == {"pierce_increase": 1, "rounds": 10}
    assert "effect" not in rows["blade_trap"]  # never fabricated


def _bloon_model(
    bid,
    *,
    base=None,
    props=0,
    camo=False,
    grow=False,
    fort=False,
    children=None,
    health=None,
    speed=None,
):
    m = {
        "$type": "Il2CppAssets.Scripts.Models.Bloons.BloonModel, Assembly-CSharp",
        "id": bid,
        "baseId": base or bid,
        "bloonProperties": props,
        "isCamo": camo,
        "isGrow": grow,
        "isFortified": fort,
        "behaviors": [],
    }
    if health is not None:
        m["maxHealth"] = health
    if speed is not None:
        m["speed"] = speed
    if children is not None:
        m["behaviors"].append(
            {
                "$type": "Il2CppAssets.Scripts.Models.Bloons.Behaviors.SpawnChildrenModel, Assembly-CSharp",
                "children": children,
                "name": "",
            },
        )
    return m


def test_bloon_children_resolve_base_and_preserve_modifiers(mod, tmp_path):
    dump = tmp_path / "dump"
    # A BAD-like bloon spawning 2 plain ZOMG + 3 *camo* DDT, plus the variant
    # child models that carry the baseId + modifier flags.
    _write(
        dump / "Bloons" / "Bad" / "Bad.json",
        _bloon_model("Bad", children=["Zomg", "Zomg", "DdtCamo", "DdtCamo", "DdtCamo"]),
    )
    _write(dump / "Bloons" / "Zomg" / "Zomg.json", _bloon_model("Zomg"))
    _write(
        dump / "Bloons" / "Ddt" / "DdtCamo.json",
        _bloon_model("DdtCamo", base="Ddt", camo=True),
    )

    meta = mod._bloon_variant_meta(dump)
    assert meta["ddtcamo".lower()] == ("Ddt", ["camo"])

    raw = json.loads((dump / "Bloons" / "Bad" / "Bad.json").read_text())
    children = mod._bloon_children_list(raw, meta)
    assert children == [
        {"bloon_id": "zomg", "count": 2, "modifiers": []},
        {"bloon_id": "ddt", "count": 3, "modifiers": ["camo"]},
    ]
    canon = {"zomg": "ZOMG", "ddt": "DDT"}
    assert mod._children_prose(children, canon) == "2 ZOMGs and 3 Camo DDTs"


def test_inherently_modified_bloon_selects_its_variant_model(mod, tmp_path):
    # Regression: a DDT is inherently Camo, so it must read from the DdtCamo model
    # (children CeramicRegrowCamo), NOT the non-camo base Ddt template (children
    # CeramicRegrow) — the base would wrongly drop Camo from DDT's children.
    dump = tmp_path / "dump"
    _write(
        dump / "Bloons" / "Ddt" / "Ddt.json",
        _bloon_model("Ddt", children=["CeramicRegrow"]),
    )
    _write(
        dump / "Bloons" / "Ddt" / "DdtCamo.json",
        _bloon_model("DdtCamo", base="Ddt", camo=True, children=["CeramicRegrowCamo"]),
    )
    _write(
        dump / "Bloons" / "Ceramic" / "CeramicRegrow.json",
        _bloon_model("CeramicRegrow", base="Ceramic", grow=True),
    )
    _write(
        dump / "Bloons" / "Ceramic" / "CeramicRegrowCamo.json",
        _bloon_model("CeramicRegrowCamo", base="Ceramic", camo=True, grow=True),
    )

    index = mod._bloon_model_index(dump)
    # The inherently-camo bloon resolves to the camo variant...
    camo_ddt = {"id": "ddt", "properties": ["camo", "lead", "black"]}
    assert mod._select_bloon_model(camo_ddt, index).name == "DdtCamo.json"
    # ...and a plain bloon resolves to the unmodified base.
    plain = {"id": "ddt", "properties": ["lead", "black"]}
    assert mod._select_bloon_model(plain, index).name == "Ddt.json"


def test_bloon_immunity_derives_from_property_bitflag(mod, tmp_path):
    # The parser sources immunity from the shared damage-types inverter; Zebra's
    # 6 (Black|White) resolves to the union of their immunities.
    from utils.btd6.damage_types import immunities_for_bloon_properties

    assert set(immunities_for_bloon_properties(6)) == {
        "Explosion",
        "Glacier",
        "Cold",
        "Frigid",
    }


def test_select_bloon_variant_model_picks_fortified(mod, tmp_path):
    dump = tmp_path / "dump"
    _write(dump / "Bloons" / "Ceramic" / "Ceramic.json", _bloon_model("Ceramic"))
    _write(
        dump / "Bloons" / "Ceramic" / "CeramicFortified.json",
        _bloon_model("CeramicFortified", base="Ceramic", fort=True),
    )
    index = mod._bloon_model_index(dump)
    bloon = {"id": "ceramic", "properties": []}
    # The base selector picks the plain model; the variant selector adds fortified.
    assert mod._select_bloon_model(bloon, index).name == "Ceramic.json"
    fort = mod._select_bloon_variant_model(bloon, index, frozenset({"fortified"}))
    assert fort.name == "CeramicFortified.json"
    # A bloon with no fortified variant in the dump → None (never invented).
    _write(dump / "Bloons" / "Red" / "Red.json", _bloon_model("Red"))
    index = mod._bloon_model_index(dump)
    assert (
        mod._select_bloon_variant_model(
            {"id": "red", "properties": []}, index, frozenset({"fortified"})
        )
        is None
    )


def test_overlay_bloons_sources_health_speed_and_fortified(mod, tmp_path, monkeypatch):
    # The stats overlay corrects health/speed/health_fortified from the dump and
    # leaves rbe alone (rbe is derived + pinned by the RBE test, not a dump scalar).
    dump = tmp_path / "dump"
    _write(
        dump / "Bloons" / "Ceramic" / "Ceramic.json",
        _bloon_model("Ceramic", health=10, speed=62.5),
    )
    _write(
        dump / "Bloons" / "Ceramic" / "CeramicFortified.json",
        _bloon_model("CeramicFortified", base="Ceramic", fort=True, health=20),
    )
    data_root = tmp_path / "data"
    _write(
        data_root / "bloons.json",
        {
            "data_version": "1.0",
            "game_version": "55.1",
            "source": "wiki",
            "bloons": [
                {
                    "id": "ceramic",
                    "canonical": "Ceramic",
                    "properties": [],
                    "health": 99,  # wrong — dump says 10
                    "speed": 1.0,  # wrong — dump says 62.5
                    "health_fortified": 999,  # wrong — fortified model says 20
                    "rbe": 104,  # derived; overlay must leave it untouched
                    "immune_to": [],
                    "children_list": [],
                },
            ],
        },
    )
    monkeypatch.setattr(mod, "_DATA_ROOT", data_root)
    report = mod.overlay_bloons(dump, dry_run=False)
    assert set(report["ceramic"]) == {
        "health 99 -> 10",
        "speed 1.0 -> 62.5",
        "health_fortified 999 -> 20",
    }
    written = json.loads((data_root / "bloons.json").read_text())["bloons"][0]
    assert written["health"] == 10 and written["speed"] == 62.5
    assert written["health_fortified"] == 20
    assert written["rbe"] == 104  # derived value preserved
    # Provenance marker broadened to list every game-sourced field.
    payload = json.loads((data_root / "bloons.json").read_text())
    assert "health" in payload["game_sourced_fields"]
    assert "children_immunity_source" not in payload


def _mode_mut(short, **fields):
    """A single mutatorMods entry with the dump's fully-qualified ``$type``."""
    return {
        "$type": f"Il2CppAssets.Scripts.Models.Gameplay.Mods.{short}, Assembly-CSharp",
        **fields,
    }


def test_parse_mode_rules_normalizes_mutators_and_drops_economy_noise(mod):
    raw = {
        "mutatorMods": [
            _mode_mut("StartingCashModModel", changeBase=650.0, multiplier=0.0),
            _mode_mut("MaxHealthModModel", set=1.0),  # the 1-life cap
            _mode_mut("StartingRoundModModel", round=6),
            _mode_mut("EndRoundModModel", round=100),
            _mode_mut("GlobalCostModModel", multiplier=1.2),
            _mode_mut("LockTowerModModel", towerToLock="BananaFarm"),
            _mode_mut("LockTowerSetModModel", towerSetToLock=2),  # Military
            _mode_mut("DisableContinueModModel"),
            _mode_mut("DisableMonkeyKnowledgeModModel"),
            # Standard economy curve — must be dropped, not surfaced as a rule.
            _mode_mut("MonkeyMoneyModModel", changeBase=1.0, multiplier=0.0),
            _mode_mut("BonusCashPerRoundModModel", baseCash=5, roundMultiple=1),
            _mode_mut("SellMultiplierModModel", addition=0.7, multiplier=0.0),
        ],
    }
    assert mod._parse_mode_rules(raw) == {
        "starting_cash": 650,
        "starting_lives": 1,
        "start_round": 6,
        "end_round": 100,
        "cost_multiplier": 1.2,
        "no_continues": True,
        "no_monkey_knowledge": True,
        "locked_tower_classes": ["military"],
        "locked_towers": ["BananaFarm"],
    }
    # A HalfCash-style mod sets only the income multiplier; nothing else leaks in.
    assert mod._parse_mode_rules(
        {"mutatorMods": [_mode_mut("ModifyAllCashModModel", multiplier=0.5)]},
    ) == {"income_multiplier": 0.5}


def test_overlay_modes_attaches_rules_and_corrects_scalars(mod, tmp_path, monkeypatch):
    dump = tmp_path / "dump"
    # Sandbox's absolute lives override differs from a curated typo (extra 9).
    _write(
        dump / "Mods" / "Sandbox.json",
        {
            "mutatorMods": [
                _mode_mut("StartingCashModModel", changeBase=9999999.0, multiplier=0.0),
                _mode_mut("StartingHealthModModel", addition=999999.0, multiplier=0.0),
            ],
        },
    )
    _write(
        dump / "Mods" / "Impoppable.json",
        {
            "mutatorMods": [
                _mode_mut("StartingRoundModModel", round=6),
                _mode_mut("MaxHealthModModel", set=1.0),
                _mode_mut("GlobalCostModModel", multiplier=1.2),
                _mode_mut("EndRoundModModel", round=100),
            ],
        },
    )
    data_root = tmp_path / "data"
    _write(
        data_root / "modes.json",
        {
            "data_version": "3.0",
            "game_version": "55.1",
            "source": "curated",
            "modes": [
                {
                    "id": "sandbox",
                    "canonical": "Sandbox",
                    "kind": "mode",
                    "aliases": [],
                    "description": "",
                    "restrictions": [],
                    "starting_cash": 9999999,
                    "starting_lives": 9999999,  # curated typo — dump says 999999
                },
                {
                    "id": "impoppable",
                    "canonical": "Impoppable",
                    "kind": "mode",
                    "aliases": [],
                    "description": "",
                    "restrictions": [],
                    "starting_cash": 650,
                    "starting_lives": 1,  # already correct (MaxHealth.set=1)
                },
                {
                    "id": "standard",  # no Mods file → no rules attached
                    "canonical": "Standard",
                    "kind": "mode",
                    "aliases": [],
                    "description": "",
                    "restrictions": [],
                    "starting_cash": 650,
                    "starting_lives": 150,
                },
            ],
        },
    )
    monkeypatch.setattr(mod, "_DATA_ROOT", data_root)
    report = mod.overlay_modes(dump, dry_run=False)
    assert report["sandbox"] == ["starting_lives 9999999 -> 999999"]
    assert report["impoppable"] == []  # rules attached, no scalar correction
    assert "standard" not in report  # unmapped → untouched

    written = {
        m["id"]: m for m in json.loads((data_root / "modes.json").read_text())["modes"]
    }
    assert written["sandbox"]["starting_lives"] == 999999
    assert written["impoppable"]["rules"] == {
        "start_round": 6,
        "starting_lives": 1,
        "cost_multiplier": 1.2,
        "end_round": 100,
    }
    assert "rules" not in written["standard"]
    payload = json.loads((data_root / "modes.json").read_text())
    assert payload["mode_rules_source"]


def test_overlay_modes_restamps_game_version_on_verified_run(
    mod, tmp_path, monkeypatch
):
    # A verified run IS the version claim: the stamp must move to the dump's
    # version even with 0 corrections (modes.json sat at 55.0 after a
    # values-didn't-change 55.1 verification pass).
    dump = tmp_path / "dump"
    _write(dump / "Mods" / "Impoppable.json", {"mutatorMods": []})
    data_root = tmp_path / "data"
    _write(
        data_root / "modes.json",
        {
            "data_version": "3.0",
            "game_version": "55.0",
            "source": "curated",
            "modes": [],
        },
    )
    monkeypatch.setattr(mod, "_DATA_ROOT", data_root)
    monkeypatch.setattr(mod, "_dump_version", lambda _dump: "55.9")
    mod.overlay_modes(dump, dry_run=False)
    payload = json.loads((data_root / "modes.json").read_text())
    assert payload["game_version"] == "55.9"


def test_overlay_bloons_restamps_game_version_on_verified_run(
    mod, tmp_path, monkeypatch
):
    # Same re-stamp rule as overlay_modes — and a gitless dump (no derivable
    # version) must leave the stamp untouched rather than blank it.
    dump = tmp_path / "dump"
    _write(
        dump / "Bloons" / "Ceramic" / "Ceramic.json",
        _bloon_model("Ceramic", health=10, speed=62.5),
    )
    data_root = tmp_path / "data"
    bloons_payload = {
        "data_version": "1.0",
        "game_version": "55.0",
        "source": "wiki",
        "bloons": [
            {
                "id": "ceramic",
                "canonical": "Ceramic",
                "properties": [],
                "health": 10,
                "speed": 62.5,
                "rbe": 104,
                "immune_to": [],
                "children_list": [],
            },
        ],
    }
    _write(data_root / "bloons.json", bloons_payload)
    monkeypatch.setattr(mod, "_DATA_ROOT", data_root)
    monkeypatch.setattr(mod, "_dump_version", lambda _dump: "55.9")
    report = mod.overlay_bloons(dump, dry_run=False)
    assert report == {}  # values already correct — a pure verification run
    payload = json.loads((data_root / "bloons.json").read_text())
    assert payload["game_version"] == "55.9"

    # No derivable version → stamp untouched.
    _write(data_root / "bloons.json", bloons_payload)
    monkeypatch.setattr(mod, "_dump_version", lambda _dump: "")
    mod.overlay_bloons(dump, dry_run=False)
    payload = json.loads((data_root / "bloons.json").read_text())
    assert payload["game_version"] == "55.0"


def test_map_monkey_knowledge_uses_category_folder(mod, tmp_path):
    dump = tmp_path / "dump"
    _write(
        dump / "Knowledge" / "Magic" / "AcidStability.json",
        {
            "name": "AcidStability",
            "category": 2,
            "monkeyMoneyCost": 250,
            "investmentRequired": 8,
            "prerequisiteIds": ["SomePrereq"],
            "mod": {
                "mutatorMods": [
                    {"$type": _t("AcidPoolModModel"), "additionalTime": 5.0},
                ],
                "name": "AcidStability",
            },
        },
    )
    _write(
        dump / "textTable.json",
        {
            "AcidStability": "Acid Stability",
            "AcidStabilityDescription": "Acid lasts longer.",
        },
    )
    rows, warnings = mod.map_monkey_knowledge(dump, "55.1")
    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == "acid_stability"
    assert row["canonical"] == "Acid Stability"
    assert row["category"] == "Magic"  # from the folder, not the opaque int
    assert row["description"] == "Acid lasts longer."
    assert row["monkey_money_cost"] == 250
    assert row["investment_required"] == 8
    assert row["prerequisites"] == ["some_prereq"]
    # AcidStability's effect (AcidPool additionalTime 5) decodes into a factor.
    assert row["effect"] == {"factors": [{"kind": "acid_pool", "additional_time": 5}]}


def _mk_mod(*mutators: dict) -> dict:
    """A KnowledgeModel ``mod`` wrapping the given mutator models."""
    return {"mutatorMods": [dict(m) for m in mutators], "name": "X"}


def test_mk_effect_decodes_scalar_magnitude_and_drops_identity_noise(mod):
    # More Cash: StartingCashModModel addition 200 is the real magnitude;
    # changeBase 0.0 (additive identity) is dropped, multiplier 1.0 kept (non-zero).
    raw = {
        "mod": _mk_mod(
            {
                "$type": _t("StartingCashModModel"),
                "changeBase": 0.0,
                "addition": 200.0,
                "multiplier": 1.0,
                "name": "MoreCash",
            },
        ),
    }
    assert mod._mk_effect(raw) == {
        "factors": [{"kind": "starting_cash", "addition": 200, "multiplier": 1}],
    }


def test_mk_effect_multiple_mutators_become_multiple_factors(mod):
    # Charged Chinooks stacks two mutators (Lives + Cash) → two factors.
    raw = {
        "mod": _mk_mod(
            {"$type": _t("LivesModModel"), "percentBonus": 0.25},
            {
                "$type": _t("CashModModel"),
                "percentBonus": 0.25,
                "bonusMultiplierBuff": 0.0,
            },
        ),
    }
    assert mod._mk_effect(raw) == {
        "factors": [
            {"kind": "lives", "percent_bonus": 0.25},
            {"kind": "cash", "percent_bonus": 0.25},  # bonusMultiplierBuff 0 dropped
        ],
    }


def test_mk_effect_keeps_targets_drops_internal_noise_and_charge_sentinel(mod):
    # Free-tower / discount mutators: string targets + a small charge count are
    # real; the unlimited-charge sentinel + pairing/priority hints are dropped.
    raw = {
        "mod": _mk_mod(
            {
                "$type": _t("FreeTowerModModel"),
                "baseTowerID": "DartMonkey",
                "charges": 1,
                "mutuallyExclusiveWith": "GlueGunner",
                "priority": -1,
                "name": "BonusMonkey",
            },
            {
                "$type": _t("SimTowerDiscountModModel"),
                "tower": "BananaFarm",
                "useAllHeroes": False,
                "multiplier": 0.0,
                "subtraction": 100.0,
                "charges": 9999999,
            },
        ),
    }
    assert mod._mk_effect(raw) == {
        "factors": [
            {"kind": "free_tower", "base_tower_id": "DartMonkey", "charges": 1},
            {
                "kind": "sim_tower_discount",
                "tower": "BananaFarm",
                "use_all_heroes": False,
                "subtraction": 100,
            },
        ],
    }


def test_mk_effect_behavioural_or_empty_stays_description_only(mod):
    # A mutator whose only payload is a nested sub-model (a projectile/ability —
    # Cold Front, Tiny Tornadoes) carries no scalar magnitude → no factor.
    nested = {
        "mod": _mk_mod(
            {"$type": _t("ColdFrontModModel"), "freeze": {"$type": "X", "layers": 4}},
        ),
    }
    assert mod._mk_effect(nested) == {}
    # No mutators at all (Grand Prix Spree) → description-only.
    assert mod._mk_effect({"mod": _mk_mod()}) == {}
    assert mod._mk_effect({}) == {}


def test_map_bosses_reads_roster_tiers_and_derives_immunity(mod, tmp_path):
    dump = tmp_path / "dump"
    # Boss roster lives in Bosses/ (the BossData names the family + its LocsKey);
    # per-tier combat stats come from Bloons/<Family>/<Family>{1..5}.json.
    _write(dump / "Bosses" / "Dreadbloon.json", {"id": 3, "LocsKey": "Dreadbloon"})
    _write(
        dump / "Bloons" / "Dreadbloon" / "Dreadbloon1.json",
        {"id": "Dreadbloon1", "maxHealth": 7500, "speed": 1.25, "bloonProperties": 1},
    )
    _write(
        dump / "Bloons" / "Dreadbloon" / "Dreadbloon2.json",
        {"id": "Dreadbloon2", "maxHealth": 25000, "speed": 1.3, "bloonProperties": 1},
    )
    _write(
        dump / "textTable.json",
        {
            "Dreadbloon": "Dreadbloon",
            "DreadbloonTagLine": "From Deep Within the Dark Earth...",
            "DreadbloonTagLine2": "the Armored Behemoth!",
            "DreadbloonInfoPanelDescription": "• Dreadbloon has Lead properties.\n• Tough.",
        },
    )
    rows, warnings = mod.map_bosses(dump, "55.1")
    assert warnings == []
    assert len(rows) == 1
    boss = rows[0]
    assert boss["id"] == "dreadbloon"
    assert boss["canonical"] == "Dreadbloon"
    assert (
        boss["tagline"] == "From Deep Within the Dark Earth... — the Armored Behemoth!"
    )
    # Bullets + newlines collapse into one readable grounded line.
    assert boss["description"] == "Dreadbloon has Lead properties. Tough."
    # bloonProperties bit 1 (Lead) → the Lead immunity set, via the shared inverter.
    assert boss["immune_to"] == ["Cold", "Energy", "Sharp", "Shatter"]
    assert boss["tiers"] == [
        {"tier": 1, "health": 7500, "speed": 1.25},
        {"tier": 2, "health": 25000, "speed": 1.3},
    ]


def test_map_bosses_skips_boss_with_no_tier_models(mod, tmp_path):
    dump = tmp_path / "dump"
    _write(dump / "Bosses" / "Ghost.json", {"LocsKey": "Ghost"})
    _write(dump / "textTable.json", {"Ghost": "Ghost"})
    rows, warnings = mod.map_bosses(dump, "55.1")
    assert rows == []
    assert any("no tier models" in w for w in warnings)


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


# --- maps (synthetic Maps/<Difficulty>/<Name>.json on tmp_path) --------------


def test_snake_and_decamel(mod):
    assert mod._snake("MushroomGrotto") == "mushroom_grotto"
    assert mod._snake("#Ouch!") == "ouch"
    assert mod._snake("Logs") == "logs"
    assert mod._decamel("CastleRevenge") == "Castle Revenge"
    assert mod._decamel("HighFinance") == "High Finance"


def _map_details(
    *,
    difficulty: int,
    has_water: bool,
    debug: bool = False,
    is_standard: bool = True,
) -> dict:
    return {
        "$type": "Il2Cpp….MapDetails, Assembly-CSharp",
        "difficulty": difficulty,
        "hasWater": has_water,
        "theme": 0,
        "isDebug": debug,
        "IsStandard": is_standard,
    }


def _make_maps_dump(tmp_path: Path) -> Path:
    dump = tmp_path / "dump"
    (dump / "Towers").mkdir(
        parents=True
    )  # map_maps doesn't need it, but be dump-shaped
    _write(
        dump / "Maps" / "Beginner" / "Logs.json",
        _map_details(difficulty=0, has_water=True),
    )
    _write(
        dump / "Maps" / "Advanced" / "MushroomGrotto.json",
        _map_details(difficulty=2, has_water=False),
    )
    _write(
        dump / "Maps" / "Expert" / "DebugMap.json",
        _map_details(difficulty=3, has_water=False, debug=True),
    )
    # Browser-only / editor / dev map (IsStandard=False) — must be filtered too,
    # like the real Blons / Base Editor Map / Protect the Yacht.
    _write(
        dump / "Maps" / "Expert" / "Blons.json",
        _map_details(difficulty=3, has_water=False, is_standard=False),
    )
    (dump / "Maps" / "Intermediate").mkdir(parents=True)  # present but empty
    _write(
        dump / "textTable.json", {"MushroomGrotto": "Mushroom Grotto", "Logs": "Logs"}
    )
    return dump


def test_map_maps_extracts_difficulty_water_and_names(mod, tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_existing_maps", dict)  # isolate from committed prose
    dump = _make_maps_dump(tmp_path)
    rows, warnings = mod.map_maps(dump, "55.0")
    assert warnings == []
    by_id = {r["id"]: r for r in rows}
    # debug map AND non-standard (browser-only/dev) map filtered out
    assert "debug_map" not in by_id and "blons" not in by_id
    assert len(rows) == 2
    assert by_id["logs"]["difficulty"] == "Beginner"
    assert by_id["logs"]["has_water"] is True
    assert "naval" in by_id["logs"]["lines_of_sight_notes"].lower()
    # difficulty comes from the folder; display name from textTable
    assert by_id["mushroom_grotto"]["difficulty"] == "Advanced"
    assert by_id["mushroom_grotto"]["canonical"] == "Mushroom Grotto"
    assert by_id["mushroom_grotto"]["has_water"] is False
    assert "no water" in by_id["mushroom_grotto"]["lines_of_sight_notes"].lower()


def test_map_maps_preserves_curated_prose(mod, tmp_path, monkeypatch):
    dump = _make_maps_dump(tmp_path)
    # Pretend a curated row already exists for logs with hand-written prose.
    monkeypatch.setattr(
        mod,
        "_existing_maps",
        lambda: {
            "logs": {
                "id": "logs",
                "description": "Single river-and-logs track.",
                "lines_of_sight_notes": "Open central area.",
                "aliases": ["log"],
            }
        },
    )
    rows, _ = mod.map_maps(dump, "55.0")
    logs = next(r for r in rows if r["id"] == "logs")
    assert logs["description"] == "Single river-and-logs track."  # curated kept
    assert logs["aliases"] == ["log"]
    assert logs["difficulty"] == "Beginner"  # but difficulty still from the dump


# --- zones (first decode slice) ---------------------------------------------


def test_zones_decode_slow_and_radius(mod):
    # Mirrors Ice Monkey's Arctic Wind in the v55 dump (slow to 60% speed, r=25).
    model = _tower_model()
    model["behaviors"].append(
        {
            "$type": _t("SlowBloonsZoneModel"),
            "name": "SlowBloonsZoneModel",
            "speedScale": 0.6,
            "zoneRadius": 25.0,
            "bloonTag": "Moabs",
        }
    )
    tier = mod._map_tier(model)
    assert tier["zones"] == [
        {
            # name is the dump's internal label (no curated "Arctic Wind" exists)
            "kind": "SlowBloonsZone",
            "name": "SlowBloonsZoneModel",
            "speedScale": 0.6,
            "zoneRadius": 25,
            "bloonTag": "Moabs",
        }
    ]


def test_zones_absent_when_no_zone_models(mod):
    # A plain attacker has no zones[] key at all (not an empty list).
    assert "zones" not in mod._map_tier(_tower_model())


# --- buffs (first decode slice — confirmed types only) ----------------------


def test_buffs_rate_support_maps_to_rate_multiplier(mod):
    # Mirrors Sniper 0-5-x Elite Defender: raw multiplier 0.75 == wiki rateMultiplier.
    model = _tower_model()
    model["behaviors"].append(
        {
            "$type": _t("RateSupportModel"),
            "name": "RateSupportModel_Support_",
            "buffLocsName": "EliteSniperBuff",
            "multiplier": 0.75,
            "isGlobal": True,
        }
    )
    tier = mod._map_tier(model)
    assert tier["buffs"] == [
        {
            "kind": "RateSupport",
            "name": "EliteSniperBuff",  # internal id, never a curated label
            "rateMultiplier": 0.75,
            "isGlobal": True,
        }
    ]


def test_buffs_poplust_maps_percent_increase_fields(mod):
    model = _tower_model()
    model["behaviors"].append(
        {
            "$type": _t("PoplustSupportModel"),
            "name": "",
            "buffLocsName": "PoplustBuff",
            "ratePercentIncrease": 0.15,
            "piercePercentIncrease": 0.15,
        }
    )
    buffs = mod._map_tier(model)["buffs"]
    assert buffs == [
        {
            "kind": "PoplustSupport",
            "name": "PoplustBuff",
            "ratePercentage": 0.15,
            "piercePercentage": 0.15,
        }
    ]


def test_unconfirmed_buff_types_emit_nothing(mod):
    # MonkeyFanClubModel is deferred (not yet confirmed vs wiki) → no guess.
    # (PierceSupportModel, the old example here, was confirmed at the Q-0067
    # cutover via Village Primary Training prose and now emits.)
    model = _tower_model()
    model["behaviors"].append(
        {"$type": _t("MonkeyFanClubModel"), "damage": 3.0, "buffLocsName": "X"}
    )
    assert "buffs" not in mod._map_tier(model)


def test_buffs_subcommander_maps_three_fields(mod):
    # Sub 0-0-5 Sub Commander: raw 4/0/2 == wiki pierceAdditive/damageAdditive/damageMultiplier.
    model = _tower_model()
    model["behaviors"].append(
        {
            "$type": _t("SubCommanderSupportModel"),
            "buffLocsName": "SubCommanderBuff",
            "pierceIncrease": 4,
            "damageIncrease": 0,
            "damageScale": 2.0,
            "isGlobal": False,
        }
    )
    buff = mod._map_tier(model)["buffs"][0]
    assert buff["pierceAdditive"] == 4
    assert buff["damageAdditive"] == 0
    assert buff["damageMultiplier"] == 2


def test_buffs_pierce_percentage_maps_to_pierce_multiplier(mod):
    # Mermonkey: raw percentIncrease 1.4 == wiki pierceMultiplier 1.4.
    model = _tower_model()
    model["behaviors"].append(
        {
            "$type": _t("PiercePercentageSupportModel"),
            "buffLocsName": "BuffMermonkeyPierce",
            "percentIncrease": 1.4,
        }
    )
    assert mod._map_tier(model)["buffs"][0]["pierceMultiplier"] == 1.4


def test_buffs_trade_empire_cash_and_damage(mod):
    # Buccaneer 0-0-5 Trade Empire: cash-per-round + flat damage additives.
    model = _tower_model()
    model["behaviors"].append(
        {
            "$type": _t("TradeEmpireBuffModel"),
            "buffLocsName": "TradeEmpireBuff",
            "cashPerRoundPerMechantship": 10.0,
            "cashPerRoundPerFavouredTrades": 20.0,
            "damageBuff": 1,
            "ceramicDamageBuff": 1,
            "moabDamageBuff": 1,
        }
    )
    buff = mod._map_tier(model)["buffs"][0]
    assert buff["cashPerRoundPerMechantship"] == 10
    assert buff["cashPerRoundPerFavouredTrades"] == 20
    assert buff["damageAdditive"] == 1
    assert buff["damageAdditiveForCeramic"] == 1
    assert buff["damageAdditiveForMoabs"] == 1


def test_buffs_start_of_round_rate(mod):
    # Engineer/Spike start-of-round buff: modifier 0.25 -> rateMultiplier; the
    # ``duration`` is a ROUND count (durationFrames is 0), so it maps to
    # ``duration_rounds`` (not ``lifespan``, which stays seconds-only) and the
    # buff is stamped with its ``start_of_round`` trigger.
    model = _tower_model()
    model["behaviors"].append(
        {
            "$type": _t("StartOfRoundRateBuffModel"),
            "modifier": 0.25,
            "duration": 3.0,
            "Duration": 3.0,
            "durationFrames": 0,
        }
    )
    buff = mod._map_tier(model)["buffs"][0]
    assert buff["rateMultiplier"] == 0.25
    assert buff["duration_rounds"] == 3
    assert buff["trigger"] == "start_of_round"
    assert "lifespan" not in buff  # rounds, never mislabelled as a seconds window


def test_buffs_vigilante_lives_lost(mod):
    # Desperado bottom-path lives-lost buff: frame windows -> seconds (÷60), the
    # two 1:1 effects, the ×2 cash-on-leak, and the on_life_lost trigger that
    # marks the durations as seconds. De-orphans a buff the parser used to drop.
    model = _tower_model()
    model["behaviors"].append(
        {
            "$type": _t("VigilanteTowerBehaviorModel"),
            "buffLocsName": "BuffIconVigilante",
            "loseLifeAttackSpeedBuff": 0.6,
            "loseLifeRangeBuff": 16.0,
            "loseLifeBuffDurationFrames": 900,
            "loseLifeBuffCooldownFrames": 3600,
            "bloonLeakValueModifier": 2.0,
        }
    )
    buff = mod._map_tier(model)["buffs"][0]
    assert buff["trigger"] == "on_life_lost"
    assert buff["rateMultiplier"] == 0.6
    assert buff["rangeAdditive"] == 16
    assert buff["cashOnLeakMultiplier"] == 2
    assert buff["lifespan"] == 15  # 900 frames / 60
    assert buff["cooldown"] == 60  # 3600 frames / 60


def test_buffs_placement_area_range_passthrough(mod):
    model = _tower_model()
    model["behaviors"].append(
        {"$type": _t("PlacementAreaTypeRangeBuffModel"), "rangeMultiplier": 1.35}
    )
    assert mod._map_tier(model)["buffs"][0]["rangeMultiplier"] == 1.35


def test_zones_moab_shove_renames_push_caps(mod):
    # Heli "MOAB Shove": the dump's *PushSpeedScaleCap → committed multiplierFor*
    # (verified exact vs the committed zone). DDT has no dump field → not emitted.
    model = _tower_model()
    model["behaviors"].append(
        {
            "$type": _t("MoabShoveZoneModel"),
            "name": "MoabShoveZoneModel",
            "range": 42,
            "moabPushSpeedScaleCap": -0.51,
            "bfbPushSpeedScaleCap": -0.11,
            "zomgPushSpeedScaleCap": 0.09,
        }
    )
    zone = mod._map_tier(model)["zones"][0]
    assert zone["multiplierForMoab"] == -0.51
    assert zone["multiplierForBfb"] == -0.11
    assert zone["multiplierForZomg"] == 0.09
    assert "multiplierForDdt" not in zone  # dump has no DDT field — never fabricate


def test_buffs_prince_of_darkness_distance_is_lifespan_multiplier(mod):
    # The committed wiki data maps distanceMultiplier -> lifespanMultiplier
    # (Undead buff 1.5), so it is the correct field, not a coincidence.
    model = _tower_model()
    model["behaviors"].append(
        {
            "$type": _t("PrinceOfDarknessZombieBuffModel"),
            "damageIncrease": 3.0,
            "distanceMultiplier": 1.5,
        }
    )
    buff = mod._map_tier(model)["buffs"][0]
    assert buff["damageAdditive"] == 3
    assert buff["lifespanMultiplier"] == 1.5


def test_buffs_shinobi_tactics_maps_multiplier_to_rate(mod):
    # Ninja "Shinobi Tactics" (0-3-0+): the dedicated model is not *SupportModel/
    # *BuffModel-suffixed, so earlier discovery missed it. Raw multiplier 0.92 ==
    # committed wiki rateMultiplier 0.92. The model has no pierce field, so only
    # the confirmed rate is written (the committed +8% pierce is a separate model).
    model = _tower_model()
    model["behaviors"].append(
        {
            "$type": _t("SupportShinobiTacticsModel"),
            "name": "SupportShinobiTacticsModel_Support_",
            "buffLocsName": "ShinobiTacticsBuff",
            "multiplier": 0.92,
            "maxStackSize": 20,
        }
    )
    # The stack cap is a faithful structural passthrough (like isGlobal), so the
    # game-native cutover reproduces the renderer's "(stacks up to 20)" clause.
    assert mod._map_tier(model)["buffs"] == [
        {
            "kind": "SupportShinobiTactics",
            "name": "ShinobiTacticsBuff",
            "rateMultiplier": 0.92,
            "maxStackSize": 20,
        }
    ]


def test_buffs_emit_stack_cap_both_field_names(mod):
    # Two dump field names encode the stack cap: ``maxStacks`` (most towers) and
    # ``maxStackSize`` (Sniper/Ninja/Mermonkey). Each is passed through verbatim
    # so the renderer's ``_stack_cap`` reproduces "(stacks up to N)" at cutover.
    model = _tower_model()
    model["behaviors"].append(
        {
            "$type": _t("TradeEmpireBuffModel"),
            "name": "TradeEmpireBuff",
            "maxStacks": 20,
            "cashPerRoundPerMechantship": 200,
        }
    )
    buff = mod._map_tier(model)["buffs"][0]
    assert buff["maxStacks"] == 20


def test_buffs_stack_cap_zero_preserved(mod):
    # ``0`` ("applies once, does not stack") is a real dump value and must be
    # preserved faithfully; the renderer (``_stack_cap``) is what suppresses the
    # clause for a non-positive cap, not the parser.
    model = _tower_model()
    model["behaviors"].append(
        {
            "$type": _t("RateSupportModel"),
            "name": "RateBuff",
            "multiplier": 0.75,
            "maxStackSize": 0,
        }
    )
    buff = mod._map_tier(model)["buffs"][0]
    assert buff["maxStackSize"] == 0


def test_buffs_damage_modifier_support_reads_nested_tag_bonus(mod):
    # Mortar Pop-and-Awe (0-4-0+): the additive bonus lives in the *nested*
    # damageModifierModel as the misspelled ``damageAddative`` (1.0 vs tag Bad ==
    # committed damageAdditiveForBad 1); ``damageMultiplier`` 1.0 is the decoy.
    model = _tower_model()
    model["behaviors"].append(
        {
            "$type": _t("DamageModifierSupportModel"),
            "mutatorId": "PopAndAweSupport",
            "isGlobal": True,
            "damageModifierModel": {
                "$type": _t("DamageModifierForTagModel"),
                "tag": "Bad",
                "damageMultiplier": 1.0,
                "damageAddative": 1.0,
            },
        }
    )
    assert mod._map_tier(model)["buffs"] == [
        {
            "kind": "DamageModifierSupport",
            "name": "PopAndAweSupport",
            "damageAdditiveForBad": 1,
            "isGlobal": True,
        }
    ]


def test_buffs_damage_modifier_support_drops_unmapped_tag(mod):
    # An unmapped tag yields no number → drop the entry, never emit a bare buff.
    model = _tower_model()
    model["behaviors"].append(
        {
            "$type": _t("DamageModifierSupportModel"),
            "mutatorId": "X",
            "damageModifierModel": {"tag": "Lead", "damageAddative": 2.0},
        }
    )
    assert "buffs" not in mod._map_tier(model)


# --- ABR rounds + income sets (game-native ingestion) -------------------------


def test_intify_whole_dollars_to_int(mod):
    assert mod._intify(121.0) == 121 and isinstance(mod._intify(121.0), int)
    assert mod._intify(1400.2) == 1400.2


def test_bloon_label_prefixes_modifiers(mod):
    names = {"lead": "Lead", "moab": "MOAB"}
    assert mod._bloon_label("lead", ["camo"], names) == "Camo Lead"
    assert mod._bloon_label("moab", ["fortified"], names) == "Fortified MOAB"
    assert (
        mod._bloon_label("lead", ["regrow", "camo", "fortified"], names)
        == "Fortified Camo Regrow Lead"
    )


def _write_income_set(root: Path, thresholds, final) -> None:
    (root / "IncomeSets").mkdir(parents=True, exist_ok=True)
    (root / "IncomeSets" / "DefaultIncomeSet.json").write_text(
        json.dumps(
            {
                "thresholds": [
                    {"threshold": t, "multiplier": m} for t, m in thresholds
                ],
                "finalMultiplier": final,
                "name": "DefaultIncomeSet",
            }
        ),
        "utf-8",
    )


def test_income_bands_sorted_and_cash_per_pop_band_selection(mod, tmp_path):
    _write_income_set(tmp_path, [(60, 0.5), (50, 1.0)], 0.02)  # unsorted on disk
    bands, final = mod._income_bands(tmp_path)
    assert bands == [(50, 1.0), (60, 0.5)] and final == 0.02
    assert mod._cash_per_pop(50, bands, final) == 1.0  # inclusive threshold
    assert mod._cash_per_pop(51, bands, final) == 0.5
    assert mod._cash_per_pop(61, bands, final) == 0.02  # past last band -> final


def test_build_abr_rounds_synthetic_dump(mod, tmp_path, monkeypatch):
    # 3-round synthetic AlternateRoundSet: frames -> seconds, id decomposition,
    # the unplayed r1-2 null cumulative, and the r3 Hard-start baseline.
    _write_income_set(tmp_path, [(50, 1.0)], 0.02)
    rounds_dir = tmp_path / "Rounds" / "AlternateRoundSet"
    rounds_dir.mkdir(parents=True)
    rows = {
        1: [{"bloon": "Blue", "start": 0.0, "end": 1050.75, "count": 10}],
        2: [],  # the empty-groups shape (DefaultSkipEveryOddRound has these)
        3: [{"bloon": "MoabFortified", "start": 60.0, "end": 120.0, "count": 1}],
    }
    for n, groups in rows.items():
        (rounds_dir / f"{n}.json").write_text(
            json.dumps({"groups": groups, "emissions": [], "name": ""}),
            "utf-8",
        )
    monkeypatch.setattr(mod, "_ABR_ROUND_COUNT", 3)
    monkeypatch.setattr(mod, "_dump_version", lambda dump: "55.1")
    payload = mod.build_abr_rounds(tmp_path)

    assert payload["game_version"] == "55.1"
    assert "AlternateRoundSet" in payload["source"]
    r1, r2, r3 = payload["rounds"]
    assert r1["groups"] == [
        {
            "bloon_id": "blue",
            "count": 10,
            "start": 0.0,
            "duration": 17.51,  # 1050.75 frames / 60
            "modifiers": [],
        },
    ]
    assert r1["cumulative_cash"] is None and r2["cumulative_cash"] is None
    assert r2["groups"] == [] and r2["rbe"] == 0
    assert r3["groups"][0]["bloon_id"] == "moab"
    assert r3["groups"][0]["modifiers"] == ["fortified"]
    assert r3["groups"][0]["start"] == 1.0 and r3["groups"][0]["duration"] == 1.0
    assert r3["roundset"] == "alternate"
    # Cumulative baselines at round 3 with the $650 Hard start.
    assert r3["cumulative_cash"] == mod._intify(
        round(mod._ABR_STARTING_CASH + r3["cash"], 2)
    )
    # Fortified MOAB pulls the fortified RBE from committed bloons.json.
    assert r3["rbe"] == 856


# --- subtower mechanism tail + zone inclusive + new buff maps (2026-06-09) ----


def _spawn_tm(name: str, **extra) -> dict:
    node = {"$type": _t("TowerModel"), "name": name, "behaviors": []}
    node.update(extra)
    return node


def test_morph_secondary_tower_model_emits_subtower(mod):
    # Alchemist Total Transformation: towerModel is null, the morphed form
    # lives in secondaryTowerModel (no named-reference morph exists in v55.1).
    spawn = {
        "$type": _t("MorphTowerModel"),
        "towerModel": None,
        "secondaryTowerModel": _spawn_tm("TransformedBaseMonkey", range=72.0),
        "name": "MorphTowerModel_TransformingTonic",
    }
    model = _spawn_tm("Alchemist", behaviors=[spawn])
    subs = mod._subtowers(model)
    assert [s["name"] for s in subs] == ["TransformedBaseMonkey"]
    assert subs[0]["range"] == 72.0


def test_beast_handler_leash_emits_both_beasts(mod):
    # Dual-path Beast Handler: the leash carries two embedded beasts at once.
    spawn = {
        "$type": _t("BeastHandlerLeashModel"),
        "towerModel": _spawn_tm("Microraptor"),
        "towerModelSecond": _spawn_tm("Gyrfalcon"),
    }
    model = _spawn_tm("BeastHandler", behaviors=[spawn])
    assert [s["name"] for s in mod._subtowers(model)] == ["Microraptor", "Gyrfalcon"]


def test_comanche_trance_and_tower_create_spawns_collected(mod):
    model = _spawn_tm(
        "X",
        behaviors=[
            {
                "$type": _t("ComancheDefenceModel"),
                "towerModel": _spawn_tm("ComancheDefenceHeli"),
            },
            {"$type": _t("TranceTotemSpawnerModel"), "tower": _spawn_tm("TranceTotem")},
            {
                "$type": _t("TowerCreateTowerModel"),
                "towerModel": _spawn_tm("PermaPhoenix"),
            },
        ],
    )
    assert [s["name"] for s in mod._subtowers(model)] == [
        "ComancheDefenceHeli",
        "TranceTotem",
        "PermaPhoenix",
    ]


def test_subtower_lifespan_falls_back_to_embedded_expire_model(mod):
    # Marine/Lava Phoenix: the spawn has no (or a zero) towerLifetime — the
    # window lives on the embedded model's own TowerExpireModel.
    nested = _spawn_tm("Marine")
    nested["behaviors"] = [{"$type": _t("TowerExpireModel"), "lifespan": 30.0}]
    spawn = {"$type": _t("CreateTowerModel"), "tower": nested, "towerLifetime": 0.0}
    subs = mod._subtowers(_spawn_tm("Heli", behaviors=[spawn]))
    assert subs[0]["lifespan"] == 30.0
    # A real spawn-side lifetime still wins (Phoenix 20s stays spawn-sourced).
    timed = {
        "$type": _t("CreateTowerModel"),
        "tower": _spawn_tm("P"),
        "towerLifetime": 20.0,
    }
    assert mod._subtowers(_spawn_tm("W", behaviors=[timed]))[0]["lifespan"] == 20.0


def test_nested_subtower_spawns_stay_unclaimed(mod):
    # A minion's own spawn is not the parent's minion: the walker must not
    # descend into any declared nested-model field (incl. secondaryTowerModel).
    inner_spawn = {"$type": _t("CreateTowerModel"), "tower": _spawn_tm("InnerMinion")}
    morphed = _spawn_tm("Morphed", behaviors=[inner_spawn])
    spawn = {
        "$type": _t("MorphTowerModel"),
        "towerModel": None,
        "secondaryTowerModel": morphed,
    }
    subs = mod._subtowers(_spawn_tm("Outer", behaviors=[spawn]))
    assert [s["name"] for s in subs] == ["Morphed"]


def test_subtower_air_unit_attacks_emitted(mod):
    # Mini-Comanche: the Ballistic Missile lives under AttackAirUnitModel.
    nested = _spawn_tm("ComancheDefenceHeli")
    nested["behaviors"] = [
        {
            "$type": _t("AttackAirUnitModel"),
            "name": "AttackAirUnitModel_BallisticMissile_",
            "weapons": [
                {
                    "$type": _t("WeaponModel"),
                    "rate": 3.0,
                    "projectile": {
                        "$type": _t("ProjectileModel"),
                        "name": "Explosion",
                        "behaviors": [
                            {"$type": _t("DamageModel"), "damage": 4.0},
                        ],
                    },
                },
            ],
        },
    ]
    spawn = {"$type": _t("ComancheDefenceModel"), "towerModel": nested}
    subs = mod._subtowers(_spawn_tm("HeliPilot", behaviors=[spawn]))
    attacks = subs[0]["attacks"]
    assert len(attacks) == 1 and attacks[0]["rate"] == 3.0


def test_zone_inclusive_flag_captured_with_tag(mod):
    # Obyn's totem: two SlowBloonsZones both tagged Moabs — one inclusive
    # (MOABs), one exclusive (everything else). Dropping the flag inverts one.
    model = _spawn_tm(
        "Totem",
        behaviors=[
            {
                "$type": _t("SlowBloonsZoneModel"),
                "name": "SlowBloonsZoneModel_NonMoabs",
                "speedScale": 0.6,
                "zoneRadius": 32.0,
                "bloonTag": "Moabs",
                "inclusive": False,
            },
            {
                "$type": _t("SlowBloonsZoneModel"),
                "name": "SlowBloonsZoneModel_Moabs",
                "speedScale": 0.8,
                "zoneRadius": 32.0,
                "bloonTag": "Moabs",
                "inclusive": True,
            },
        ],
    )
    zones = mod._zones(model)
    assert [(z["bloonTag"], z["inclusive"], z["speedScale"]) for z in zones] == [
        ("Moabs", False, 0.6),
        ("Moabs", True, 0.8),
    ]


def test_buffs_range_support_maps_additive_and_fraction(mod):
    model = _spawn_tm(
        "V",
        behaviors=[
            {
                "$type": _t("RangeSupportModel"),
                "name": "RangeSupportModel_",
                "buffLocsName": "BiggerRadiusBuff",
                "additive": 5.0,
                "multiplier": 0.0,
                "isGlobal": True,
            },
        ],
    )
    (buff,) = mod._buffs(model)
    assert buff["rangeAdditive"] == 5.0
    assert buff["rangePercentage"] == 0.0  # the zero cross-checks the mapping
    assert buff["isGlobal"] is True


def test_buffs_projectile_radius_and_bank_income(mod):
    model = _spawn_tm(
        "H",
        behaviors=[
            {
                "$type": _t("ProjectileRadiusSupportModel"),
                "name": "x",
                "buffLocsName": "",
                "mutatorId": "StrikerJonesProjectileRadiusBuff",
                "multiplier": 1.1,
            },
            {
                "$type": _t("BananaCashIncreaseSupportModel"),
                "name": "y",
                "buffLocsName": "BuffIconBenjamin",
                "multiplier": 0.05,
                "isGlobal": True,
            },
        ],
    )
    radius, bank = mod._buffs(model)
    assert radius["radiusMultiplier"] == 1.1
    assert radius["name"] == "StrikerJonesProjectileRadiusBuff"
    assert bank["incomePercentage"] == 0.05


def test_buffs_projectile_speed_fraction(mod):
    # Q-0069 (owner-confirmed): Village Primary Training's 0.25 = +25%.
    model = _spawn_tm(
        "Village",
        behaviors=[
            {
                "$type": _t("ProjectileSpeedSupportModel"),
                "name": "z",
                "buffLocsName": "PrimaryTrainingBuff",
                "multiplier": 0.25,
                "isGlobal": False,
            },
        ],
    )
    (buff,) = mod._buffs(model)
    assert buff["projectileSpeedPercentage"] == 0.25


# --- towers cutover (Q-0066/Q-0067/Q-0068) -----------------------------------


def test_emission_spawned_projectiles_collected(mod):
    # Prince of Darkness reanimates BFBs from weapon.emission.alternateProjectile
    # (damage 100, committed-confirmed) — a spawn location the old walker missed.
    model = _tower_model()
    model["behaviors"][0]["weapons"][0]["emission"] = {
        "$type": _t("EmissionModel"),
        "alternateProjectile": _projectile(name="ProjectileBfb", damage=100.0),
    }
    tier = mod._map_tier(model)
    names = [p["name"] for p in tier["attacks"][0]["projectiles"]]
    assert "ProjectileBfb" in names


def test_effect_name_prefers_semantic_markers(mod):
    # A stun is a SlowModel with multiplier 0 — the game stamps the semantics
    # on overlayType / mutationId; the class name alone would mislabel it.
    assert mod._effect_name({"overlayType": "Stun", "name": ""}) == "Stun"
    assert mod._effect_name({"mutationId": "Stun:Strong", "name": ""}) == "Stun"
    assert (
        mod._effect_name({"$type": _t("SlowModel"), "name": "SlowModel_Glue_"})
        == "Glue"
    )


def test_visual_only_effects_are_not_emitted(mod):
    # A CreateEffectOn… node with no semantic marker and no model name is a
    # purely visual spawn — emitting its class name would leak an internal
    # string into the Pro view.
    proj = _projectile()
    proj["behaviors"].append(
        {"$type": _t("CreateEffectOnExpireModel"), "lifespan": 0.5, "name": ""}
    )
    proj["behaviors"].append(
        {
            "$type": _t("SlowModel"),
            "overlayType": "Stun",
            "lifespan": 2.0,
            "name": "",
        }
    )
    cleaned = mod._clean_projectile(proj)
    assert [e["name"] for e in cleaned["effects"]] == ["Stun"]


def test_buff_flag_types_emit_presence_flags(mod):
    # Village Radar Scanner (camo grant) / MIB (all damage types): the model's
    # presence is the effect — prose-pinned, no number to mis-map.
    model = _tower_model()
    model["behaviors"] += [
        {"$type": _t("VisibilitySupportModel"), "buffLocsName": "RadarScannerBuff"},
        {"$type": _t("DamageTypeSupportModel"), "buffLocsName": "MibBuff"},
    ]
    buffs = mod._map_tier(model)["buffs"]
    assert buffs[0]["grantsCamoDetection"] is True
    assert buffs[1]["grantsAllDamageTypes"] is True


def test_income_aura_buffs_decode_as_true_multipliers(mod):
    # Q-0067: Central Market x1.1 (+10% prose), Banana Central x1.25,
    # Monkey City incomeModifier 1.2 — true multipliers, never fractions.
    model = _tower_model()
    model["behaviors"] += [
        {
            "$type": _t("CentralMarketBuffModel"),
            "multiplier": 1.1,
            "maxStackSize": 10,
            "isGlobalRange": True,
            "buffLocsName": "CentralMarketBuff",
        },
        {"$type": _t("BananaCentralBuffModel"), "multiplier": 1.25},
        {"$type": _t("MonkeyCityIncomeSupportModel"), "incomeModifier": 1.2},
    ]
    buffs = mod._map_tier(model)["buffs"]
    assert [b.get("incomeMultiplier") for b in buffs] == [1.1, 1.25, 1.2]
    # isGlobalRange spells the shared global flag — normalised to isGlobal.
    assert buffs[0]["isGlobal"] is True and buffs[0]["maxStackSize"] == 10


def test_nominal_attack_suppression_keeps_damaging_attacks(mod, tmp_path):
    # Q-0067: Farm/Village nominal AttackModels (banana spawner, empty
    # SharedAttack) are suppressed; a damaging attack (Village 5-x-x Mega
    # Ballista) stays.
    dump = tmp_path / "dump"
    tdir = dump / "Towers" / "MonkeyVillage"
    tdir.mkdir(parents=True)
    base = _tower_model(attacks=[_attack(_projectile(damage=None))])
    (tdir / "MonkeyVillage.json").write_text(json.dumps(base))
    ballista = _tower_model(attacks=[_attack(_projectile(damage=10.0))])
    (tdir / "MonkeyVillage-500.json").write_text(json.dumps(ballista))
    res = mod.map_tower(dump, "monkey_village", "MonkeyVillage", "55.1")
    assert res.payload["tiers"]["000"]["attacks"] == []
    assert res.payload["tiers"]["500"]["attacks"][0]["projectiles"][0]["damage"] == 10


def test_cutover_renames_and_drops_internal_effect_names(mod):
    payload = {
        "tiers": {
            "030": {
                "zones": [
                    {"kind": "SlowBloonsZone", "name": "SlowBloonsZoneModel"},
                    {"kind": "BountyHunterZone", "name": "Desperado-040"},
                ],
                "subtowers": [{"name": "KeepMe"}],
            },
        },
    }
    report = mod._apply_name_policy(payload, "ice_monkey")
    zones = payload["tiers"]["030"]["zones"]
    assert zones[0]["name"] == "Arctic Wind"
    assert "name" not in zones[1]  # unmapped internal id stripped
    assert payload["tiers"]["030"]["subtowers"][0]["name"] == "KeepMe"
    assert report


def test_cutover_rename_disambiguates_by_kind(mod):
    # Mermonkey's totem stamps two different effects with one internal id.
    payload = {
        "tiers": {
            "004": {
                "buffs": [
                    {"kind": "RangeSupport", "name": "NaturesClarityBuff"},
                    {
                        "kind": "AbilityCooldownScaleSupport",
                        "name": "NaturesClarityBuff",
                    },
                ],
            },
        },
    }
    mod._apply_name_policy(payload, "mermonkey")
    names = [b["name"] for b in payload["tiers"]["004"]["buffs"]]
    assert names == ["Range buff", "Ability cooldown buff"]


def test_cutover_preserves_paragon_keys_costs_and_curated_fields(mod):
    payload = {
        "tower_id": "heli_pilot",
        "upgrades": [{"path": 1, "tier": 4, "name": "Operation: X"}],
        "tiers": {
            "003": {
                "zones": [
                    {
                        "kind": "MoabShoveZone",
                        "name": "MoabShoveZoneModel",
                        "multiplierForMoab": -0.3,
                        "multiplierForZomg": 0.75,
                    },
                ],
            },
        },
    }
    committed = {
        "paragon_cost": 1000,
        "paragon_name": "X Paragon",
        "upgrades": [
            {"path": 1, "tier": 4, "name": "Operation: X", "cost": 3300, "xp": 8000},
        ],
        "tiers": {
            "003": {
                "zones": [
                    {
                        "name": "MOAB Shove",
                        "radius": 42,
                        "multiplierForMoab": -0.3,
                        "multiplierForDdt": 0.75,
                    },
                ],
            },
        },
    }
    mod.cutover_payload(payload, committed, "heli_pilot")
    assert payload["paragon_cost"] == 1000 and payload["paragon_name"] == "X Paragon"
    card = payload["upgrades"][0]
    assert card["cost"] == 3300 and card["xp"] == 8000
    zone = payload["tiers"]["003"]["zones"][0]
    # curated name restored + absent curated scalars transplanted (DDT mirror,
    # radius) without touching mapped values.
    assert zone["name"] == "MOAB Shove"
    assert zone["multiplierForDdt"] == 0.75 and zone["radius"] == 42
    assert zone["multiplierForMoab"] == -0.3


def test_cutover_restores_committed_upgrade_names(mod):
    # The dump's upgrade ids are internal for several towers
    # ("Buccaneer-Faster Shooting"); curated names are the resolver vocabulary.
    payload = {
        "tower_id": "monkey_buccaneer",
        "upgrades": [
            {"path": 1, "tier": 1, "name": "Buccaneer-Faster Shooting", "cost": 350},
        ],
        "tiers": {},
    }
    committed = {
        "upgrades": [{"path": 1, "tier": 1, "name": "Faster Shooting", "cost": 350}],
        "tiers": {},
    }
    mod.cutover_payload(payload, committed, "monkey_buccaneer")
    assert payload["upgrades"][0]["name"] == "Faster Shooting"


def test_cutover_carryforward_reinjects_undecodable_entries(mod, monkeypatch):
    # The table is EMPTY since the 2026-06-10 decode pass (every #649 entry is
    # now mapper-decoded) — the machinery stays as the safety valve for any
    # future dump shape the walkers can't reach, so pin it via a patched table.
    assert mod._CUTOVER_CARRYFORWARD == {}
    monkeypatch.setattr(
        mod,
        "_CUTOVER_CARRYFORWARD",
        {"druid": frozenset({("zones", "Thorn zone (close)")})},
    )
    payload = {"tower_id": "druid", "tiers": {"050": {}}, "upgrades": []}
    committed = {
        "tiers": {
            "050": {
                "zones": [
                    {"name": "Thorn zone (close)", "damage": 1},
                    {"name": "Thorn zone (middle)", "damage": 1},
                ],
            },
        },
        "upgrades": [],
    }
    with pytest.raises(mod.NameDowngradeError):
        # Re-injection covers only the listed entry; the unlisted middle zone
        # is genuinely lost and the guard must say so loudly.
        mod.cutover_payload(payload, committed, "druid")
    names = [z["name"] for z in payload["tiers"]["050"]["zones"]]
    assert names == ["Thorn zone (close)"]


def test_cutover_guard_raises_on_lost_curated_name(mod):
    payload = {"tower_id": "ninja_monkey", "tiers": {"030": {"buffs": []}}}
    committed = {
        "tiers": {"030": {"buffs": [{"name": "Some Curated Buff"}]}},
    }
    with pytest.raises(mod.NameDowngradeError):
        mod.cutover_payload(payload, committed, "ninja_monkey")


def test_cutover_guard_allows_owner_approved_retirements(mod):
    # Q-0068: "Beast" retires in favour of the per-tier game names.
    payload = {"tower_id": "beast_handler", "tiers": {"100": {"subtowers": []}}}
    committed = {"tiers": {"100": {"subtowers": [{"name": "Beast"}]}}}
    mod.cutover_payload(payload, committed, "beast_handler")  # no raise


def test_beast_subtowers_adopt_per_tier_upgrade_names(mod):
    # Q-0068: the leash model keeps the base internal name at every tier; the
    # per-tier names are the path's upgrade names.
    payload = {
        "tower_id": "beast_handler",
        "upgrades": [
            {"path": 1, "tier": 3, "name": "Great White"},
            {"path": 2, "tier": 2, "name": "Adasaurus"},
        ],
        "tiers": {
            "320": {
                "subtowers": [{"name": "Piranha"}, {"name": "Microraptor"}],
            },
        },
    }
    mod.cutover_payload(payload, None, "beast_handler")
    names = [s["name"] for s in payload["tiers"]["320"]["subtowers"]]
    assert names == ["Great White", "Adasaurus"]


def test_upgrades_for_synthesizes_colon_id_cards(mod, tmp_path):
    # "Operation: Dart Storm" has no Upgrades/<id>.json (':' is
    # Windows-illegal, the exporter skipped it) — identity comes from the
    # state-file reference + textTable; cost/xp stay for the merge to fill.
    dump = tmp_path / "dump"
    tdir = dump / "Towers" / "MonkeyAce"
    tdir.mkdir(parents=True)
    (dump / "textTable.json").write_text(
        json.dumps(
            {
                "Operation: Dart Storm": "Operation: Dart Storm",
                "Operation: Dart Storm Description": "Shoots 16 darts per volley.",
            }
        )
    )
    state = _tower_model()
    state["upgrades"] = [
        {"tower": "MonkeyAce-400", "upgrade": "Operation: Dart Storm"},
    ]
    (tdir / "MonkeyAce-300.json").write_text(json.dumps(state))
    cards = mod._upgrades_for(tdir, dump)
    (card,) = cards
    assert card["path"] == 1 and card["tier"] == 4
    assert card["name"] == "Operation: Dart Storm"
    assert card["description"] == "Shoots 16 darts per volley."
    assert "cost" not in card


# --- the 2026-06-10 carry-forward decode pass (former _CUTOVER_CARRYFORWARD) -


def test_thorn_zones_decoded_from_spirit_of_the_forest(mod):
    # Druid x5x: three DamageOverTimeZone rings nested on the SotF model,
    # verified field-identical vs committed on all five tiers. Field shape
    # mirrors the real Druid-050 (additive vs the Ceramic+Moabs tag pair).
    def ring(mutator, damage, additive, ibp):
        return {
            "$type": _t("DamageOverTimeZoneModel"),
            "mutatorId": mutator,
            "behaviorModel": {
                "$type": _t("DamageOverTimeCustomModel"),
                "bloonTagsList": ["Ceramic", "Moabs"],
                "additive": additive,
                "damage": damage,
                "immuneBloonProperties": ibp,
                "interval": 0.5,
                "initialDelay": 0.0,
                "distributeToChildren": True,
            },
        }

    sotf = {
        "$type": _t("SpiritOfTheForestModel"),
        "closeRange": 50.0,
        "middleRange": 100.0,
        "damageOverTimeZoneModelClose": ring("SpiritOfTheForestClose", 1.0, 14.0, 17),
        "damageOverTimeZoneModelMiddle": ring("SpiritOfTheForestMedium", 1.0, 4.0, 17),
        "damageOverTimeZoneModelFar": ring("SpiritOfTheForestFar", 2.0, 8.0, 17),
    }
    zones = mod._zones({"behaviors": [sotf]})
    assert [z["name"] for z in zones] == [
        "SpiritOfTheForestFar",
        "SpiritOfTheForestMedium",
        "SpiritOfTheForestClose",
    ]
    far, middle, close = zones
    assert far["damage"] == 2 and "radius" not in far
    assert middle["damageModifierForCeramicOrMoabs"] == 4 and middle["radius"] == 100
    assert close["damageModifierForCeramicOrMoabs"] == 14 and close["radius"] == 50
    for z in zones:
        assert z["damage_type"] == "Sharp"
        assert z["cannot_pop"] == "Cannot damage Lead or frozen"
        assert z["immuneBloonProperties"] == 17
        assert z["interval"] == 0.5 and z["initialDelay"] == 0
        assert z["distributeToChildren"] is True

    # An unmapped tag set must never invent the CeramicOrMoabs field, and the
    # path-1 crosspaths' ibp 0 reads Normal / pops-anything.
    other = ring("SpiritOfTheForestFar", 2.0, 8.0, 0)
    other["behaviorModel"]["bloonTagsList"] = ["Fortified"]
    zones = mod._zones(
        {"behaviors": [{**sotf, "damageOverTimeZoneModelFar": other}]},
    )
    assert "damageModifierForCeramicOrMoabs" not in zones[0]
    assert zones[0]["damage_type"] == "Normal"


def test_cashback_zone_decodes_as_buff_not_zone(mod):
    # Bucc x-x-4 Favored Trades: a *ZoneModel in the dump, a buff in the
    # committed schema. The zone walker must skip it (no value-less husk).
    cashback = {
        "$type": _t("CashbackZoneModel"),
        "cashbackZoneMultiplier": 0.04,
        "cashbackMaxPercent": 0.95,
        "maxStacks": 3,
        "maxStackSize": 3,
        "buffLocsName": "BuffIconBuccaneerxx4",
        "isGlobalRange": False,
    }
    model = {"behaviors": [cashback]}
    assert mod._zones(model) == []
    (buff,) = mod._buffs(model)
    assert buff["name"] == "BuffIconBuccaneerxx4"
    assert buff["cashbackZoneMultiplier"] == 0.04
    assert buff["cashbackMaxPercent"] == 0.95
    assert buff["maxStacks"] == 3 and buff["isGlobal"] is False


def test_submerge_buffs_neutral_filtered_and_split(mod):
    # Sub 3xx: all-neutral SubmergeModel emits nothing.
    neutral = {
        "$type": _t("SubmergeModel"),
        "abilityCooldownSpeedScale": 1.0,
        "abilityCooldownSpeedScaleGlobal": 1.0,
        "abilityCooldownSpeedScaleParagon": 0.0,
        "heroXpScale": 1.0,
    }
    assert mod._buffs({"behaviors": [neutral]}) == []

    # Sub 5xx: local + global (with hero XP); names are the stable synthetic
    # ids the curated rename table maps to the committed labels.
    energizer = dict(
        neutral,
        abilityCooldownSpeedScale=1.2,
        abilityCooldownSpeedScaleGlobal=1.2,
        heroXpScale=1.5,
    )
    local, global_ = mod._buffs({"behaviors": [energizer]})
    assert local["name"] == "SubmergeSupport"
    assert local["abilityCooldownMultiplier"] == 1.2 and local["isGlobal"] is False
    assert global_["name"] == "SubmergeSupportGlobal"
    assert global_["isGlobal"] is True and global_["heroXpMultiplier"] == 1.5

    # The paragon: + the paragon-only scale and the nested support model,
    # whose *Bonus* fields are additive (+1 == committed totals) while
    # rate/xp are direct.
    paragon = dict(
        neutral,
        abilityCooldownSpeedScale=1.3,
        abilityCooldownSpeedScaleGlobal=1.2,
        abilityCooldownSpeedScaleParagon=1.1,
        monkeySubParagonSupportModel={
            "$type": _t("MonkeySubParagonSupportModel"),
            "subBonusDamageMultiplier": 6.0,
            "subBonusPierceMultiplier": 2.0,
            "heroBonusDamageMultiplier": 5.0,
            "heroBonusPierceMultiplier": 2.0,
            "heroRateMultiplier": 1.3,
            "heroXpMultiplier": 5.0,
            "isGlobal": False,
        },
    )
    buffs = {b["name"]: b for b in mod._buffs({"behaviors": [paragon]})}
    assert buffs["SubmergeSupportParagon"]["abilityCooldownMultiplier"] == 1.1
    assert buffs["SubmergeSupportParagon"]["filterOutNonParagon"] is True
    sub = buffs["MonkeySubParagonSupportSub"]
    assert sub["damageMultiplier"] == 7 and sub["pierceMultiplier"] == 3
    hero = buffs["MonkeySubParagonSupportHero"]
    assert hero["damageMultiplier"] == 6 and hero["pierceMultiplier"] == 3
    assert hero["rateMultiplier"] == 1.3 and hero["heroXpMultiplier"] == 5


def test_striker_rate_support_models_decode(mod):
    explosive = {
        "$type": _t("RateSupportExplosiveModel"),
        "multiplier": 0.9,
        "buffLocsName": "ArtilleryCommanderBuff",
        "isGlobal": True,
        "maxStackSize": 0,
    }
    bomb_expert = {
        "$type": _t("RateSupportBombExpertModel"),
        "rangeMultiplier": 0.05,
        "pierceMultiplier": 0.25,
        "buffLocsName": "",
        "isGlobal": False,
    }
    speed, bomb = mod._buffs({"behaviors": [explosive, bomb_expert]})
    assert speed["name"] == "ArtilleryCommanderBuff"
    assert speed["rateMultiplier"] == 0.9 and speed["isGlobal"] is True
    # Empty buffLocsName falls back to the type name — the rename table's key.
    assert bomb["name"] == "RateSupportBombExpert"
    # Fractions land on the *Percentage schema family (+5% range, +25% pierce);
    # the dump's Multiplier field names are misleading (a x0.05 range aura is
    # absurd) and rendered as reductions when kept verbatim.
    assert bomb["rangePercentage"] == 0.05 and bomb["piercePercentage"] == 0.25


def test_only_affect_paragon_flag_copied(mod):
    # Bucc paragon ships two number-identical Flagship instances; the flag is
    # the only honest discriminator.
    def flagship(paragon_only):
        return {
            "$type": _t("FlagshipAttackSpeedIncreaseModel"),
            "attackSpeedIncrease": 0.85,
            "isGlobalRange": True,
            "onlyAffectParagon": paragon_only,
        }

    everyone, paragon_only = mod._buffs(
        {"behaviors": [flagship(False), flagship(True)]},
    )
    assert "onlyAffectParagon" not in everyone
    assert paragon_only["onlyAffectParagon"] is True


def test_typed_sentries_decode_from_typed_tower_model(mod):
    # Engineer 4-x-x: four embedded TowerModels on the typed spawner.
    spawn = {
        "$type": _t("CreateTypedTowerModel"),
        "crushingTower": _spawn_tm("SentryCrushing"),
        "boomTower": _spawn_tm("SentryBoom"),
        "coldTower": _spawn_tm("SentryCold"),
        "energyTower": _spawn_tm("SentryEnergy"),
    }
    names = [s["name"] for s in mod._subtowers(_spawn_tm("Eng", behaviors=[spawn]))]
    assert names == ["SentryCrushing", "SentryBoom", "SentryCold", "SentryEnergy"]


def test_paragon_tower_list_variants_dedupe_to_one(mod):
    # Magus' phoenix: five per-degree skins, combat-identical, differing only
    # by name — the dedupe (name-excluded key) keeps the first.
    variants = [_spawn_tm(f"DarkPhoenixV{i}", range=50.0) for i in range(1, 6)]
    spawn = {"$type": _t("TowerCreateParagonTowerModel"), "towerModels": variants}
    subs = mod._subtowers(_spawn_tm("Magus", behaviors=[spawn]))
    assert [s["name"] for s in subs] == ["DarkPhoenixV1"]
    # Distinct combat survives on its own (the colour sentries' case).
    variants[1]["range"] = 70.0
    subs = mod._subtowers(_spawn_tm("Magus", behaviors=[spawn]))
    assert [s["name"] for s in subs] == ["DarkPhoenixV1", "DarkPhoenixV2"]


def test_sequenced_typed_towers_emit_list_and_deduped_child(mod):
    # Engineer paragon: towers[] holds the three colour sentries (distinct
    # rates); each nests a CreateTowerModel deploying an identical child —
    # the child joins the roster once.
    def colour(name, rate):
        tower = _spawn_tm(name, range=70.0)
        child = _spawn_tm("SentryParagonChild", range=50.0)
        tower["behaviors"] = [
            {
                "$type": _t("AttackModel"),
                "weapons": [{"$type": _t("WeaponModel"), "rate": rate}],
            },
            {"$type": _t("CreateTowerModel"), "tower": child},
        ]
        return tower

    spawn = {
        "$type": _t("CreateSequencedTypedTowerCurrentIndexModel"),
        "towers": [colour("SentryParagonGreen", 0.2), colour("SentryParagonRed", 0.05)],
    }
    subs = mod._subtowers(_spawn_tm("EngParagon", behaviors=[spawn]))
    assert [s["name"] for s in subs] == [
        "SentryParagonGreen",
        "SentryParagonRed",
        "SentryParagonChild",
    ]


# --- decode wave 1 (#653) integration tests kept at the merge ---------------


def test_typed_sentry_subtowers_decode(mod):
    # Engineer Sentry Expert: four typed sentries embedded on the spawner
    # projectile's CreateTypedTowerModel.
    def sentry(name):
        return {
            "$type": "Il2CppAssets.Scripts.Models.Towers.TowerModel, Assembly-CSharp",
            "name": name,
            "behaviors": [{"$type": _t("TowerExpireModel"), "lifespan": 25.0}],
        }

    proj = _projectile()
    proj["behaviors"].append(
        {
            "$type": _t("CreateTypedTowerModel"),
            "crushingTower": sentry("SentryCrushing"),
            "boomTower": sentry("SentryBoom"),
            "coldTower": sentry("SentryCold"),
            "energyTower": sentry("SentryEnergy"),
        }
    )
    model = _tower_model(attacks=[_attack(proj)])
    subs = mod._map_tier(model)["subtowers"]
    assert [s["name"] for s in subs] == [
        "SentryCrushing",
        "SentryBoom",
        "SentryCold",
        "SentryEnergy",
    ]
    assert all(s["lifespan"] == 25 for s in subs)


def test_farm_income_extraction(mod, tmp_path):
    # Farm economy lifts off the (suppressed) banana attack's CashModel and
    # the BankModel — prose-pinned fields.
    dump = tmp_path / "dump"
    tdir = dump / "Towers" / "BananaFarm"
    tdir.mkdir(parents=True)
    proj = _projectile(damage=None)
    proj["behaviors"].append(
        {
            "$type": _t("CashModel"),
            "minimum": 45.0,
            "maximum": 45.0,
            "salvage": 0.5,
            "bonusMultiplier": 0.25,
        }
    )
    base = _tower_model(attacks=[_attack(proj)])
    base["behaviors"].append(
        {"$type": _t("BankModel"), "capacity": 7000.0, "interest": 0.15}
    )
    (tdir / "BananaFarm.json").write_text(json.dumps(base))
    res = mod.map_tower(dump, "banana_farm", "BananaFarm", "55.1")
    tier = res.payload["tiers"]["000"]
    assert tier["attacks"] == []  # nominal banana attack suppressed
    assert tier["bananaValue"] == 45
    assert tier["bananaSalvageValue"] == 0.5
    assert tier["bananaBonusMultiplier"] == 0.25
    assert tier["bankCapacity"] == 7000 and tier["bankInterest"] == 0.15
