"""M3A — the fetch service refuses unknown / disabled / no-base-url rows."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_fetch_service as fetch  # noqa: E402
from services import btd6_source_registry  # noqa: E402
from utils.db import btd6_sources as btd6_db  # noqa: E402


@pytest.fixture(autouse=True)
def _stub_registry(monkeypatch):
    rows = {
        "nk_btd6_maps": {
            "source_key": "nk_btd6_maps",
            "enabled": False,
            "base_url": None,
            "trust_tier": 1,
        },
        "nk_btd6_events": {
            "source_key": "nk_btd6_events",
            "enabled": True,
            "base_url": "https://example.test",
            "trust_tier": 1,
        },
        "nk_btd6_disabled_with_url": {
            "source_key": "nk_btd6_disabled_with_url",
            "enabled": False,
            "base_url": "https://example.test",
            "trust_tier": 1,
        },
    }

    async def _by_key(key):
        return rows.get(key)

    monkeypatch.setattr(btd6_db, "get_source_by_key", _by_key)
    yield


async def test_refuses_unknown_source():
    with pytest.raises(fetch.BTD6FetchRefusedError) as info:
        await fetch.fetch("does_not_exist")
    assert info.value.reason == "source_not_registered"


async def test_refuses_disabled_row():
    with pytest.raises(fetch.BTD6FetchRefusedError) as info:
        await fetch.fetch("nk_btd6_disabled_with_url")
    assert info.value.reason == "source_disabled"


async def test_refuses_when_base_url_missing():
    with pytest.raises(fetch.BTD6FetchRefusedError) as info:
        await fetch.fetch("nk_btd6_maps")
    assert info.value.reason in ("source_disabled", "source_missing_base_url")


async def test_circuit_breaker_opens_after_repeated_failures(monkeypatch):
    """M3B — after N consecutive HTTP failures the breaker opens and
    subsequent calls raise ``circuit_breaker_open`` until it resets.
    The HTTP layer is stubbed so the test runs offline."""
    fetch._reset_for_tests()

    async def _failing_get(url, *, timeout):
        raise fetch.BTD6FetchHTTPError("nk_btd6_events", 500, "boom")

    monkeypatch.setattr(fetch, "_http_get", _failing_get)

    for _ in range(5):
        with pytest.raises(fetch.BTD6FetchHTTPError):
            await fetch.fetch("nk_btd6_events")

    with pytest.raises(fetch.BTD6FetchRefusedError) as info:
        await fetch.fetch("nk_btd6_events")
    assert info.value.reason == "circuit_breaker_open"


async def test_successful_fetch_resets_failure_count(monkeypatch):
    fetch._reset_for_tests()

    async def _ok_get(url, *, timeout):
        return "ok", 200

    monkeypatch.setattr(fetch, "_http_get", _ok_get)

    result = await fetch.fetch("nk_btd6_events")
    assert result.status_code == 200
    assert result.raw_body == "ok"
    assert result.raw_body_hash  # sha256 hex string


async def test_resolves_path_params(monkeypatch):
    fetch._reset_for_tests()
    captured: dict = {}

    async def _record_get(url, *, timeout):
        captured["url"] = url
        return "{}", 200

    monkeypatch.setattr(fetch, "_http_get", _record_get)

    # nk_btd6_events has path_template '/btd6/events' so path_params
    # don't change the URL; test the substitution helper directly.
    row = {
        "base_url": "https://example.test",
        "path_template": "/btd6/races/:raceID/leaderboard",
        "full_url": "https://example.test/btd6/races/:raceID/leaderboard",
    }
    assert (
        fetch._resolve_url(row, {"raceID": "abc"})
        == "https://example.test/btd6/races/abc/leaderboard"
    )
