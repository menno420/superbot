"""Unit tests for youtube_context_service.build().

All external I/O mocked; no real YouTube API calls.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai.contracts import AITask  # noqa: E402
from core.runtime.ai.feature_facts import FeatureFactRequest  # noqa: E402
from services import youtube_context_service  # noqa: E402


def _req(text: str = "") -> FeatureFactRequest:
    return FeatureFactRequest(
        task=AITask.VIDEO_DESCRIBE,
        text=text,
        guild_id=1234,
        channel_id=5678,
        author_id=9,
        message_id=0,
    )


_FAKE_METADATA = {
    "snippet": {
        "title": "Test Video",
        "channelTitle": "Test Channel",
        "publishedAt": "2024-01-15T10:00:00Z",
        "description": "A test video description.",
        "thumbnails": {"high": {"url": "https://example.com/thumb.jpg"}},
    },
    "contentDetails": {"duration": "PT5M30S"},
}


# ---------------------------------------------------------------------------
# Feature flag off
# ---------------------------------------------------------------------------


async def test_flag_off_returns_empty_with_error_reason(monkeypatch):
    monkeypatch.setattr(
        youtube_context_service,
        "is_enabled",
        AsyncMock(return_value=False),
    )
    result = await youtube_context_service.build(_req("https://youtube.com/watch?v=dQw4w9WgXcQ"))
    assert result.facts == ()
    assert result.error_reason == "video_feature_disabled"


# ---------------------------------------------------------------------------
# Missing API key
# ---------------------------------------------------------------------------


async def test_missing_api_key_returns_error_reason(monkeypatch):
    monkeypatch.setattr(youtube_context_service, "is_enabled", AsyncMock(return_value=True))
    monkeypatch.setattr(youtube_context_service.youtube_fetch_service, "_API_KEY", None)
    result = await youtube_context_service.build(_req("https://youtube.com/watch?v=dQw4w9WgXcQ"))
    assert result.facts == ()
    assert result.error_reason == "youtube_api_key_missing"


# ---------------------------------------------------------------------------
# OK path — cache hit
# ---------------------------------------------------------------------------


async def test_cache_hit_returns_facts(monkeypatch):
    from datetime import datetime, timezone

    cached_entry = MagicMock(
        fetch_status="ok",
        metadata_json=_FAKE_METADATA,
        transcript_text="Hello world transcript.",
        fetched_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc),
    )
    monkeypatch.setattr(youtube_context_service, "is_enabled", AsyncMock(return_value=True))
    monkeypatch.setattr(youtube_context_service.youtube_fetch_service, "_API_KEY", "fake-key")
    monkeypatch.setattr(
        "services.video_reference_cache_service.get_cached",
        AsyncMock(return_value=cached_entry),
    )

    result = await youtube_context_service.build(_req("https://youtube.com/watch?v=dQw4w9WgXcQ"))

    assert len(result.facts) > 0
    assert any("Test Video" in f for f in result.facts)
    assert result.error_reason is None


# ---------------------------------------------------------------------------
# OK path — cache miss, fetch succeeds
# ---------------------------------------------------------------------------


async def test_cache_miss_fetch_ok(monkeypatch):
    monkeypatch.setattr(youtube_context_service, "is_enabled", AsyncMock(return_value=True))
    monkeypatch.setattr(youtube_context_service.youtube_fetch_service, "_API_KEY", "fake-key")
    monkeypatch.setattr(
        "services.video_reference_cache_service.get_cached",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "services.youtube_fetch_service.fetch_video_metadata",
        AsyncMock(return_value=_FAKE_METADATA),
    )
    monkeypatch.setattr(
        "services.youtube_fetch_service.fetch_transcript",
        AsyncMock(return_value=[{"text": "Transcript text."}]),
    )
    monkeypatch.setattr(
        "services.video_reference_cache_service.put_cached",
        AsyncMock(),
    )

    result = await youtube_context_service.build(_req("https://youtube.com/watch?v=dQw4w9WgXcQ"))

    assert len(result.facts) > 0
    assert result.error_reason is None
    assert result.confidence > 0.0


# ---------------------------------------------------------------------------
# Private/deleted video → negative cache
# ---------------------------------------------------------------------------


async def test_private_video_returns_error(monkeypatch):
    from services.youtube_fetch_service import YouTubeFetchError

    monkeypatch.setattr(youtube_context_service, "is_enabled", AsyncMock(return_value=True))
    monkeypatch.setattr(youtube_context_service.youtube_fetch_service, "_API_KEY", "fake-key")
    monkeypatch.setattr(
        "services.video_reference_cache_service.get_cached",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "services.youtube_fetch_service.fetch_video_metadata",
        AsyncMock(side_effect=YouTubeFetchError("abc", "video_private_or_deleted")),
    )
    put_mock = AsyncMock()
    monkeypatch.setattr("services.video_reference_cache_service.put_cached", put_mock)

    result = await youtube_context_service.build(_req("https://youtube.com/watch?v=dQw4w9WgXcQ"))

    assert result.facts == ()
    assert result.error_reason == "video_private_or_deleted"
    put_mock.assert_called_once()
    assert put_mock.call_args.kwargs.get("fetch_status") != "ok"


# ---------------------------------------------------------------------------
# No transcript — metadata-only facts, no error
# ---------------------------------------------------------------------------


async def test_no_transcript_gives_metadata_only_facts(monkeypatch):
    monkeypatch.setattr(youtube_context_service, "is_enabled", AsyncMock(return_value=True))
    monkeypatch.setattr(youtube_context_service.youtube_fetch_service, "_API_KEY", "fake-key")
    monkeypatch.setattr(
        "services.video_reference_cache_service.get_cached",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        "services.youtube_fetch_service.fetch_video_metadata",
        AsyncMock(return_value=_FAKE_METADATA),
    )
    monkeypatch.setattr(
        "services.youtube_fetch_service.fetch_transcript",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr("services.video_reference_cache_service.put_cached", AsyncMock())

    result = await youtube_context_service.build(_req("https://youtube.com/watch?v=dQw4w9WgXcQ"))

    assert len(result.facts) > 0
    assert result.error_reason is None
    assert any("unavailable" in f for f in result.facts)


# ---------------------------------------------------------------------------
# Same URL twice — cache is hit on second call (fetched_at unchanged)
# ---------------------------------------------------------------------------


async def test_same_url_twice_uses_cache(monkeypatch):
    from datetime import datetime, timezone

    cached_entry = MagicMock(
        fetch_status="ok",
        metadata_json=_FAKE_METADATA,
        transcript_text="Cached transcript.",
        fetched_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(youtube_context_service, "is_enabled", AsyncMock(return_value=True))
    monkeypatch.setattr(youtube_context_service.youtube_fetch_service, "_API_KEY", "fake-key")
    get_mock = AsyncMock(return_value=cached_entry)
    monkeypatch.setattr("services.video_reference_cache_service.get_cached", get_mock)
    fetch_mock = AsyncMock()
    monkeypatch.setattr("services.youtube_fetch_service.fetch_video_metadata", fetch_mock)

    text = "https://youtube.com/watch?v=dQw4w9WgXcQ"
    await youtube_context_service.build(_req(text))
    await youtube_context_service.build(_req(text))

    fetch_mock.assert_not_called()


# ---------------------------------------------------------------------------
# Sanitisation — Discord mentions escaped
# ---------------------------------------------------------------------------


def test_sanitise_escapes_mentions():
    raw = "Hello @everyone and <@123> and @here"
    result = youtube_context_service._sanitise(raw, 500)
    assert "@everyone" not in result
    assert "@here" not in result
    assert "<@123>" not in result


# ---------------------------------------------------------------------------
# Duration parsing
# ---------------------------------------------------------------------------


def test_parse_iso8601_duration():
    assert youtube_context_service._parse_iso8601_duration("PT5M30S") == 330
    assert youtube_context_service._parse_iso8601_duration("PT1H") == 3600
    assert youtube_context_service._parse_iso8601_duration("PT2H15M") == 8100
    assert youtube_context_service._parse_iso8601_duration("invalid") is None
