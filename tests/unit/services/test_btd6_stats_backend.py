"""btd6_stats_service reads the per-entity stats tree through the active
BTD6 data backend (so the stats tree honours ``BTD6_DATA_BACKEND``).

Drives the stats loaders off an injected Postgres provider — no filesystem,
no real DB — proving the stats reads no longer go straight to disk.
"""

from __future__ import annotations

import pytest

from services import btd6_data_service as ds
from services import btd6_stats_service as ss
from services.btd6_data_provider import PostgresRawProvider


def _fetch_all(rows):
    async def fetch():
        return list(rows)

    return fetch


@pytest.fixture(autouse=True)
def _restore():
    original = ds.get_provider()
    ds.reset_cache()
    ss.reset_cache()
    yield
    ds.set_provider(original)
    ds.reset_cache()
    ss.reset_cache()


async def _install(rows):
    provider = PostgresRawProvider(fetch_all=_fetch_all(rows))
    await provider.warm_cache()
    ds.set_provider(provider)
    ds.reset_cache()
    ss.reset_cache()


@pytest.mark.asyncio
async def test_tower_stats_read_from_provider():
    blob = {
        "tower_id": "dart_monkey",
        "canonical": "Dart Monkey",
        "game_version": "47.0",
        "base_cost": 200,
        "category": "primary",
        "upgrades": [],
        "tiers": {},
    }
    await _install([("stats/dart_monkey.json", blob)])

    stats = ss.get_tower_stats("dart_monkey")
    assert stats is not None
    assert stats.canonical == "Dart Monkey"
    assert stats.base_cost == 200
    # A tower with no blob degrades to None (unchanged contract).
    assert ss.get_tower_stats("does_not_exist") is None


@pytest.mark.asyncio
async def test_list_paragon_ids_read_from_provider():
    rows = [
        (
            "stats/paragons/wizard_lord_phoenix.json",
            {"paragon_id": "wizard_lord_phoenix"},
        ),
        (
            "stats/paragons/apex_plasma_master.json",
            {"paragon_id": "apex_plasma_master"},
        ),
        ("stats/dart_monkey.json", {"tower_id": "dart_monkey"}),
        ("towers.json", {"towers": []}),
    ]
    await _install(rows)

    assert ss.list_paragon_ids() == (
        "apex_plasma_master",
        "wizard_lord_phoenix",
    )
