"""YouTube metadata and transcript fetcher.

Requires YOUTUBE_API_KEY env var for metadata.  Transcript fetch uses
youtube-transcript-api and does not require an API key.

A WARNING is logged once per process if YOUTUBE_API_KEY is missing.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re

import aiohttp

logger = logging.getLogger("bot.services.youtube_fetch")

_API_KEY: str | None = os.getenv("YOUTUBE_API_KEY")
_API_KEY_WARNED = False

_VIDEO_ID_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)"
    r"([A-Za-z0-9_-]{11})",
)
_BARE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")

_METADATA_URL = "https://www.googleapis.com/youtube/v3/videos"


class YouTubeFetchError(Exception):
    def __init__(self, video_id: str, reason: str, *, retryable: bool = False) -> None:
        super().__init__(f"YouTube fetch error for {video_id!r}: {reason}")
        self.video_id = video_id
        self.reason = reason
        self.retryable = retryable


def parse_video_id(url_or_id: str) -> str | None:
    """Extract 11-char video ID from a YouTube URL or bare ID string."""
    if not url_or_id:
        return None
    m = _VIDEO_ID_RE.search(url_or_id)
    if m:
        return m.group(1)
    if _BARE_ID_RE.match(url_or_id.strip()):
        return url_or_id.strip()
    return None


async def fetch_video_metadata(video_id: str) -> dict:
    """Fetch video metadata from YouTube Data API v3.

    Raises YouTubeFetchError for missing key, private/deleted video,
    or quota exceeded.
    """
    global _API_KEY_WARNED
    if not _API_KEY:
        if not _API_KEY_WARNED:
            logger.warning("YOUTUBE_API_KEY not set; YouTube metadata fetch disabled")
            _API_KEY_WARNED = True
        raise YouTubeFetchError(video_id, "youtube_api_key_missing")

    params = {
        "id": video_id,
        "key": _API_KEY,
        "part": "snippet,contentDetails",
    }
    async with (
        aiohttp.ClientSession() as session,
        session.get(
            _METADATA_URL,
            params=params,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp,
    ):
        if resp.status == 403:
            text = await resp.text()
            if "quotaExceeded" in text or "dailyLimitExceeded" in text:
                raise YouTubeFetchError(video_id, "quota_limited")
            raise YouTubeFetchError(video_id, "fetch_error")
        if resp.status != 200:
            raise YouTubeFetchError(
                video_id,
                "fetch_error",
                retryable=resp.status >= 500,
            )
        data = await resp.json()

    items = data.get("items", [])
    if not items:
        raise YouTubeFetchError(video_id, "video_private_or_deleted")
    return items[0]


async def fetch_transcript(video_id: str) -> list[dict]:
    """Fetch transcript segments for a video.

    Returns empty list if no transcript is available — never raises
    for absent transcript.  Runs the blocking API in an executor.
    """
    try:
        from youtube_transcript_api import (
            YouTubeTranscriptApi,
        )

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: YouTubeTranscriptApi.get_transcript(video_id),
        )
    except Exception:
        return []


__all__ = [
    "YouTubeFetchError",
    "parse_video_id",
    "fetch_video_metadata",
    "fetch_transcript",
]
