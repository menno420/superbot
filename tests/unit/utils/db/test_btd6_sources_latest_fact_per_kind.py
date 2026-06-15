"""Pin the new ``latest_fact_per_entity_kind`` DB helper.

DISTINCT ON returns one row per kind, newest by ``fetched_at``. Kinds
absent from ``btd6_facts`` are absent from the dict. Empty input
returns ``{}`` without hitting the DB.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from utils.db import btd6_sources as btd6_db


@pytest.mark.asyncio
async def test_empty_kinds_returns_empty_dict_without_db_call(monkeypatch):
    """Fast-path: no SQL round-trip when ``kinds`` is empty."""
    fake_pool = MagicMock()
    fake_pool.fetch = AsyncMock()
    monkeypatch.setattr(btd6_db.pool, "get", lambda: fake_pool)

    result = await btd6_db.latest_fact_per_entity_kind([])

    assert result == {}
    fake_pool.fetch.assert_not_called()


@pytest.mark.asyncio
async def test_one_row_per_kind_keyed_by_entity_kind(monkeypatch):
    now = datetime.now(tz=timezone.utc)

    canned = [
        {
            "id": 1,
            "source_id": 7,
            "fact_type": "btd6.races_index",
            "entity_kind": "btd6_race",
            "entity_key": "Reversed_Loop",
            "body_json": {"name": "Reversed Loop"},
            "game_version": "44.0",
            "fetched_at": now,
            "validated_at": None,
            "confidence": 1.0,
            "version": 1,
        },
        {
            "id": 2,
            "source_id": 8,
            "fact_type": "btd6.bosses_index",
            "entity_kind": "btd6_boss",
            "entity_key": "Diamondback5",
            "body_json": {"name": "Diamondback v5"},
            "game_version": "44.0",
            "fetched_at": now,
            "validated_at": None,
            "confidence": 1.0,
            "version": 1,
        },
    ]
    fake_pool = MagicMock()
    fake_pool.fetch = AsyncMock(return_value=canned)
    monkeypatch.setattr(btd6_db.pool, "get", lambda: fake_pool)

    result = await btd6_db.latest_fact_per_entity_kind(["btd6_race", "btd6_boss"])

    assert set(result) == {"btd6_race", "btd6_boss"}
    assert result["btd6_race"]["entity_key"] == "Reversed_Loop"
    assert result["btd6_boss"]["entity_key"] == "Diamondback5"

    # SQL must use DISTINCT ON + ANY ordering by fetched_at DESC.
    sql_call = fake_pool.fetch.call_args
    sql = sql_call.args[0]
    assert "DISTINCT ON (entity_kind)" in sql
    assert "entity_kind = ANY" in sql
    assert "ORDER BY entity_kind, fetched_at DESC" in sql


@pytest.mark.asyncio
async def test_missing_kinds_are_absent_not_none(monkeypatch):
    """When the registry has no facts for a kind, the dict simply lacks the key."""
    fake_pool = MagicMock()
    fake_pool.fetch = AsyncMock(return_value=[])
    monkeypatch.setattr(btd6_db.pool, "get", lambda: fake_pool)

    result = await btd6_db.latest_fact_per_entity_kind(["btd6_race"])

    assert result == {}
    assert "btd6_race" not in result


# ---------------------------------------------------------------------------
# get_latest_fact: extended to accept ``fact_type=None``
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_latest_fact_with_none_fact_type_omits_clause(monkeypatch):
    captured: dict = {}

    async def _fetchrow(sql, *args):
        captured["sql"] = sql
        captured["args"] = args
        return None

    fake_pool = MagicMock()
    fake_pool.fetchrow = _fetchrow
    monkeypatch.setattr(btd6_db.pool, "get", lambda: fake_pool)

    await btd6_db.get_latest_fact(None, "btd6_race", "Reversed_Loop")

    # No ``f.fact_type = $1`` filter clause when fact_type is None.
    # (``f.fact_type`` still appears in the SELECT projection.)
    assert "f.fact_type = $1" not in captured["sql"]
    # entity_kind + entity_key are the only filter params.
    assert captured["args"] == ("btd6_race", "Reversed_Loop")


@pytest.mark.asyncio
async def test_get_latest_fact_with_fact_type_keeps_clause(monkeypatch):
    captured: dict = {}

    async def _fetchrow(sql, *args):
        captured["sql"] = sql
        captured["args"] = args
        return None

    fake_pool = MagicMock()
    fake_pool.fetchrow = _fetchrow
    monkeypatch.setattr(btd6_db.pool, "get", lambda: fake_pool)

    await btd6_db.get_latest_fact(
        "btd6.race_metadata", "btd6_race", "Reversed_Loop",
    )

    assert "f.fact_type = $1" in captured["sql"]
    assert captured["args"] == (
        "btd6.race_metadata",
        "btd6_race",
        "Reversed_Loop",
    )
