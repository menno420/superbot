"""PR-D tests for source health bucketing + bounded listing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services import btd6_source_registry as svc
from utils.db import btd6_sources as btd6_db


def _row(
    *,
    sid: int = 1,
    key: str = "nk_btd6_races",
    name: str = "Races",
    tier: int = 1,
    enabled: bool = True,
    kind: str = "official_api",
    fetched_at=None,
    fact_count: int = 0,
):
    return {
        "id": sid,
        "source_key": key,
        "source_name": name,
        "source_owner": "Ninja Kiwi",
        "source_kind": kind,
        "trust_tier": tier,
        "base_url": "https://api",
        "path_template": "/btd6/races",
        "full_url": None,
        "enabled": enabled,
        "notes": "",
        "last_fetched_at": fetched_at,
        "fact_count": fact_count,
    }


# ---------------------------------------------------------------------------
# Bucketing
# ---------------------------------------------------------------------------


def test_bucket_never_when_never_fetched():
    assert svc._bucket_for(None) == "never"


def test_bucket_fresh_for_recent_fetch():
    now = datetime.now(tz=timezone.utc)
    assert svc._bucket_for(now - timedelta(minutes=30)) == "fresh"


def test_bucket_aging_for_yesterday():
    now = datetime.now(tz=timezone.utc)
    assert svc._bucket_for(now - timedelta(days=1)) == "aging"


def test_bucket_stale_for_old_data():
    now = datetime.now(tz=timezone.utc)
    assert svc._bucket_for(now - timedelta(days=7)) == "stale"


def test_bucket_accepts_naive_datetime():
    """The DB column is TIMESTAMPTZ but asyncpg may return naive
    datetimes in some envs; the bucketer must treat them as UTC.
    """
    naive = datetime.now() - timedelta(hours=1)
    assert svc._bucket_for(naive) in {"fresh", "aging"}


# ---------------------------------------------------------------------------
# list_health
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_health_uses_bounded_db_helper(monkeypatch):
    captured = {}

    async def _fake(*, enabled, limit, offset):
        captured["enabled"] = enabled
        captured["limit"] = limit
        captured["offset"] = offset
        now = datetime.now(tz=timezone.utc)
        return [
            _row(sid=1, key="nk_btd6_races", fetched_at=now, fact_count=10),
            _row(sid=2, key="nk_btd6_bosses", fetched_at=None, fact_count=0),
        ]

    monkeypatch.setattr(btd6_db, "list_sources_with_freshness", _fake)

    health = await svc.list_health(limit=25)
    assert captured == {"enabled": None, "limit": 25, "offset": 0}
    assert {h.source_key for h in health} == {"nk_btd6_races", "nk_btd6_bosses"}
    races = next(h for h in health if h.source_key == "nk_btd6_races")
    assert races.bucket == "fresh"
    assert races.fact_count == 10
    bosses = next(h for h in health if h.source_key == "nk_btd6_bosses")
    assert bosses.bucket == "never"
    assert bosses.fact_count == 0


# ---------------------------------------------------------------------------
# list_sources bound enforcement
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_sources_caps_huge_limit(monkeypatch):
    captured = []

    class _FakeConn:
        async def fetch(self, sql, *args):
            captured.append({"sql": sql, "args": args})
            return []

    monkeypatch.setattr("utils.db.btd6_sources.pool.get", lambda: _FakeConn())

    await btd6_db.list_sources(limit=999_999)

    # Caller asked for 999_999 — the helper must have clamped to
    # the hard cap before binding.
    args = captured[0]["args"]
    assert args[0] == btd6_db._LIST_SOURCES_MAX_LIMIT
    sql = captured[0]["sql"]
    assert "LIMIT" in sql
    assert "OFFSET" in sql


@pytest.mark.asyncio
async def test_list_sources_min_limit_one(monkeypatch):
    captured = []

    class _FakeConn:
        async def fetch(self, sql, *args):
            captured.append({"args": args})
            return []

    monkeypatch.setattr("utils.db.btd6_sources.pool.get", lambda: _FakeConn())

    await btd6_db.list_sources(limit=0)
    assert captured[0]["args"][0] == 1
