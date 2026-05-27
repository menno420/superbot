"""Tests for ``btd6_knowledge_service.fact_summary_by_kind``."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services import btd6_knowledge_service


@pytest.mark.asyncio
async def test_empty_table_returns_empty_tuple(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    async def _empty():
        return []

    monkeypatch.setattr(btd6_db, "aggregate_facts_by_entity_kind", _empty)

    assert await btd6_knowledge_service.fact_summary_by_kind() == ()


@pytest.mark.asyncio
async def test_one_row_per_entity_kind(monkeypatch):
    from utils.db import btd6_sources as btd6_db

    now = datetime.now(tz=timezone.utc)

    async def _agg():
        return [
            {
                "entity_kind": "btd6_event",
                "fact_count": 14,
                "last_fetched_at": now - timedelta(minutes=45),
            },
            {
                "entity_kind": "btd6_map",
                "fact_count": 78,
                "last_fetched_at": now - timedelta(hours=2),
            },
        ]

    monkeypatch.setattr(btd6_db, "aggregate_facts_by_entity_kind", _agg)

    summary = await btd6_knowledge_service.fact_summary_by_kind()
    assert len(summary) == 2
    kinds = {s.entity_kind for s in summary}
    assert kinds == {"btd6_event", "btd6_map"}

    event_row = next(s for s in summary if s.entity_kind == "btd6_event")
    assert event_row.fact_count == 14
    assert event_row.bucket == "fresh"


@pytest.mark.asyncio
async def test_bucket_assignment_uses_public_helper(monkeypatch):
    """fact_summary_by_kind delegates bucketing to bucket_freshness."""
    from utils.db import btd6_sources as btd6_db

    now = datetime.now(tz=timezone.utc)

    async def _agg():
        return [
            {
                "entity_kind": "btd6_race",
                "fact_count": 1,
                "last_fetched_at": now - timedelta(days=5),  # stale
            },
            {
                "entity_kind": "btd6_unknown",
                "fact_count": 0,
                "last_fetched_at": None,  # never
            },
        ]

    monkeypatch.setattr(btd6_db, "aggregate_facts_by_entity_kind", _agg)

    summary = await btd6_knowledge_service.fact_summary_by_kind()
    by_kind = {s.entity_kind: s for s in summary}
    assert by_kind["btd6_race"].bucket == "stale"
    assert by_kind["btd6_unknown"].bucket == "never"
    assert by_kind["btd6_unknown"].last_fetched_at is None


def test_no_private_threshold_imports():
    """fact_summary_by_kind must not import private threshold constants."""
    import inspect

    from services import btd6_knowledge_service as ks

    source = inspect.getsource(ks)
    assert "_FRESH_THRESHOLD" not in source, (
        "btd6_knowledge_service must use bucket_freshness, not private "
        "threshold constants"
    )
    assert "_AGING_THRESHOLD" not in source
    assert "_bucket_for" not in source
