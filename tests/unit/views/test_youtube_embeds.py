"""Focused unit tests for the YouTube Discord embed builders.

Part of closing the Media/YouTube readiness "Embed/renderer focused tests"
Not-Done row.  Pure embed construction — no Discord I/O.
"""

from __future__ import annotations

from datetime import datetime, timezone

from services.youtube_context_service import (
    TranscriptContext,
    VideoContext,
    VideoMetadata,
    VideoReference,
)
from views.youtube_embeds import build_compare_embed, build_video_card_embed


def _ctx(
    *,
    video_id: str = "dQw4w9WgXcQ",
    title: str | None = "Rick Astley - Never Gonna Give You Up",
    channel: str | None = "Rick Astley",
    published: datetime | None = datetime(2009, 10, 25, tzinfo=timezone.utc),
    duration: int | None = 213,
    thumbnail: str | None = "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
    transcript_available: bool = True,
) -> VideoContext:
    return VideoContext(
        reference=VideoReference(
            provider="youtube",
            video_id=video_id,
            canonical_url=f"https://www.youtube.com/watch?v={video_id}",
            original_url=None,
        ),
        metadata=VideoMetadata(
            title=title,
            channel_name=channel,
            published_at=published,
            duration_seconds=duration,
            description_excerpt=None,
            thumbnail_url=thumbnail,
        ),
        transcript=TranscriptContext(
            available=transcript_available,
            language=None,
            excerpt="hi" if transcript_available else None,
            coverage_seconds=None,
        ),
        limitations=(),
    )


# ---------------------------------------------------------------------------
# build_video_card_embed
# ---------------------------------------------------------------------------


def test_card_embed_carries_metadata_and_summary():
    embed = build_video_card_embed(_ctx(), "An AI-written summary.")
    assert embed.title == "Rick Astley - Never Gonna Give You Up"
    assert embed.url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert embed.description == "An AI-written summary."
    assert embed.author.name == "Rick Astley"
    assert embed.thumbnail.url.endswith("hqdefault.jpg")
    field_names = {f.name: f.value for f in embed.fields}
    assert field_names["Duration"] == "3:33"  # 213s
    assert field_names["Published"] == "2009-10-25"
    assert embed.footer.text == "Transcript available"


def test_card_embed_falls_back_to_video_id_and_no_transcript_footer():
    ctx = _ctx(
        title=None,
        channel=None,
        published=None,
        duration=None,
        thumbnail=None,
        transcript_available=False,
    )
    embed = build_video_card_embed(ctx, "")
    assert embed.title == "dQw4w9WgXcQ"  # title falls back to the id
    assert embed.description is None  # empty summary → no description
    assert embed.fields == []  # no duration / published fields
    assert embed.footer.text == "No transcript"


def test_card_embed_formats_hours_in_duration():
    embed = build_video_card_embed(_ctx(duration=3661), "s")  # 1:01:01
    field_names = {f.name: f.value for f in embed.fields}
    assert field_names["Duration"] == "1:01:01"


def test_card_embed_truncates_an_overlong_title():
    embed = build_video_card_embed(_ctx(title="A" * 300), "s")
    assert len(embed.title) == 256


# ---------------------------------------------------------------------------
# build_compare_embed
# ---------------------------------------------------------------------------


def test_compare_embed_lists_both_videos():
    a = _ctx(video_id="aaaaaaaaaaa", title="First", channel="ChanA", duration=60)
    b = _ctx(video_id="bbbbbbbbbbb", title="Second", channel="ChanB", duration=120)
    embed = build_compare_embed(a, b, "comparison text")
    assert embed.title == "Video Comparison"
    assert embed.description == "comparison text"
    labels = [f.name for f in embed.fields]
    assert labels == ["Video A", "Video B"]
    a_field = embed.fields[0].value
    assert "[First](https://www.youtube.com/watch?v=aaaaaaaaaaa)" in a_field
    assert "by ChanA" in a_field
    assert "1:00" in a_field
    b_field = embed.fields[1].value
    assert "Second" in b_field
    assert "2:00" in b_field


def test_compare_embed_omits_optional_lines_when_absent():
    a = _ctx(title=None, channel=None, duration=None)
    b = _ctx(video_id="bbbbbbbbbbb", channel=None, duration=None)
    embed = build_compare_embed(a, b, "")
    assert embed.description is None
    # title falls back to the video id when absent, no "by"/duration lines
    a_field = embed.fields[0].value
    assert "dQw4w9WgXcQ" in a_field
    assert "by " not in a_field
