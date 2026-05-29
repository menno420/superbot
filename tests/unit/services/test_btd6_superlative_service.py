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


def test_unknown_metric_returns_empty():
    assert sup.rank("nonsense") == []
