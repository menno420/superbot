"""Tests for the stats-JSON parsing in ``scripts/parse_bloonswiki.py``.

The fixture mirrors the real ``Module:BTD6 stats`` shape (``_order`` containers,
nested projectiles/effects/abilities, crosspath deltas) using real Bomb Shooter
numbers, so it exercises the flatten + damage-type decode + delta-drop paths.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "parse_bloonswiki.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("parse_bloonswiki_stats_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _tier(damage=1, immune=2, pierce=22):
    return {
        "range": 40,
        "footprintRadius": 7,
        "attacks": {
            "_order": ["Attack"],
            "Attack": {
                "rate": 1.5,
                "projectiles": {
                    "_order": ["Projectile", "Explosion"],
                    "Explosion": {
                        "pierce": pierce,
                        "damage": damage,
                        "radius": 12,
                        "immuneBloonProperties": immune,
                    },
                    "Projectile": {"pierce": 1, "speed": 180},
                },
            },
        },
    }


def _raw_json(*, drop: str | None = None) -> str:
    data: dict = {"_" + c: _tier() for c in (
        "000", "100", "200", "300", "400", "500",
        "010", "020", "030", "040", "050",
        "001", "002", "003", "004", "005",
    )}
    data["_last_updated"] = "54.0"
    # Bloon Crush: Normal type (immune 0), heavy damage.
    data["_500"] = _tier(damage=24, immune=0, pierce=80)
    # crosspath delta inside a main tier — must be dropped.
    data["_500"]["_510"] = {"attacks": {"_order": ["Attack"], "Attack": {"rate": 1.125}}}
    # MOAB modifier passes through.
    data["_030"]["attacks"]["Attack"]["projectiles"]["Explosion"]["damageModifierForMoabs"] = 15
    # Stun effect on Bloon Impact.
    data["_400"]["attacks"]["Attack"]["projectiles"]["Explosion"]["effects"] = {
        "_order": ["Stun"],
        "Stun": {"lifespan": 1.4, "multiplier": 0},
    }
    # Bomb Blitz ability with the BAD/non-BAD damage fields.
    data["_005"]["abilities"] = {
        "_order": ["Ability"],
        "Ability": {"cooldown": 60, "damageToBad": 2000, "damageToNonBad": 9999999},
    }
    if drop is not None:
        del data["_" + drop]
    return json.dumps(data)


def test_clean_parse_has_no_warnings(mod):
    result = mod.parse_stats_json(_raw_json())
    assert result.ok, result.warnings
    assert result.game_version == "54.0"
    assert len(result.tiers) == 16


def test_damage_type_decoded(mod):
    result = mod.parse_stats_json(_raw_json())
    base_expl = result.tiers["000"]["attacks"][0]["projectiles"][1]
    assert base_expl["name"] == "Explosion"
    assert base_expl["damage_type"] == "Explosion"
    assert base_expl["cannot_pop"] == "Cannot damage Black"
    # Bloon Crush flips to Normal.
    crush = result.tiers["500"]["attacks"][0]["projectiles"][1]
    assert crush["damage_type"] == "Normal"


def test_order_flattened_to_named_lists(mod):
    result = mod.parse_stats_json(_raw_json())
    attacks = result.tiers["000"]["attacks"]
    assert isinstance(attacks, list)
    projectiles = attacks[0]["projectiles"]
    assert [p["name"] for p in projectiles] == ["Projectile", "Explosion"]


def test_crosspath_deltas_dropped(mod):
    result = mod.parse_stats_json(_raw_json())
    tier = result.tiers["500"]
    assert "_510" not in tier
    assert "510" not in tier


def test_passthrough_fields_and_abilities(mod):
    result = mod.parse_stats_json(_raw_json())
    expl_030 = result.tiers["030"]["attacks"][0]["projectiles"][1]
    assert expl_030["damageModifierForMoabs"] == 15
    ability = result.tiers["005"]["abilities"][0]
    assert ability["damageToBad"] == 2000
    assert ability["damageToNonBad"] == 9999999
    # effect flattened
    stun = result.tiers["400"]["attacks"][0]["projectiles"][1]["effects"][0]
    assert stun["name"] == "Stun" and stun["lifespan"] == 1.4


def test_missing_tier_warns(mod):
    result = mod.parse_stats_json(_raw_json(drop="003"))
    assert any("missing tier 003" in w for w in result.warnings)


def test_malformed_json_raises(mod):
    with pytest.raises(ValueError):
        mod.parse_stats_json("{ not valid json ")
