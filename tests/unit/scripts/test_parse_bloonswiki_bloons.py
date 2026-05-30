"""Tests for btd6_bloons wikitext parsing in ``scripts/parse_bloonswiki.py``."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "parse_bloonswiki.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("parse_bloonswiki_bloons_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_immunity_damage_type_block(mod):
    immune, status = mod.parse_bloon_immunity(
        "[[damage type|Sharp, Shatter, Cold, Energy]]"
    )
    assert immune == ["Sharp", "Shatter", "Cold", "Energy"]
    assert status == []


def test_immunity_capitalised_label(mod):
    immune, _ = mod.parse_bloon_immunity("[[Damage type|Explosion]]")
    assert immune == ["Explosion"]


def test_immunity_bare_list(mod):
    immune, status = mod.parse_bloon_immunity("Energy, Plasma, Acid")
    assert immune == ["Energy", "Plasma", "Acid"]
    assert status == []


def test_immunity_status_tokens(mod):
    immune, status = mod.parse_bloon_immunity("[[Slow]], [[blowback]], [[knockback]]")
    assert immune == []
    assert [s.lower() for s in status] == ["slow", "blowback", "knockback"]


def test_immunity_empty(mod):
    assert mod.parse_bloon_immunity("") == ([], [])


def test_children_simple(mod):
    assert mod.parse_bloon_children("[[Black Bloon (BTD6)|Black Bloon]] ×2") == [
        {"bloon_id": "black", "count": 2, "modifiers": []},
    ]


def test_children_multiple(mod):
    out = mod.parse_bloon_children(
        "[[White Bloon (BTD6)|White Bloon]] ×1, [[Black Bloon (BTD6)|Black Bloon]] ×1",
    )
    assert out == [
        {"bloon_id": "white", "count": 1, "modifiers": []},
        {"bloon_id": "black", "count": 1, "modifiers": []},
    ]


def test_children_with_modifiers(mod):
    out = mod.parse_bloon_children(
        "[[Camo Bloon (BTD6)|Camo]] [[Regrow Bloon (BTD6)|Regrow]] [[Ceramic (BTD6)|Ceramic]] ×4",
    )
    assert out == [{"bloon_id": "ceramic", "count": 4, "modifiers": ["camo", "regrow"]}]


def test_children_unlinked_bloon_name(mod):
    # Glass Bloon: the modifier is linked but the child ("Zebra Bloon") is bare.
    out = mod.parse_bloon_children("[[Regrow Bloon (BTD6)|Regrow]] Zebra Bloon ×1")
    assert out == [{"bloon_id": "zebra", "count": 1, "modifiers": ["regrow"]}]


def test_children_empty(mod):
    assert mod.parse_bloon_children("") == []
