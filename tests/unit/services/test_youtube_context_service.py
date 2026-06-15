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
        "thumbnails": {"high": {"url": "https://i.ytimg.com/vi/abc/hqdefault.jpg"}},
    },
    "contentDetails": {"duration": "PT5M30S"},
    # Raw provider fields that must NEVER reach storage (data-minimisation).
    "id": "dQw4w9WgXcQ",
    "statistics": {"viewCount": "9999"},
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


# ---------------------------------------------------------------------------
# Data-minimisation projection (P0-2 / Q-0099)
# ---------------------------------------------------------------------------

_BOUNDED_KEYS = {
    "title",
    "channel_name",
    "published_at",
    "duration_seconds",
    "description_excerpt",
    "thumbnail_url",
}


def test_project_metadata_extracts_only_bounded_fields():
    projected = youtube_context_service._project_metadata(_FAKE_METADATA)
    # Only the bounded keys — no raw provider keys leak through.
    assert set(projected) == _BOUNDED_KEYS
    assert "snippet" not in projected
    assert "contentDetails" not in projected
    assert "statistics" not in projected
    assert "id" not in projected
    assert projected["title"] == "Test Video"
    assert projected["channel_name"] == "Test Channel"
    assert projected["duration_seconds"] == 330
    assert projected["thumbnail_url"] == "https://i.ytimg.com/vi/abc/hqdefault.jpg"


def test_project_metadata_is_idempotent():
    once = youtube_context_service._project_metadata(_FAKE_METADATA)
    twice = youtube_context_service._project_metadata(once)
    assert once == twice


def test_project_metadata_empty_is_empty():
    assert youtube_context_service._project_metadata({}) == {}


def test_description_excerpt_is_capped():
    raw = {"snippet": {"description": "x" * 5000}}
    projected = youtube_context_service._project_metadata(raw)
    assert len(projected["description_excerpt"]) <= youtube_context_service._MAX_DESCRIPTION_CHARS


async def test_cache_miss_stores_only_bounded_projection(monkeypatch):
    """The fresh-fetch path must persist the bounded projection, not the raw
    provider payload (the headline Q-0099 privacy guarantee)."""
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
    put_mock = AsyncMock()
    monkeypatch.setattr("services.video_reference_cache_service.put_cached", put_mock)

    await youtube_context_service.build(_req("https://youtube.com/watch?v=dQw4w9WgXcQ"))

    put_mock.assert_called_once()
    stored = put_mock.call_args.args[1]
    assert set(stored) == _BOUNDED_KEYS
    assert "snippet" not in stored and "statistics" not in stored and "id" not in stored


# ---------------------------------------------------------------------------
# Thumbnail URL validation
# ---------------------------------------------------------------------------


def test_safe_thumbnail_url_accepts_youtube_hosts():
    assert (
        youtube_context_service._safe_thumbnail_url(
            "https://i.ytimg.com/vi/abc/hqdefault.jpg",
        )
        == "https://i.ytimg.com/vi/abc/hqdefault.jpg"
    )
    assert (
        youtube_context_service._safe_thumbnail_url("https://img.youtube.com/vi/abc/0.jpg")
        == "https://img.youtube.com/vi/abc/0.jpg"
    )


def test_safe_thumbnail_url_rejects_foreign_and_insecure():
    assert youtube_context_service._safe_thumbnail_url("https://example.com/thumb.jpg") is None
    assert youtube_context_service._safe_thumbnail_url("http://i.ytimg.com/x.jpg") is None
    assert youtube_context_service._safe_thumbnail_url("https://evil-ytimg.com/x.jpg") is None
    assert youtube_context_service._safe_thumbnail_url(None) is None
    assert youtube_context_service._safe_thumbnail_url("not a url") is None
