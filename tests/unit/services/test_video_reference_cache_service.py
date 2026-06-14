"""Unit tests for video_reference_cache_service.

The DB helper layer is mocked; these tests pin the service seam's behaviour
(bounded-projection storage contract + retention purge delegation, P0-2/Q-0099).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import video_reference_cache_service as svc  # noqa: E402


async def test_put_cached_stores_metadata_as_given(monkeypatch):
    """The service is provider-shape-agnostic: it persists exactly the bounded
    dict it is handed (projection is the caller's job)."""
    upsert = AsyncMock()
    monkeypatch.setattr(svc._db, "upsert_video_cache", upsert)

    bounded = {"title": "T", "channel_name": "C", "description_excerpt": "d"}
    await svc.put_cached("vid", bounded, "transcript", fetch_status="ok")

    upsert.assert_called_once()
    assert upsert.call_args.kwargs["metadata_json"] is bounded
    assert upsert.call_args.kwargs["fetch_status"] == "ok"
    # transcript present → transcript_status not flagged unavailable
    assert upsert.call_args.kwargs["transcript_status"] is None


async def test_put_cached_error_row_marks_transcript_unavailable(monkeypatch):
    upsert = AsyncMock()
    monkeypatch.setattr(svc._db, "upsert_video_cache", upsert)

    await svc.put_cached("vid", {}, None, fetch_status="private_or_deleted", last_error_code="x")

    assert upsert.call_args.kwargs["transcript_status"] == "unavailable"
    assert upsert.call_args.kwargs["last_error_code"] == "x"
    assert upsert.call_args.kwargs["last_error_at"] is not None


async def test_purge_expired_delegates_and_returns_count(monkeypatch):
    purge = AsyncMock(return_value=4)
    monkeypatch.setattr(svc._db, "purge_expired_video_cache", purge)

    removed = await svc.purge_expired()

    purge.assert_called_once()
    assert removed == 4


async def test_cache_health_derives_live_rows_and_passes_timestamps(monkeypatch):
    from datetime import datetime, timezone

    oldest = datetime(2026, 6, 1, tzinfo=timezone.utc)
    newest = datetime(2026, 6, 14, tzinfo=timezone.utc)
    next_expiry = datetime(2026, 6, 15, tzinfo=timezone.utc)
    stats = AsyncMock(
        return_value={
            "total_rows": 10,
            "expired_rows": 3,
            "ok_rows": 8,
            "error_rows": 2,
            "with_transcript_rows": 6,
            "oldest_fetched_at": oldest,
            "newest_fetched_at": newest,
            "next_expiry_at": next_expiry,
        },
    )
    monkeypatch.setattr(svc._db, "get_cache_stats", stats)

    health = await svc.cache_health()

    assert health.total_rows == 10
    assert health.expired_rows == 3
    assert health.live_rows == 7  # derived
    assert health.ok_rows == 8
    assert health.error_rows == 2
    assert health.with_transcript_rows == 6
    assert health.oldest_fetched_at == oldest
    assert health.next_expiry_at == next_expiry


async def test_cache_health_handles_empty_table(monkeypatch):
    """A fresh/empty table returns NULL aggregates — must not crash."""
    monkeypatch.setattr(svc._db, "get_cache_stats", AsyncMock(return_value={}))

    health = await svc.cache_health()

    assert health.total_rows == 0
    assert health.live_rows == 0
    assert health.oldest_fetched_at is None
    assert health.next_expiry_at is None


def test_cache_health_dataclass_has_no_content_fields():
    """The health read model exposes only counts/timestamps — no content
    column (P0-2 / Q-0099 content-free contract)."""
    fields = set(svc.MediaCacheHealth.__dataclass_fields__)
    for forbidden in ("metadata_json", "transcript_text", "video_id", "title"):
        assert forbidden not in fields

