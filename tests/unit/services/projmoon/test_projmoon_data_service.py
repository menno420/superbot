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
    assert kinds == ("sinner", "sin", "damage_type", "mechanic", "ego_grade", "status")
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


def test_every_mechanic_has_a_category():
    mechs = data.get_entries("mechanic")
    assert len(mechs) >= 12  # the core combat layer
    for m in mechs:
        assert m.extra.get("category"), f"{m.canonical} missing a category"


def test_core_combat_mechanics_are_present():
    # The mechanics a Project Moon player asked for: clashing, speed, IDs +
    # passives, enemy-stat concepts (stagger / resistance). All must be modeled.
    ids = {m.id for m in data.get_entries("mechanic")}
    for required in (
        "clash",
        "coin",
        "speed",
        "sanity",
        "stagger",
        "damage_resistance",
        "identity",
        "passive",
    ):
        assert required in ids, f"missing core mechanic {required!r}"


def test_mechanics_resolve_by_player_terms():
    # The terms players actually type resolve to the right mechanic.
    assert data.resolve("clashing", kind="mechanic").id == "clash"
    assert data.resolve("ids", kind="mechanic").id == "identity"
    assert data.resolve("support passive", kind="mechanic").id == "passive"
    # cross-kind resolution finds a mechanic too (no other kind owns "stagger").
    assert data.resolve("stagger").id == "stagger"


def test_all_entries_spans_every_kind():
    everything = data.all_entries()
    assert len(everything) == sum(len(data.get_entries(k)) for k in data.entity_kinds())


def test_every_sinner_has_a_literary_origin():
    for sinner in data.get_entries("sinner"):
        origin = sinner.extra.get("literary_origin")
        assert isinstance(origin, dict), f"{sinner.canonical} missing literary_origin"
        assert origin.get("work") and origin.get("author")


def test_sinner_origins_accessor_covers_full_roster():
    origins = data.sinner_origins()
    assert len(origins) == 12
    faust = next(o for o in origins if o.canonical == "Faust")
    assert faust.author == "Johann Wolfgang von Goethe"
    assert "Faust" in faust.work
    # roster order is preserved (Yi Sang is Sinner No. 1).
    assert origins[0].canonical == "Yi Sang"


def test_malformed_literary_origin_is_rejected(tmp_path, monkeypatch):
    bad = tmp_path / "sinners.json"
    bad.write_text(
        '{"data_version":"x","game_version":"x","source":"x",'
        '"entity_kind":"sinner","entries":[{"id":"a","canonical":"A",'
        '"description":"d","literary_origin":{"work":"W"}}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(data, "DATA_ROOT", tmp_path)
    data.reset_cache()
    with pytest.raises(data.LimbusDataValidationError, match="literary_origin"):
        data.get_entries("sinner")
