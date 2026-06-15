"""M3B — fetcher refuses URLs with unresolved ``:varName`` placeholders.

Five parameterized endpoint families are exercised so the guard's
behavior is locked across the path-template shapes that PR2 enables:
race metadata, boss metadata, challenge metadata, single map, CT tiles.
The fetcher must NEVER issue an HTTP call to a URL that still carries
``/:varName`` after path_params substitution.
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

# Each row mirrors what migration 040 + 042 produces: an enabled,
# base-URL-having registry entry whose path_template still contains
# placeholders. The full_url field is used by _resolve_url first.
_ROWS = {
    "nk_btd6_races_metadata": {
        "source_key": "nk_btd6_races_metadata",
        "enabled": True,
        "base_url": "https://example.test",
        "path_template": "/btd6/races/:raceID/metadata",
        "full_url": "https://example.test/btd6/races/:raceID/metadata",
        "trust_tier": 1,
    },
    "nk_btd6_bosses_metadata": {
        "source_key": "nk_btd6_bosses_metadata",
        "enabled": True,
        "base_url": "https://example.test",
        "path_template": "/btd6/bosses/:bossID/metadata/:difficulty",
        "full_url": "https://example.test/btd6/bosses/:bossID/metadata/:difficulty",
        "trust_tier": 1,
    },
    "nk_btd6_challenges_one": {
        "source_key": "nk_btd6_challenges_one",
        "enabled": True,
        "base_url": "https://example.test",
        "path_template": "/btd6/challenges/challenge/:challengeID",
        "full_url": "https://example.test/btd6/challenges/challenge/:challengeID",
        "trust_tier": 1,
    },
    "nk_btd6_maps_one": {
        "source_key": "nk_btd6_maps_one",
        "enabled": True,
        "base_url": "https://example.test",
        "path_template": "/btd6/maps/map/:mapID",
        "full_url": "https://example.test/btd6/maps/map/:mapID",
        "trust_tier": 1,
    },
    "nk_btd6_ct_tiles": {
        "source_key": "nk_btd6_ct_tiles",
        "enabled": True,
        "base_url": "https://example.test",
        "path_template": "/btd6/ct/:ctID/tiles",
        "full_url": "https://example.test/btd6/ct/:ctID/tiles",
        "trust_tier": 1,
    },
}


@pytest.fixture(autouse=True)
def _stub_registry(monkeypatch):
    async def _by_key(key):
        return _ROWS.get(key)

    monkeypatch.setattr(btd6_db, "get_source_by_key", _by_key)

    async def _explode_on_http(_url, *, timeout):
        raise AssertionError(
            "fetcher must not issue an HTTP call when path params unresolved",
        )

    monkeypatch.setattr(fetch, "_http_get", _explode_on_http)
    fetch._reset_for_tests()
    yield


@pytest.mark.parametrize(
    "source_key",
    list(_ROWS),
)
async def test_missing_path_param_refuses_before_http(source_key):
    with pytest.raises(fetch.BTD6FetchRefusedError) as info:
        await fetch.fetch(source_key)  # path_params omitted
    assert info.value.reason == "missing_path_param"
    assert info.value.source_key == source_key


async def test_partially_resolved_url_still_refuses():
    # boss metadata needs BOTH bossID and difficulty; passing only one
    # leaves ``:difficulty`` in the URL and must refuse.
    with pytest.raises(fetch.BTD6FetchRefusedError) as info:
        await fetch.fetch(
            "nk_btd6_bosses_metadata",
            path_params={"bossID": "Diamondback5_mpfz8mi4"},
        )
    assert info.value.reason == "missing_path_param"


async def test_fully_resolved_url_passes_path_guard(monkeypatch):
    captured: dict = {}

    async def _record(url, *, timeout):
        captured["url"] = url
        return "{}", 200

    monkeypatch.setattr(fetch, "_http_get", _record)

    result = await fetch.fetch(
        "nk_btd6_bosses_metadata",
        path_params={"bossID": "Diamondback5_mpfz8mi4", "difficulty": "standard"},
    )
    assert result.status_code == 200
    assert ":bossID" not in captured["url"]
    assert ":difficulty" not in captured["url"]
    assert captured["url"].endswith("/Diamondback5_mpfz8mi4/metadata/standard")


async def test_extra_path_param_keys_are_ignored_when_url_is_resolved(monkeypatch):
    """Unknown path_param keys are not an error as long as the URL
    ends up fully resolved (the existing ``_resolve_url`` ignores
    unknown keys by design)."""

    async def _ok(url, *, timeout):
        return "{}", 200

    monkeypatch.setattr(fetch, "_http_get", _ok)

    result = await fetch.fetch(
        "nk_btd6_races_metadata",
        path_params={"raceID": "abc", "unrelated": "ignored"},
    )
    assert result.status_code == 200
