"""Pin the canonical scheduled parent-source policy.

This regression test guards the inputs the admin panel and the
ingestion supervisor BOTH consume. If the parent set or cadence
changes, update this test deliberately.
"""

from __future__ import annotations

import inspect

from services import btd6_ingestion_sources


def test_parent_source_keys_are_pinned():
    keys = btd6_ingestion_sources.parent_source_keys()
    assert keys == (
        "nk_btd6_events",
        "nk_btd6_races",
        "nk_btd6_bosses",
        "nk_btd6_odyssey",
        "nk_btd6_ct",
        "nk_btd6_maps",
        "nk_btd6_challenges",
        "steam_btd6_news",
    )


def test_source_intervals_match_parent_keys():
    intervals = btd6_ingestion_sources.source_intervals()
    assert set(intervals) == set(btd6_ingestion_sources.parent_source_keys())
    # Live rotations every 30 minutes; daily directories every 24h.
    for key in (
        "nk_btd6_events",
        "nk_btd6_races",
        "nk_btd6_bosses",
        "nk_btd6_odyssey",
        "nk_btd6_ct",
    ):
        assert intervals[key] == 1800
    for key in ("nk_btd6_maps", "nk_btd6_challenges"):
        assert intervals[key] == 86400
    # Steam patch-notes feed polls every 6h.
    assert intervals["steam_btd6_news"] == 21600


def test_parent_source_helpers_are_sync():
    # Pure config — not async. Callers in views must not await these.
    assert not inspect.iscoroutinefunction(btd6_ingestion_sources.parent_source_keys)
    assert not inspect.iscoroutinefunction(btd6_ingestion_sources.source_intervals)
