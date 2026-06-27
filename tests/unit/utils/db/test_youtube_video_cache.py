"""Focused unit tests for the ``youtube_video_cache`` DB primitives.

Advances the Media/YouTube readiness "Fetch/cache/DB" row: the
``get_video_cache`` / ``upsert_video_cache`` / ``purge_expired_video_cache``
primitives had no dedicated test (only ``get_cache_stats`` did).  The pool
connection is mocked (the pattern used by ``test_youtube_video_cache_stats``),
so these run offline with no live PostgreSQL.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from utils.db import youtube_video_cache as cache


def _fake_conn(monkeypatch, *, fetchrow_return=None, execute_return="") -> dict:
    captured: dict = {}

    async def _fetchrow(sql, *args):
        captured["sql"] = sql
        captured["args"] = args
        return fetchrow_return

    async def _execute(sql, *args):
        captured["sql"] = sql
        captured["args"] = args
        return execute_return

    conn = MagicMock()
    conn.fetchrow = AsyncMock(side_effect=_fetchrow)
    conn.execute = AsyncMock(side_effect=_execute)
    monkeypatch.setattr(cache.pool, "get", lambda: conn)
    return captured


# ---------------------------------------------------------------------------
# get_video_cache
# ---------------------------------------------------------------------------


async def test_get_video_cache_returns_dict_when_row_present(monkeypatch):
    row = {"video_id": "abc", "fetch_status": "ok"}
    captured = _fake_conn(monkeypatch, fetchrow_return=row)
    result = await cache.get_video_cache("abc")
    assert result == row
    assert captured["args"] == ("abc",)


async def test_get_video_cache_returns_none_when_absent(monkeypatch):
    _fake_conn(monkeypatch, fetchrow_return=None)
    assert await cache.get_video_cache("missing") is None


async def test_get_video_cache_enforces_ttl_in_query(monkeypatch):
    """A reader must never see an expired row — the TTL filter is in the SQL."""
    captured = _fake_conn(monkeypatch, fetchrow_return=None)
    await cache.get_video_cache("abc")
    assert "expires_at > now()" in captured["sql"]


async def test_get_video_cache_returns_a_plain_dict_copy(monkeypatch):
    """The asyncpg Record is wrapped in a plain dict (dict(row))."""

    class _Record(dict):
        """Stand-in for an asyncpg Record (dict-like)."""

    rec = _Record(video_id="abc", fetch_status="ok")
    _fake_conn(monkeypatch, fetchrow_return=rec)
    result = await cache.get_video_cache("abc")
    assert type(result) is dict
    assert result == {"video_id": "abc", "fetch_status": "ok"}


# ---------------------------------------------------------------------------
# upsert_video_cache
# ---------------------------------------------------------------------------


async def test_upsert_serializes_metadata_and_orders_params(monkeypatch):
    captured = _fake_conn(monkeypatch)
    expires = datetime(2024, 1, 2, tzinfo=timezone.utc)
    err_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    await cache.upsert_video_cache(
        video_id="abc",
        metadata_json={"title": "T"},
        transcript_text="words",
        fetch_status="ok",
        transcript_status="present",
        last_error_code=None,
        last_error_at=err_at,
        expires_at=expires,
    )
    args = captured["args"]
    # Positional order must match the INSERT placeholders ($1..$8).
    assert args[0] == "abc"
    assert args[1] == json.dumps({"title": "T"})  # metadata is JSON-serialized
    assert args[2] == "words"
    assert args[3] == "ok"
    assert args[4] == "present"
    assert args[5] is None
    assert args[6] == err_at
    assert args[7] == expires
    assert "$2::jsonb" in captured["sql"]
    assert "ON CONFLICT (video_id) DO UPDATE" in captured["sql"]


async def test_upsert_handles_empty_metadata(monkeypatch):
    captured = _fake_conn(monkeypatch)
    await cache.upsert_video_cache(
        video_id="abc",
        metadata_json={},
        transcript_text=None,
        fetch_status="private_or_deleted",
        transcript_status=None,
        last_error_code="video_private_or_deleted",
        last_error_at=None,
        expires_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    args = captured["args"]
    assert args[1] == "{}"  # empty dict still serializes (error-cache row)
    assert args[2] is None
    assert args[3] == "private_or_deleted"
    assert args[5] == "video_private_or_deleted"


# ---------------------------------------------------------------------------
# purge_expired_video_cache
# ---------------------------------------------------------------------------


async def test_purge_parses_deleted_row_count(monkeypatch):
    captured = _fake_conn(monkeypatch, execute_return="DELETE 5")
    deleted = await cache.purge_expired_video_cache()
    assert deleted == 5
    assert "DELETE FROM youtube_video_cache WHERE expires_at <= now()" in captured["sql"]


async def test_purge_returns_zero_when_nothing_expired(monkeypatch):
    _fake_conn(monkeypatch, execute_return="DELETE 0")
    assert await cache.purge_expired_video_cache() == 0
