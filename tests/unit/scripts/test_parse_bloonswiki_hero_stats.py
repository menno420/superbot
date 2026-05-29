"""Tests for hero per-level stats parsing in ``scripts/parse_bloonswiki.py``.

A hero ``Module:BTD6 stats`` page stores level 1 at the top level and
``_2``..``_20`` as *partial deltas*; the parser must deep-merge each delta
cumulatively onto the running state, then clean each level. The fixture below
exercises that: pierce changes at levels 2 and 10, rate only at 20.
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
    spec = importlib.util.spec_from_file_location("parse_bloonswiki_hero_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _hero_json() -> str:
    """Base (level 1) + partial deltas at 2, 10, 20 — mirrors the real shape."""
    base = {
        "range": 50,
        "attacks": {
            "_order": ["Attack"],
            "Attack": {
                "rate": 0.95,
                "projectiles": {
                    "_order": ["Projectile"],
                    "Projectile": {
                        "damage": 1,
                        "pierce": 3,
                        "immuneBloonProperties": 17,  # Sharp
                    },
                },
            },
        },
    }
    data: dict = dict(base)
    # Partial deltas — note they carry no ``_order`` (base supplies it).
    data["_2"] = {"attacks": {"Attack": {"projectiles": {"Projectile": {"pierce": 4}}}}}
    data["_10"] = {
        "attacks": {"Attack": {"projectiles": {"Projectile": {"pierce": 6}}}}
    }
    data["_20"] = {
        "attacks": {
            "Attack": {"rate": 0.2, "projectiles": {"Projectile": {"pierce": 9}}},
        },
    }
    data["_last_updated"] = "46.3"
    return json.dumps(data)


def _pierce(level_node: dict) -> int:
    return level_node["attacks"][0]["projectiles"][0]["pierce"]


def test_levels_merge_cumulatively(mod):
    result = mod.parse_hero_stats_json(_hero_json())
    assert result.ok, result.warnings
    assert result.game_version == "46.3"
    assert len(result.levels) == 20
    assert _pierce(result.levels["1"]) == 3
    assert _pierce(result.levels["2"]) == 4
    assert _pierce(result.levels["9"]) == 4  # carries the level-2 value
    assert _pierce(result.levels["10"]) == 6
    assert _pierce(result.levels["20"]) == 9


def test_rate_changes_only_at_max_level(mod):
    result = mod.parse_hero_stats_json(_hero_json())
    assert result.levels["1"]["attacks"][0]["rate"] == 0.95
    assert result.levels["19"]["attacks"][0]["rate"] == 0.95
    assert result.levels["20"]["attacks"][0]["rate"] == 0.2


def test_damage_type_decoded_per_level(mod):
    result = mod.parse_hero_stats_json(_hero_json())
    proj = result.levels["1"]["attacks"][0]["projectiles"][0]
    assert proj["damage_type"] == "Sharp"
    assert "Lead" in proj["cannot_pop"]


def test_no_base_stats_warns(mod):
    result = mod.parse_hero_stats_json(json.dumps({"_2": {}, "_last_updated": "1.0"}))
    assert any("no base" in w for w in result.warnings)
    assert result.levels == {}


def test_malformed_json_raises(mod):
    with pytest.raises(ValueError):
        mod.parse_hero_stats_json("{ not valid json ")
