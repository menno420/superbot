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
