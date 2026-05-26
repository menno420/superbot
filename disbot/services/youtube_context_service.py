"""YouTube URL context supplier for the AI pipeline.

Feature-flag gated: only activates when youtube.context.enabled is ON
for the guild AND message contains a supported YouTube URL.

Rollout note: the flag being registered in the DB does NOT mean it is
active.  The evaluator follows: env override (SUPERBOT_FF_YOUTUBE_CONTEXT_ENABLED=on)
→ feature_flag.primary DB state → guild-level override → default_value=False.
YOUTUBE_API_KEY must also be set; if missing the feature is effectively
off even when the flag is enabled.

No raw SQL in this module; DB access goes through video_reference_cache_service.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from core.runtime.ai.feature_facts import FeatureFactRequest
from core.runtime.feature_flags import is_enabled
from services import video_reference_cache_service, youtube_fetch_service

logger = logging.getLogger("bot.services.youtube_context")

_YOUTUBE_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")
_MENTION_RE = re.compile(r"(@everyone|@here|<@[!&]?\d+>)")

_MAX_DESCRIPTION_CHARS = 500
_MAX_TRANSCRIPT_CHARS = 1500
_MAX_TITLE_CHARS = 200
_MAX_CHANNEL_CHARS = 100


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VideoReference:
    provider: Literal["youtube"]
    video_id: str
    canonical_url: str
    original_url: str | None


@dataclass(frozen=True)
class VideoMetadata:
    title: str | None
    channel_name: str | None
    published_at: datetime | None
    duration_seconds: int | None
    description_excerpt: str | None
    thumbnail_url: str | None


@dataclass(frozen=True)
class TranscriptContext:
    available: bool
    language: str | None
    excerpt: str | None
    coverage_seconds: int | None


@dataclass(frozen=True)
class VideoContext:
    reference: VideoReference
    metadata: VideoMetadata
    transcript: TranscriptContext
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class YouTubeContext:
    facts: tuple[str, ...]
    source_summary: str
    confidence: float
    videos: tuple[VideoContext, ...]
    error_reason: str | None = None


# ---------------------------------------------------------------------------
# Sanitisation
# ---------------------------------------------------------------------------


def _sanitise(text: str | None, max_chars: int = 500) -> str | None:
    if text is None:
        return None
    text = _CONTROL_CHAR_RE.sub(" ", text)
    text = _MENTION_RE.sub("[mention]", text)
    return text[:max_chars].strip() or None


# ---------------------------------------------------------------------------
# build()
# ---------------------------------------------------------------------------


async def build(req: FeatureFactRequest) -> YouTubeContext:
    # 1. Feature flag check.
    if not await is_enabled("youtube.context.enabled", req.guild_id):
        return YouTubeContext(
            facts=(),
            source_summary="feature_disabled",
            confidence=0.0,
            videos=(),
            error_reason="video_feature_disabled",
        )

    # 2. API key check.
    if not youtube_fetch_service._API_KEY:
        return YouTubeContext(
            facts=(),
            source_summary="api_key_missing",
            confidence=0.0,
            videos=(),
            error_reason="youtube_api_key_missing",
        )

    # 3. Extract video IDs (cap at 2).
    url_matches = _YOUTUBE_URL_RE.findall(req.text or "")
    video_ids = list(dict.fromkeys(url_matches))[:2]
    if not video_ids:
        return YouTubeContext(
            facts=(),
            source_summary="no_urls",
            confidence=0.0,
            videos=(),
            error_reason="video_grounding_failed",
        )

    # 4. Fetch or load from cache.
    video_contexts: list[VideoContext] = []
    last_error: str | None = None
    for video_id in video_ids:
        ctx = await _resolve_video(video_id)
        if ctx is None:
            last_error = last_error or "fetch_error"
            continue
        if isinstance(ctx, str):
            last_error = ctx
            continue
        video_contexts.append(ctx)

    if not video_contexts:
        return YouTubeContext(
            facts=(),
            source_summary=last_error or "fetch_error",
            confidence=0.0,
            videos=(),
            error_reason=last_error or "fetch_error",
        )

    # 5-6. Build facts.
    facts = _render_facts(video_contexts)

    return YouTubeContext(
        facts=tuple(facts),
        source_summary="ok",
        confidence=0.8,
        videos=tuple(video_contexts),
    )


async def _resolve_video(video_id: str) -> VideoContext | str | None:
    """Return VideoContext, an error_reason string, or None on transient failure."""
    cached = await video_reference_cache_service.get_cached(video_id)
    if cached is not None:
        if cached.fetch_status != "ok":
            return cached.fetch_status
        return _build_video_context(video_id, cached.metadata_json, cached.transcript_text)

    try:
        metadata = await youtube_fetch_service.fetch_video_metadata(video_id)
    except youtube_fetch_service.YouTubeFetchError as err:
        await video_reference_cache_service.put_cached(
            video_id,
            {},
            None,
            fetch_status=_reason_to_status(err.reason),
            last_error_code=err.reason,
        )
        return err.reason
    except Exception:
        logger.warning("unexpected error fetching metadata for %s", video_id, exc_info=True)
        return "fetch_error"

    transcript_segments = await youtube_fetch_service.fetch_transcript(video_id)
    transcript_text: str | None = None
    if transcript_segments:
        raw = " ".join(s.get("text", "") for s in transcript_segments)
        transcript_text = _sanitise(raw, _MAX_TRANSCRIPT_CHARS)

    await video_reference_cache_service.put_cached(
        video_id, metadata, transcript_text, fetch_status="ok"
    )
    return _build_video_context(video_id, metadata, transcript_text)


def _reason_to_status(reason: str) -> str:
    mapping = {
        "youtube_api_key_missing": "disabled_missing_api_key",
        "video_private_or_deleted": "private_or_deleted",
        "quota_limited": "quota_limited",
    }
    return mapping.get(reason, "metadata_error")


def _build_video_context(
    video_id: str,
    metadata: dict,
    transcript_text: str | None,
) -> VideoContext:
    snippet = metadata.get("snippet", {})
    content = metadata.get("contentDetails", {})

    title = _sanitise(snippet.get("title"), _MAX_TITLE_CHARS)
    channel = _sanitise(snippet.get("channelTitle"), _MAX_CHANNEL_CHARS)
    description = _sanitise(snippet.get("description", "")[:_MAX_DESCRIPTION_CHARS], _MAX_DESCRIPTION_CHARS)

    published_at: datetime | None = None
    raw_pub = snippet.get("publishedAt")
    if raw_pub:
        try:
            from datetime import timezone
            published_at = datetime.fromisoformat(raw_pub.replace("Z", "+00:00"))
        except ValueError:
            pass

    duration_seconds: int | None = None
    raw_dur = content.get("duration")
    if raw_dur:
        duration_seconds = _parse_iso8601_duration(raw_dur)

    thumbnails = snippet.get("thumbnails", {})
    thumbnail_url = (
        thumbnails.get("high", {}).get("url")
        or thumbnails.get("default", {}).get("url")
    )

    limitations: list[str] = []
    if not transcript_text:
        limitations.append("transcript_unavailable")

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
            published_at=published_at,
            duration_seconds=duration_seconds,
            description_excerpt=description,
            thumbnail_url=thumbnail_url,
        ),
        transcript=TranscriptContext(
            available=bool(transcript_text),
            language=None,
            excerpt=transcript_text,
            coverage_seconds=None,
        ),
        limitations=tuple(limitations),
    )


def _parse_iso8601_duration(duration: str) -> int | None:
    import re as _re
    m = _re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not m:
        return None
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


def _render_facts(contexts: list[VideoContext]) -> list[str]:
    facts: list[str] = []
    for i, ctx in enumerate(contexts, 1):
        label = f"Video {i}" if len(contexts) > 1 else "Video"
        m = ctx.metadata
        if m.title:
            facts.append(f"{label} title: {m.title}")
        if m.channel_name:
            facts.append(f"{label} channel: {m.channel_name}")
        if m.published_at:
            facts.append(f"{label} published: {m.published_at.strftime('%Y-%m-%d')}")
        if m.duration_seconds is not None:
            facts.append(f"{label} duration: {m.duration_seconds}s")
        if m.description_excerpt:
            facts.append(f"{label} description: {m.description_excerpt}")
        if ctx.transcript.excerpt:
            facts.append(f"{label} transcript excerpt: {ctx.transcript.excerpt}")
        else:
            facts.append(f"{label} transcript: unavailable")
        facts.append(f"{label} URL: {ctx.reference.canonical_url}")
    return facts


__all__ = [
    "YouTubeContext",
    "VideoContext",
    "VideoMetadata",
    "VideoReference",
    "TranscriptContext",
    "build",
]
