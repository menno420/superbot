"""Tests for paragon stats parsing in ``scripts/parse_bloonswiki.py``.

A paragon ``Module:BTD6 stats/<Paragon>/new`` page is a single flat node (no
crosspath ``_NNN`` keys, no per-level ``_N`` deltas), so the parser just cleans
the root: flatten ``_order`` containers, decode the damage type, drop ``_``-keys.
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
    spec = importlib.util.spec_from_file_location("parse_bloonswiki_paragon_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_RAW = {
    "_last_updated": "53.0",
    "range": 60,
    "placeableOnLand": True,
    "attacks": {
        "_order": ["Attack"],
        "Attack": {
            "rate": 0.04,
            "count": 1,
            "projectiles": {
                "_order": ["Projectile"],
                "Projectile": {
                    "pierce": 60,
                    "maxPierce": 0,
                    "damage": 25,
                    "damageModifierForBoss": 50,
                    "immuneBloonProperties": 0,
                },
            },
        },
    },
    "abilities": {
        "_order": ["Ability"],
        "Ability": {"cooldown": 45},
    },
}


def test_parse_paragon_flattens_to_clean_base(mod):
    result = mod.parse_paragon_stats_json(json.dumps(_RAW))
    assert result.ok
    assert result.game_version == "53.0"
    base = result.base
    # `_order` containers became ordered lists of named children.
    assert [a["name"] for a in base["attacks"]] == ["Attack"]
    proj = base["attacks"][0]["projectiles"][0]
    assert proj["name"] == "Projectile"
    assert proj["pierce"] == 60
    assert proj["damage"] == 25
    # immuneBloonProperties decoded to a readable damage type.
    assert proj["damage_type"] == "Normal"
    assert [a["name"] for a in base["abilities"]] == ["Ability"]
    # `_`-prefixed keys dropped from the cleaned base.
    assert "_last_updated" not in base


def test_parse_paragon_warns_on_non_combat_node(mod):
    result = mod.parse_paragon_stats_json(json.dumps({"_last_updated": "53.0", "range": 5}))
    assert not result.ok
    assert any("no attacks or abilities" in w for w in result.warnings)


def test_parse_paragon_rejects_malformed_json(mod):
    with pytest.raises(ValueError):
        mod.parse_paragon_stats_json("{not json")
