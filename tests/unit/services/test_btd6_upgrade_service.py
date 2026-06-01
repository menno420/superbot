"""Deterministic upgrade resolution — upgrades as first-class BTD6 entities.

Pins the reported failures (PMFC / POD / Prince of Darkness / Wizard Lord
Phoenix / path notation), the curated-alias integrity (no typo'd names), and the
no-match / ambiguity behaviour so the resolver can't silently regress.
"""

from __future__ import annotations

import pytest

from services import btd6_upgrade_service as up


@pytest.fixture(autouse=True)
def _fresh():
    up.reset_cache()
    yield
    up.reset_cache()


def test_registry_covers_every_upgrade():
    upgrades = up.all_upgrades()
    # 25 towers x 3 paths x 5 tiers.
    assert len(upgrades) == 375
    ids = {u.upgrade_id for u in upgrades}
    assert len(ids) == 375  # unique
    for u in upgrades:
        assert u.upgrade_id == f"{u.tower_id}:{u.code}"
        assert u.crosspath == "-".join(u.code)
        assert 1 <= u.tier <= 5
        assert u.canonical


def test_every_curated_alias_names_a_real_upgrade():
    # Guards against a typo in the curated alias table.
    for alias, canonical in up._CURATED_ALIASES.items():
        res = up.resolve_upgrade(alias)
        assert res.found, f"{alias!r} -> {canonical!r} did not resolve"
        assert res.upgrade.canonical == canonical


@pytest.mark.parametrize(
    ("query", "expected_id", "expected_type"),
    [
        ("What are PMFC's stats?", "dart_monkey:050", "alias"),
        ("POD cooldown?", "wizard_monkey:005", "alias"),
        ("PoD", "wizard_monkey:005", "alias"),
        ("Prince of Darkness damage", "wizard_monkey:005", "exact_name"),
        ("Wizard Lord Phoenix", "wizard_monkey:050", "exact_name"),
        ("Phoenix Lord", "wizard_monkey:050", "alias"),
        ("Abyss Lord", "mermonkey:500", "alias"),
        ("MAD stats", "dartling_gunner:050", "alias"),
        ("M.A.D", "dartling_gunner:050", "exact_name"),
        ("BEZ", "dartling_gunner:005", "alias"),
        ("Bloon Master Alchemist", "alchemist:005", "exact_name"),
        ("Pop and Awe", "mortar_monkey:050", "exact_name"),
    ],
)
def test_named_and_alias_queries_resolve(query, expected_id, expected_type):
    res = up.resolve_upgrade(query)
    assert res.found, query
    assert res.upgrade.upgrade_id == expected_id
    assert res.match_type == expected_type


@pytest.mark.parametrize(
    ("query", "expected_id"),
    [
        ("005 wizard", "wizard_monkey:005"),
        ("wizard 005", "wizard_monkey:005"),
        ("050 dart", "dart_monkey:050"),
        ("0-0-5 wizard", "wizard_monkey:005"),
        ("dart 500", "dart_monkey:500"),
        ("wizard 003", "wizard_monkey:003"),  # lower tier via notation
    ],
)
def test_path_notation_resolves_with_a_tower(query, expected_id):
    res = up.resolve_upgrade(query)
    assert res.found, query
    assert res.match_type == "path_notation"
    assert res.upgrade.upgrade_id == expected_id


def test_lower_tier_single_word_name_resolves():
    # 'Nomad' is a real Desperado 0-0-2 upgrade — full-tree coverage, not just T5.
    res = up.resolve_upgrade("nomad")
    assert res.found
    assert res.upgrade.upgrade_id == "desperado:002"
    assert res.upgrade.canonical == "Nomad"


def test_ambiguous_query_returns_candidates():
    res = up.resolve_upgrade("wizard lord phoenix vs prince of darkness")
    assert not res.found
    assert res.match_type == "ambiguous"
    ids = {c.upgrade_id for c in res.candidates}
    assert ids == {"wizard_monkey:050", "wizard_monkey:005"}


@pytest.mark.parametrize(
    "query",
    [
        "",
        "   ",
        "005",  # bare code, no tower -> can't disambiguate
        "0-2-5",  # crosspath, not a single upgrade
        "what is the best tower",
        "madness",  # must not match the 'mad' alias
        "supercalifragilistic",
    ],
)
def test_non_matches_return_none(query):
    res = up.resolve_upgrade(query)
    assert not res.found
    assert res.match_type == "none"
    assert res.candidates == ()


def test_get_upgrade_round_trips():
    pod = up.get_upgrade("wizard_monkey:005")
    assert pod is not None
    assert pod.canonical == "Prince of Darkness"
    assert pod.tower_name == "Wizard Monkey"
    assert pod.path == "bot" and pod.path_index == 3 and pod.tier == 5
    assert pod.cost == 26500
    assert "pod" in pod.aliases
    assert up.get_upgrade("does_not:999") is None
