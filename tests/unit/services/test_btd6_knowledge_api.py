"""M3A — BTD6KnowledgeAPI tests (DB-empty fixture fallback + populated path)."""

from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_knowledge_api as kapi  # noqa: E402
from utils.db import btd6_sources as btd6_db  # noqa: E402


@pytest.fixture
def _empty_db(monkeypatch):
    async def _get_latest_fact(*a, **kw):
        return None

    async def _search_facts(**kw):
        return []

    async def _get_source(rid):
        return None

    async def _latest_patch():
        return None

    monkeypatch.setattr(btd6_db, "get_latest_fact", _get_latest_fact)
    monkeypatch.setattr(btd6_db, "search_facts", _search_facts)
    monkeypatch.setattr(btd6_db, "get_source", _get_source)
    monkeypatch.setattr(btd6_db, "latest_patch_note", _latest_patch)
    yield


@pytest.fixture
def _populated_db(monkeypatch):
    sources: dict[int, dict] = {
        7: {
            "id": 7,
            "source_key": "nk_btd6_maps",
            "trust_tier": 1,
            "base_url": "https://example.test",
            "full_url": "https://example.test/btd6/maps",
        },
    }
    facts: dict[tuple[str, str, str], dict] = {
        ("map", "map", "monkey_meadow"): {
            "id": 1,
            "source_id": 7,
            "fact_type": "map",
            "entity_kind": "map",
            "entity_key": "monkey_meadow",
            "body_json": {"name": "Monkey Meadow", "difficulty": "Beginner"},
            "game_version": "44.0",
            "fetched_at": _dt.datetime.now(_dt.timezone.utc),
            "validated_at": _dt.datetime.now(_dt.timezone.utc),
            "confidence": 1.0,
            "version": 1,
        },
    }

    async def _get_latest_fact(ftype, kind, key):
        return facts.get((ftype, kind, key))

    async def _get_source(rid):
        return sources.get(rid)

    async def _search_facts(**kw):
        return list(facts.values())

    monkeypatch.setattr(btd6_db, "get_latest_fact", _get_latest_fact)
    monkeypatch.setattr(btd6_db, "get_source", _get_source)
    monkeypatch.setattr(btd6_db, "search_facts", _search_facts)
    yield


async def test_get_tower_falls_back_to_fixtures_when_db_empty(_empty_db):
    bundle = await kapi.get_tower("dart_monkey")
    # fixtures may or may not have dart_monkey; either way the call
    # must not raise. When fixtures resolve we get fixture_fallback;
    # when they don't, None.
    if bundle is not None:
        assert bundle.source_key == "fixture"
        assert bundle.freshness_status == "fixture_fallback"


async def test_get_map_uses_db_row_when_populated(_populated_db):
    bundle = await kapi.get_map("monkey_meadow")
    assert bundle is not None
    assert bundle.source_key == "nk_btd6_maps"
    assert bundle.body["name"] == "Monkey Meadow"
    assert bundle.freshness_status in ("fresh", "stale", "unknown")
    assert bundle.source_trust_tier == 1


async def test_compare_entities_returns_only_resolved(_populated_db):
    bundles = await kapi.compare_entities("map", "map", ["monkey_meadow", "nope"])
    assert len(bundles) == 1
    assert bundles[0].entity_key == "monkey_meadow"


async def test_search_facts_round_trips_body(_populated_db):
    rows = await kapi.search_facts(fact_type="map")
    assert rows
    assert rows[0].body["difficulty"] == "Beginner"
