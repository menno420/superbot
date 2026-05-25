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
            "source_key": "nk_btd6_maps", "enabled": False,
            "base_url": None, "trust_tier": 1,
        },
        "nk_btd6_events": {
            "source_key": "nk_btd6_events", "enabled": True,
            "base_url": "https://example.test", "trust_tier": 1,
        },
        "nk_btd6_disabled_with_url": {
            "source_key": "nk_btd6_disabled_with_url", "enabled": False,
            "base_url": "https://example.test", "trust_tier": 1,
        },
    }

    async def _by_key(key):
        return rows.get(key)

    monkeypatch.setattr(btd6_db, "get_source_by_key", _by_key)
    yield


async def test_refuses_unknown_source():
    with pytest.raises(fetch.BTD6FetchRefused) as info:
        await fetch.fetch("does_not_exist")
    assert info.value.reason == "source_not_registered"


async def test_refuses_disabled_row():
    with pytest.raises(fetch.BTD6FetchRefused) as info:
        await fetch.fetch("nk_btd6_disabled_with_url")
    assert info.value.reason == "source_disabled"


async def test_refuses_when_base_url_missing():
    with pytest.raises(fetch.BTD6FetchRefused) as info:
        await fetch.fetch("nk_btd6_maps")
    assert info.value.reason in ("source_disabled", "source_missing_base_url")


async def test_seam_refuses_even_for_usable_source_in_m3a():
    """M3A intentionally has no HTTP client — even an enabled row
    raises ``fetcher_unwired_in_m3a``. M3B replaces this seam."""
    with pytest.raises(fetch.BTD6FetchRefused) as info:
        await fetch.fetch("nk_btd6_events")
    assert info.value.reason == "fetcher_unwired_in_m3a"
