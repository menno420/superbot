"""Tests for round-composition parsing in ``scripts/parse_bloonswiki.py``."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "parse_bloonswiki.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("parse_bloonswiki_rounds_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _rbe_map():
    return {
        "red": {"rbe": 1, "rbe_fortified": None},
        "lead": {"rbe": 23, "rbe_fortified": 26},
        "ceramic": {"rbe": 104, "rbe_fortified": 114},
        "moab": {"rbe": 616, "rbe_fortified": None},
    }


def test_parse_rounds_composition_and_order(mod):
    data = {
        "rounds": [
            [{"bloon": "Red", "count": 20, "start": 0, "duration": 17.5}],
            [
                {"bloon": "Lead", "count": 75, "start": 0, "duration": 42},
                {"bloon": "Ceramic", "count": 40, "start": 3.9, "duration": 0.2},
            ],
        ],
    }
    rounds = mod.parse_rounds_json(data, rbe_map=_rbe_map())
    assert [r["round"] for r in rounds] == [1, 2]
    assert rounds[0]["rbe"] == 20
    second = rounds[1]
    assert [g["bloon_id"] for g in second["groups"]] == [
        "lead",
        "ceramic",
    ]  # order kept
    assert second["rbe"] == 75 * 23 + 40 * 104  # children-inclusive
    assert second["roundset"] == "default"


def test_parse_rounds_modifier_stripping_and_fortified_rbe(mod):
    data = {
        "rounds": [
            [
                {"bloon": "LeadFortifiedCamo", "count": 10, "start": 0, "duration": 1},
                {"bloon": "CeramicRegrow", "count": 5, "start": 0, "duration": 1},
            ],
        ],
    }
    groups = mod.parse_rounds_json(data, rbe_map=_rbe_map())[0]["groups"]
    assert groups[0]["bloon_id"] == "lead"
    assert set(groups[0]["modifiers"]) == {"fortified", "camo"}
    assert groups[1]["bloon_id"] == "ceramic" and groups[1]["modifiers"] == ["regrow"]
    # Fortified lead uses rbe_fortified (26); regrow doesn't change RBE (104).
    assert (
        mod.parse_rounds_json(data, rbe_map=_rbe_map())[0]["rbe"] == 10 * 26 + 5 * 104
    )


def test_parse_rounds_does_not_double_count_children(mod):
    # A single MOAB is its full children-inclusive RBE, not re-expanded.
    data = {"rounds": [[{"bloon": "Moab", "count": 1, "start": 0, "duration": 0.1}]]}
    assert mod.parse_rounds_json(data, rbe_map=_rbe_map())[0]["rbe"] == 616


def test_parse_rounds_danger_tiers(mod):
    data = {
        "rounds": [
            [{"bloon": "Red", "count": 1}],  # rbe 1 -> trivial
            [{"bloon": "Ceramic", "count": 200}],  # 20800 -> very_high
        ],
    }
    rounds = mod.parse_rounds_json(data, rbe_map=_rbe_map())
    assert rounds[0]["danger"] == "trivial"
    assert rounds[1]["danger"] == "very_high"
