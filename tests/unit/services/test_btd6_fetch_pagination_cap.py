"""M3B — fetcher refuses any page != 1 before touching the network.

Bounded explicit pagination is deferred; PR2 is page-1-only. The guard
fires before any registry lookup or HTTP call so a buggy caller cannot
accidentally crawl race or boss leaderboards.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_fetch_service as fetch  # noqa: E402
from utils.db import btd6_sources as btd6_db  # noqa: E402


@pytest.fixture(autouse=True)
def _stub_registry(monkeypatch):
    """Provide a single enabled row so the test reaches the page check
    only when ``page=1`` and bails at the cap when ``page != 1``."""

    rows = {
        "nk_btd6_races_leaderboard": {
            "source_key": "nk_btd6_races_leaderboard",
            "enabled": True,
            "base_url": "https://example.test",
            "path_template": "/btd6/races/:raceID/leaderboard",
            "full_url": "https://example.test/btd6/races/:raceID/leaderboard",
            "trust_tier": 1,
        },
    }

    async def _by_key(key):
        return rows.get(key)

    monkeypatch.setattr(btd6_db, "get_source_by_key", _by_key)

    async def _ok_get(url, *, timeout):
        return "{}", 200

    monkeypatch.setattr(fetch, "_http_get", _ok_get)
    fetch._reset_for_tests()
    yield


async def test_default_page_is_one_and_succeeds():
    result = await fetch.fetch(
        "nk_btd6_races_leaderboard",
        path_params={"raceID": "abc"},
    )
    assert result.status_code == 200


async def test_explicit_page_one_succeeds():
    result = await fetch.fetch(
        "nk_btd6_races_leaderboard",
        path_params={"raceID": "abc"},
        page=1,
    )
    assert result.status_code == 200


async def test_page_two_raises_paging_cap():
    with pytest.raises(fetch.BTD6FetchRefusedError) as info:
        await fetch.fetch(
            "nk_btd6_races_leaderboard",
            path_params={"raceID": "abc"},
            page=2,
        )
    assert info.value.reason == "paging_cap"
    assert info.value.source_key == "nk_btd6_races_leaderboard"


async def test_negative_or_zero_page_also_raises_paging_cap():
    with pytest.raises(fetch.BTD6FetchRefusedError) as info_neg:
        await fetch.fetch(
            "nk_btd6_races_leaderboard",
            path_params={"raceID": "abc"},
            page=-1,
        )
    assert info_neg.value.reason == "paging_cap"

    with pytest.raises(fetch.BTD6FetchRefusedError) as info_zero:
        await fetch.fetch(
            "nk_btd6_races_leaderboard",
            path_params={"raceID": "abc"},
            page=0,
        )
    assert info_zero.value.reason == "paging_cap"


async def test_page_guard_fires_before_registry_lookup(monkeypatch):
    """The cap must fire before any registry call so a misuse never
    reaches the DB layer or rate limiter."""
    called = {"hit": False}

    async def _explode_on_lookup(_key):
        called["hit"] = True
        raise AssertionError("registry must not be consulted when page!=1")

    monkeypatch.setattr(btd6_db, "get_source_by_key", _explode_on_lookup)

    with pytest.raises(fetch.BTD6FetchRefusedError) as info:
        await fetch.fetch("anything", page=42)
    assert info.value.reason == "paging_cap"
    assert called["hit"] is False
