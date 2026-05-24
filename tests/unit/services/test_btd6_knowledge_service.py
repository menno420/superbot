"""Knowledge-service tests."""

from __future__ import annotations

from services.btd6_knowledge_service import (
    data_version,
    game_version,
    hero_fact,
    list_modes,
    list_rounds,
    map_fact,
    mode_fact,
    round_fact,
    tower_fact,
)


def test_tower_fact_returns_costs_and_paths():
    fact = tower_fact("dart_monkey")
    assert fact is not None
    assert fact.base_cost == 200
    assert "top" in fact.upgrade_paths
    assert len(fact.upgrade_paths["top"]) == 5


def test_unknown_tower_returns_none():
    assert tower_fact("not_a_real_tower") is None


def test_hero_fact_has_abilities():
    quincy = hero_fact("quincy")
    assert quincy is not None
    assert len(quincy.abilities) >= 1


def test_map_fact_includes_difficulty():
    logs = map_fact("logs")
    assert logs is not None
    assert logs.difficulty


def test_mode_fact_chimps_includes_restrictions():
    chimps = mode_fact("chimps")
    assert chimps is not None
    assert any("no income" in r.lower() or "no powers" in r.lower() for r in chimps.restrictions)


def test_round_fact_includes_threats():
    fact = round_fact(63)
    assert fact is not None
    assert "Ceramic" in fact.common_threats or "Camo Lead" in fact.common_threats


def test_version_accessors():
    assert data_version()
    assert game_version()


def test_list_accessors_return_tuples():
    assert isinstance(list_modes(), tuple)
    assert isinstance(list_rounds(), tuple)
