"""Tests for the Project Moon (Limbus) deterministic data service."""

from __future__ import annotations

import pytest

from services import projmoon_data_service as data


@pytest.fixture(autouse=True)
def _fresh_cache():
    data.reset_cache()
    yield
    data.reset_cache()


def test_all_kinds_load_and_validate():
    kinds = data.entity_kinds()
    assert kinds == ("sinner", "sin", "damage_type", "ego_grade", "status")
    for kind in kinds:
        entries = data.get_entries(kind)
        assert entries, f"no entries for {kind}"
        for e in entries:
            assert e.entity_kind == kind
            assert e.id and e.canonical and e.description


def test_fixed_roster_counts():
    assert len(data.get_entries("sinner")) == 12
    assert len(data.get_entries("sin")) == 7
    assert len(data.get_entries("damage_type")) == 3
    assert len(data.get_entries("ego_grade")) == 5


def test_unknown_kind_raises():
    with pytest.raises(KeyError):
        data.get_entries("nope")


def test_resolve_canonical_and_alias():
    assert data.resolve("Outis").id == "outis"
    assert data.resolve("what does sinking do", kind="status").id == "sinking"
    # alias
    assert data.resolve("rodya").id == "rodion"


def test_resolve_prefers_longest_match():
    # "don" is an alias of Don Quixote; the full phrase must still resolve to it,
    # and the longer canonical wins over the bare alias.
    assert data.resolve("don quixote").id == "don_quixote"


def test_resolve_no_match_returns_none():
    assert data.resolve("definitely not a limbus term") is None
    assert data.resolve("", kind="sin") is None


def test_kind_scoped_resolution_does_not_leak():
    # "Slash" is a damage type; scoping to sinners must not find it.
    assert data.resolve("slash", kind="sinner") is None
    assert data.resolve("slash", kind="damage_type").id == "slash"


def test_extra_fields_preserved():
    wrath = data.resolve("Wrath", kind="sin")
    assert wrath.extra.get("color") == "Red"
    aleph = data.resolve("ALEPH", kind="ego_grade")
    assert aleph.extra.get("rank") == 5


def test_all_entries_spans_every_kind():
    everything = data.all_entries()
    assert len(everything) == sum(len(data.get_entries(k)) for k in data.entity_kinds())
