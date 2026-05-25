"""M3A — read-only registry tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_source_registry  # noqa: E402
from utils.db import btd6_sources as btd6_db  # noqa: E402


@pytest.fixture(autouse=True)
def _stub_db(monkeypatch):
    state: dict = {
        "rows": [
            {
                "id": 1, "source_key": "nk_btd6_maps", "source_name": "maps",
                "source_owner": "Ninja Kiwi", "source_kind": "official_api",
                "trust_tier": 1, "base_url": None, "path_template": "/btd6/maps",
                "full_url": None, "cache_policy_key": None, "enabled": False,
                "notes": "",
            },
            {
                "id": 2, "source_key": "nk_btd6_events", "source_name": "events",
                "source_owner": "Ninja Kiwi", "source_kind": "official_api",
                "trust_tier": 1, "base_url": "https://example.test",
                "path_template": "/btd6/events",
                "full_url": "https://example.test/btd6/events",
                "cache_policy_key": None, "enabled": True, "notes": "",
            },
            {
                "id": 3, "source_key": "community_wiki", "source_name": "Wiki",
                "source_owner": "Community", "source_kind": "webpage",
                "trust_tier": 2, "base_url": "https://wiki.test",
                "path_template": "/", "full_url": "https://wiki.test/",
                "cache_policy_key": None, "enabled": False, "notes": "",
            },
        ],
    }

    async def _list(*, trust_tier=None, enabled=None):
        out = list(state["rows"])
        if trust_tier is not None:
            out = [r for r in out if r["trust_tier"] == trust_tier]
        if enabled is not None:
            out = [r for r in out if r["enabled"] == enabled]
        return out

    async def _by_key(key):
        return next((r for r in state["rows"] if r["source_key"] == key), None)

    async def _by_id(rid):
        return next((r for r in state["rows"] if r["id"] == rid), None)

    monkeypatch.setattr(btd6_db, "list_sources", _list)
    monkeypatch.setattr(btd6_db, "get_source_by_key", _by_key)
    monkeypatch.setattr(btd6_db, "get_source", _by_id)
    yield state


async def test_list_enabled_returns_only_enabled():
    rows = await btd6_source_registry.list_enabled_sources()
    keys = {r["source_key"] for r in rows}
    assert keys == {"nk_btd6_events"}


async def test_list_by_tier_filters():
    tier_1 = await btd6_source_registry.list_by_tier(1)
    tier_2 = await btd6_source_registry.list_by_tier(2)
    assert {r["source_key"] for r in tier_1} == {"nk_btd6_maps", "nk_btd6_events"}
    assert {r["source_key"] for r in tier_2} == {"community_wiki"}


async def test_is_source_usable_rejects_missing_base_url():
    usable, reason = await btd6_source_registry.is_source_usable("nk_btd6_maps")
    assert not usable
    assert reason == "source_disabled"


async def test_is_source_usable_rejects_unknown():
    usable, reason = await btd6_source_registry.is_source_usable("nope")
    assert not usable
    assert reason == "source_not_registered"


async def test_is_source_usable_accepts_enabled_with_base_url():
    usable, reason = await btd6_source_registry.is_source_usable("nk_btd6_events")
    assert usable
    assert reason == "ok"
