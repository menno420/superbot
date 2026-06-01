"""Paragon combat stats are grounded end-to-end: data file -> stats service ->
degree derivation.

These pin the committed ``stats/paragons/<id>.json`` files (the fetched
degree-INDEPENDENT base nodes) and the service that loads them + derives the
degree-dependent table. Eleven of the thirteen paragons have a bloonswiki stats
module; the two that don't (Root of all Nature, Herald of Everfrost) have no file
and keep cost-only on their tower.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services import btd6_stats_service as svc

_PARAGONS = Path(svc.PARAGON_STATS_ROOT)

# Paragons that genuinely lack a bloonswiki stats module (cost-only).
_MODULE_LESS = {"root_of_all_nature", "herald_of_everfrost"}
_EXPECTED_WITH_MODULE = 11


@pytest.fixture(autouse=True)
def _fresh():
    svc.reset_cache()
    yield
    svc.reset_cache()


def test_eleven_paragon_files_committed():
    ids = svc.list_paragon_ids()
    assert len(ids) == _EXPECTED_WITH_MODULE
    assert not (_MODULE_LESS & set(ids))


def test_every_paragon_file_has_a_combat_base():
    for paragon_id in svc.list_paragon_ids():
        stats = svc.get_paragon_stats(paragon_id)
        assert stats is not None
        assert stats.has_combat_stats, paragon_id
        assert stats.paragon_id == paragon_id
        assert stats.tower_id
        assert stats.cost and stats.cost > 0


def test_filename_matches_internal_paragon_id():
    for path in _PARAGONS.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["paragon_id"] == path.stem


def test_lookup_by_tower_matches_lookup_by_id():
    apex = svc.get_paragon_stats("apex_plasma_master")
    assert apex is not None
    by_tower = svc.get_paragon_stats_by_tower(apex.tower_id)
    assert by_tower is apex


def test_module_less_paragons_have_no_stats():
    assert svc.get_paragon_stats("root_of_all_nature") is None
    assert svc.get_paragon_stats_by_tower("druid") is None
    assert svc.get_paragon_stats_by_tower("ice_monkey") is None


def test_paragon_tower_matches_committed_tower_paragon_name():
    """Each paragon stats file cross-references a real tower whose stats file
    names the same paragon — the two data sources stay consistent.
    """
    for paragon_id in svc.list_paragon_ids():
        pstats = svc.get_paragon_stats(paragon_id)
        assert pstats is not None
        tower = svc.get_tower_stats(pstats.tower_id)
        assert tower is not None
        assert tower.paragon_name, pstats.tower_id
        assert tower.paragon_cost == pstats.cost


def test_glaive_dominus_degree_table_endpoints():
    stats = svc.get_paragon_stats("glaive_dominus")
    assert stats is not None

    d1 = stats.degree(1)
    assert d1.power == 0
    assert d1.boss_multiplier == 1.0
    # Degree 1 reproduces the base node values.
    cd = next(s for s in d1.stats if s.group == "Attack" and s.label == "Cooldown")
    assert cd.value == 0.04
    pierce = next(s for s in d1.stats if s.group == "Projectile" and s.label == "Pierce")
    assert pierce.value == 60

    d100 = stats.degree(100)
    assert d100.power == 200_000
    assert d100.boss_multiplier == 2.25
    pierce100 = next(
        s for s in d100.stats if s.group == "Projectile" and s.label == "Pierce"
    )
    assert pierce100.value == 60 * 2 + 10  # degree-100 special


def test_degree_groups_are_stable_across_degrees():
    stats = svc.get_paragon_stats("glaive_dominus")
    assert stats is not None
    groups = stats.degree_groups()
    assert "Attack" in groups
    assert groups[0] == "Attack"
    # Same groups regardless of the degree the row is built at.
    assert tuple(
        dict.fromkeys(s.group for s in stats.degree(77).stats)
    ) == groups
