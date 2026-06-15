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

# The two paragons with no bloonswiki stats module — transcribed from article
# prose instead, so they carry a stats file but are flagged prose-sourced.
_PROSE_SOURCED = {"root_of_all_nature", "herald_of_everfrost"}
_EXPECTED_PARAGONS = 13


@pytest.fixture(autouse=True)
def _fresh():
    svc.reset_cache()
    yield
    svc.reset_cache()


def test_all_thirteen_paragon_files_committed():
    ids = set(svc.list_paragon_ids())
    assert len(ids) == _EXPECTED_PARAGONS
    assert _PROSE_SOURCED <= ids  # the prose-sourced two are present too


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


def test_no_paragon_is_prose_sourced_after_cutover():
    # The two article-prose bases (Herald, Root) were re-sourced from game data
    # at the v55.1 cutover — every paragon now has a module-exact combat base
    # and none carries the lower-fidelity prose flag.
    for pid in _PROSE_SOURCED:
        stats = svc.get_paragon_stats(pid)
        assert stats is not None
        assert stats.has_combat_stats
        assert stats.is_prose_sourced is False
    assert svc.get_paragon_stats_by_tower("druid") is not None
    assert svc.get_paragon_stats_by_tower("ice_monkey") is not None
    assert all(
        svc.get_paragon_stats(pid).is_prose_sourced is False
        for pid in svc.list_paragon_ids()
    )


def test_formerly_prose_sourced_degree_scaling_works():
    # The universal degree scaling applies to the (now game-sourced) base.
    herald = svc.get_paragon_stats("herald_of_everfrost")
    d1, d100 = herald.degree(1), herald.degree(100)
    assert d1.power == 0 and d100.power == 200_000
    assert d1.boss_multiplier == 1.0 and d100.boss_multiplier == 2.25
    # The beam hit: 600 dmg at d1 -> 600*2+10 at d100 (the same value the old
    # prose base carried as "Ice Beam"; the group is the game attack name now).
    dmg100 = next(
        s
        for s in d100.stats
        if s.group == "BeamHitProjectile" and s.label == "Damage"
    )
    assert dmg100.value == 600 * 2 + 10


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


# --- AI grounding (btd6_context_service) ------------------------------------


def test_render_paragon_now_includes_combat_stats():
    from services import btd6_context_service as ctx

    lines = ctx._render_paragon("boomerang_monkey", "Boomerang Monkey")
    joined = "\n".join(lines)
    # Still names the paragon + cost.
    assert "[btd6_paragon]" in joined
    assert "Glaive Dominus" in joined
    # Now also carries degree-1 + degree-100 combat stats.
    assert "[btd6_paragon_stats normal]" in joined
    assert "Degree 1" in joined
    assert "Degree 100" in joined
    assert "×2.25" in joined  # max boss multiplier
    # Primary-attack headline, not the situational MOAB-Press nuke.
    assert "25 dmg" in joined
    assert "60 pierce" in joined


def test_paragon_name_alone_grounds_stats():
    """Naming only the paragon (not its tower) still grounds it — the screenshot
    flow ("what are the stats of Glaive Dominus?").
    """
    from services import btd6_context_service as ctx

    lines = ctx._paragon_name_facts("what are the stats of glaive dominus", set())
    assert any("Glaive Dominus" in line for line in lines)
    assert any("[btd6_paragon_stats normal]" in line for line in lines)


def test_paragon_name_pass_dedupes_resolved_towers():
    from services import btd6_context_service as ctx

    # If the tower is already grounded via intent, the name pass stays silent.
    assert ctx._paragon_name_facts("glaive dominus", {"boomerang_monkey"}) == []


def test_every_paragon_has_a_curated_description():
    for pid in svc.list_paragon_ids():
        stats = svc.get_paragon_stats(pid)
        assert stats is not None
        assert stats.description, pid
        # A real summary, not a stub.
        assert len(stats.description) > 60, pid
        assert "Paragon" in stats.description


def test_description_surfaces_in_grounding():
    from services import btd6_context_service as ctx

    lines = ctx._render_paragon("boomerang_monkey", "Boomerang Monkey")
    assert any("fusing Glaive Lord" in line for line in lines)


def test_render_paragon_labels_game_data_origin():
    from services import btd6_context_service as ctx

    # Druid's paragon base was article-prose before the v55.1 cutover; it is
    # game-sourced now and the provenance label says so.
    lines = ctx._render_paragon("druid", "Druid")
    joined = "\n".join(lines)
    assert "[btd6_paragon]" in joined  # name + cost
    assert "[btd6_paragon_stats normal]" in joined  # now has stats too
    assert "Root of all Nature" in joined
    assert "BTD6 game data" in joined  # provenance label
    assert "article prose" not in joined
