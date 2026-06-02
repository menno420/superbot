"""Tests for btd6_superlative_service against the real committed cost data.

Pins the cross-roster ranking answers ("most expensive tier-4 upgrade",
"cheapest tower", priciest paragon) the AI now answers from data instead of
disclaiming.
"""

from __future__ import annotations

import pytest

from services import btd6_data_service as ds
from services import btd6_stats_service as ss
from services import btd6_superlative_service as sup


@pytest.fixture(autouse=True)
def _fresh():
    ds.reset_cache()
    ss.reset_cache()
    yield
    ds.reset_cache()
    ss.reset_cache()


def test_most_expensive_tier4_upgrade_is_sun_temple():
    top = sup.rank(sup.UPGRADE_COST, tier=4)
    assert top[0].tower_id == "super_monkey"
    assert top[0].cost == 100000
    assert "tier 4" in top[0].what


def test_most_expensive_tier3_upgrade_is_sun_avatar():
    top = sup.rank(sup.UPGRADE_COST, tier=3)
    assert top[0].tower_id == "super_monkey"
    assert top[0].cost == 20000


def test_cheapest_and_priciest_tower():
    assert sup.rank(sup.TOWER_COST, cheapest=True)[0].tower_id == "dart_monkey"
    assert sup.rank(sup.TOWER_COST)[0].tower_id == "super_monkey"


def test_paragon_ranking_returns_known_costs():
    hits = sup.rank(sup.PARAGON_COST)
    assert hits  # several towers have paragons in the data
    assert all(h.cost > 0 for h in hits)
    assert all("Paragon" in h.what for h in hits)


def test_results_are_ordered_and_capped():
    rows = sup.rank(sup.UPGRADE_COST, limit=3)
    assert len(rows) == 3
    assert rows[0].cost >= rows[1].cost >= rows[2].cost


def test_paragon_dps_ranks_all_paragons_by_total_highest_and_lowest():
    high = sup.rank(sup.PARAGON_DPS, limit=25)
    # Every paragon has a computable total DPS, ranked descending.
    assert len(high) == len(sup.rank(sup.PARAGON_COST, limit=25))
    assert [h.value for h in high] == sorted((h.value for h in high), reverse=True)
    assert high[0].unit == "DPS"
    assert "total of" in high[0].detail and "degree 1" in high[0].detail
    # Total DPS (all attacks): Magus Perfectus' four attacks top it; the
    # single-attack Spike paragon is the floor. (Main-attack-only would have
    # mis-ranked Glaive Dominus first — see the regression this metric fixes.)
    assert high[0].tower_id == "wizard_monkey"
    assert sup.rank(sup.PARAGON_DPS, cheapest=True)[0].tower_id == "spike_factory"


def test_paragon_pierce_differs_from_dps_ranking():
    # A high-pierce paragon that ranks low on single-target DPS must top pierce —
    # proving DPS and pierce are genuinely distinct metrics, not the same sort.
    top_pierce = sup.rank(sup.PARAGON_PIERCE)[0]
    assert top_pierce.unit == "pierce"
    assert top_pierce.tower_id == "ice_monkey"  # Herald of Everfrost, 500 pierce


def test_tower_combat_metrics_use_base_tier_and_have_range():
    rng = sup.rank(sup.TOWER_RANGE)
    assert rng and rng[0].unit == "range"
    assert rng[0].value > 0
    dps = sup.rank(sup.TOWER_DPS, limit=30)
    assert dps and all(h.unit == "DPS" for h in dps)
    assert all("base 0-0-0" in h.detail for h in dps)


def test_unknown_metric_returns_empty():
    assert sup.rank("nonsense") == []
