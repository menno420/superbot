"""PR3 — fetch_for_intent is deterministic, joins the registry, and caps.

Per-domain shape and parser behavior live in
``tests/unit/services/parsers/``; this module covers the new read
surface that grounds the AI stage.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_fact_store  # noqa: E402
from utils.db import btd6_sources as btd6_db  # noqa: E402


def _make_row(
    *,
    fact_type: str,
    entity_kind: str,
    entity_key: str,
    trust_tier: int = 1,
    fetched_at: datetime | None = None,
    version: int = 1,
    body_json: dict | None = None,
    source_name: str = "data.ninjakiwi.com",
    source_kind: str = "official_api",
) -> dict:
    return {
        "id": 1,
        "source_id": 100,
        "fact_type": fact_type,
        "entity_kind": entity_kind,
        "entity_key": entity_key,
        "body_json": body_json or {"name": entity_key},
        "game_version": "54.3",
        "fetched_at": fetched_at or datetime.now(timezone.utc),
        "validated_at": None,
        "confidence": 1.0,
        "version": version,
        "source_key": "nk_test",
        "source_name": source_name,
        "trust_tier": trust_tier,
        "source_kind": source_kind,
    }


async def test_empty_queries_short_circuits_without_db():
    called = {"hit": False}

    async def _explode(*args, **kwargs):
        called["hit"] = True
        raise AssertionError("DB should not be touched on empty input")

    # Even if the DB primitive were called, it would explode; this
    # verifies the service short-circuits before that.
    btd6_db_orig = btd6_db.fetch_facts_for_intent
    try:
        btd6_db.fetch_facts_for_intent = _explode  # type: ignore[assignment]
        result = await btd6_fact_store.fetch_for_intent([])
        assert result == []
        assert called["hit"] is False
    finally:
        btd6_db.fetch_facts_for_intent = btd6_db_orig  # type: ignore[assignment]


async def test_returns_rows_preserving_db_order(monkeypatch):
    rows = [
        _make_row(
            fact_type="btd6.map_metadata",
            entity_kind="btd6_map",
            entity_key="EndOfTheRoad",
            trust_tier=1,
        ),
        _make_row(
            fact_type="btd6.map_metadata",
            entity_kind="btd6_map",
            entity_key="Logs",
            trust_tier=1,
        ),
    ]

    async def _stub(_queries, *, overall_limit):
        return rows

    monkeypatch.setattr(btd6_db, "fetch_facts_for_intent", _stub)
    queries = [
        btd6_fact_store.BTD6FactQuery(None, "btd6_map", "EndOfTheRoad"),
        btd6_fact_store.BTD6FactQuery(None, "btd6_map", "Logs"),
    ]
    result = await btd6_fact_store.fetch_for_intent(queries)
    assert [r["entity_key"] for r in result] == ["EndOfTheRoad", "Logs"]


async def test_per_fact_type_cap_prevents_one_endpoint_from_dominating(monkeypatch):
    # 10 leaderboard rows + 1 tower-metadata row. Without capping the
    # tower fact would be the last to arrive; the cap must let it
    # survive even when leaderboard rows came first.
    leaderboard = [
        _make_row(
            fact_type="btd6.race_leaderboard",
            entity_kind="btd6_race_leaderboard_row",
            entity_key=f"R_rank_{i}",
        )
        for i in range(1, 11)
    ]
    tower = _make_row(
        fact_type="btd6.tower_metadata",
        entity_kind="btd6_tower",
        entity_key="dart-monkey",
    )

    async def _stub(_queries, *, overall_limit):
        return leaderboard + [tower]

    monkeypatch.setattr(btd6_db, "fetch_facts_for_intent", _stub)
    queries = [
        btd6_fact_store.BTD6FactQuery(None, "btd6_tower", "dart-monkey"),
    ]
    result = await btd6_fact_store.fetch_for_intent(
        queries,
        per_fact_type_limit=3,
    )
    fact_types = [r["fact_type"] for r in result]
    assert fact_types.count("btd6.race_leaderboard") == 3
    assert "btd6.tower_metadata" in fact_types


async def test_overall_limit_caps_total_rows(monkeypatch):
    rows = [
        _make_row(fact_type=f"btd6.kind_{i}", entity_kind="btd6_x", entity_key=f"e{i}")
        for i in range(30)
    ]

    async def _stub(_queries, *, overall_limit):
        return rows

    monkeypatch.setattr(btd6_db, "fetch_facts_for_intent", _stub)
    result = await btd6_fact_store.fetch_for_intent(
        [btd6_fact_store.BTD6FactQuery(None, "btd6_x", "e1")],
        overall_limit=5,
    )
    assert len(result) == 5


async def test_returned_rows_carry_source_registry_metadata(monkeypatch):
    """Rows must carry source_name / trust_tier / source_kind so the
    context service can render provenance labels."""
    rows = [
        _make_row(
            fact_type="btd6.race_metadata",
            entity_kind="btd6_race",
            entity_key="Reversed_Loop_mpbd7tcu",
            trust_tier=1,
            source_name="data.ninjakiwi.com",
            source_kind="official_api",
        ),
    ]

    async def _stub(_queries, *, overall_limit):
        return rows

    monkeypatch.setattr(btd6_db, "fetch_facts_for_intent", _stub)
    result = await btd6_fact_store.fetch_for_intent(
        [btd6_fact_store.BTD6FactQuery(None, "btd6_race", "Reversed_Loop_mpbd7tcu")],
    )
    row = result[0]
    assert row["source_name"] == "data.ninjakiwi.com"
    assert row["trust_tier"] == 1
    assert row["source_kind"] == "official_api"
    assert row["fetched_at"] is not None


async def test_db_primitive_called_with_overfetch_for_capping_headroom(monkeypatch):
    """overall_limit * 4 reaches the DB so the service can drop
    excess per-fact_type rows and still satisfy overall_limit."""
    captured = {}

    async def _stub(queries, *, overall_limit):
        captured["overall_limit"] = overall_limit
        return []

    monkeypatch.setattr(btd6_db, "fetch_facts_for_intent", _stub)
    await btd6_fact_store.fetch_for_intent(
        [btd6_fact_store.BTD6FactQuery(None, "btd6_x", "e")],
        overall_limit=10,
    )
    assert captured["overall_limit"] == 40


def test_query_dataclass_is_frozen_and_hashable():
    q1 = btd6_fact_store.BTD6FactQuery(None, "btd6_race", "x")
    q2 = btd6_fact_store.BTD6FactQuery(None, "btd6_race", "x")
    # frozen dataclass → equal instances hash identically.
    assert q1 == q2
    assert hash(q1) == hash(q2)
    with pytest.raises(Exception):
        q1.fact_type = "mutated"  # type: ignore[misc]
