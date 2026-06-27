"""Focused unit tests for the YouTube response renderers.

Part of closing the Media/YouTube readiness "Embed/renderer focused tests"
Not-Done row.  Exercises the ``render_describe`` / ``render_compare`` guards
(wrong render-context type, too-few videos) and the happy path.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from services.youtube_context_service import (
    TranscriptContext,
    VideoContext,
    VideoMetadata,
    VideoReference,
    YouTubeContext,
)
from views.youtube_renderers import render_compare, render_describe


def _video(video_id: str, title: str) -> VideoContext:
    return VideoContext(
        reference=VideoReference(
            provider="youtube",
            video_id=video_id,
            canonical_url=f"https://www.youtube.com/watch?v={video_id}",
            original_url=None,
        ),
        metadata=VideoMetadata(
            title=title,
            channel_name="Chan",
            published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            duration_seconds=60,
            description_excerpt=None,
            thumbnail_url=None,
        ),
        transcript=TranscriptContext(
            available=False,
            language=None,
            excerpt=None,
            coverage_seconds=None,
        ),
        limitations=(),
    )


def _yt_context(*videos: VideoContext) -> YouTubeContext:
    return YouTubeContext(
        facts=(),
        source_summary="ok",
        confidence=0.8,
        videos=tuple(videos),
    )


def _response(text: str = "summary"):
    return SimpleNamespace(text=text)


# ---------------------------------------------------------------------------
# render_describe
# ---------------------------------------------------------------------------


async def test_render_describe_returns_none_for_wrong_context_type():
    result = await render_describe(None, _response(), None, object())
    assert result is None


async def test_render_describe_returns_none_when_no_videos():
    result = await render_describe(None, _response(), None, _yt_context())
    assert result is None


async def test_render_describe_builds_card_embed():
    ctx = _yt_context(_video("aaaaaaaaaaa", "Solo Video"))
    result = await render_describe(None, _response("the summary"), None, ctx)
    assert result is not None
    assert result.content is None
    assert result.embed is not None
    assert result.embed.title == "Solo Video"
    assert result.embed.description == "the summary"


# ---------------------------------------------------------------------------
# render_compare
# ---------------------------------------------------------------------------


async def test_render_compare_returns_none_for_wrong_context_type():
    result = await render_compare(None, _response(), None, object())
    assert result is None


async def test_render_compare_returns_none_with_fewer_than_two_videos():
    ctx = _yt_context(_video("aaaaaaaaaaa", "Only One"))
    result = await render_compare(None, _response(), None, ctx)
    assert result is None


async def test_render_compare_builds_comparison_embed():
    ctx = _yt_context(
        _video("aaaaaaaaaaa", "First"),
        _video("bbbbbbbbbbb", "Second"),
    )
    result = await render_compare(None, _response("vs"), None, ctx)
    assert result is not None
    assert result.embed is not None
    assert result.embed.title == "Video Comparison"
    assert [f.name for f in result.embed.fields] == ["Video A", "Video B"]
