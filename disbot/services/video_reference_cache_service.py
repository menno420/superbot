"""Video reference cache service — thin layer over youtube_video_cache DB helper.

No raw SQL in this module; all DB access goes through utils.db.youtube_video_cache.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from utils.db import youtube_video_cache as _db

_CACHE_TTL_OK_S: int = 86_400
_CACHE_TTL_ERROR_S: int = 600


@dataclass(frozen=True)
class CachedVideoEntry:
    video_id: str
    metadata_json: dict
    transcript_text: str | None
    fetch_status: str
    fetched_at: datetime
    expires_at: datetime


async def get_cached(video_id: str) -> CachedVideoEntry | None:
    row = await _db.get_video_cache(video_id)
    if row is None:
        return None
    return CachedVideoEntry(
        video_id=row["video_id"],
        metadata_json=row["metadata_json"],
        transcript_text=row["transcript_text"],
        fetch_status=row["fetch_status"],
        fetched_at=row["fetched_at"],
        expires_at=row["expires_at"],
    )


async def put_cached(
    video_id: str,
    metadata: dict,
    transcript_text: str | None,
    *,
    fetch_status: str = "ok",
    last_error_code: str | None = None,
) -> None:
    """Persist a cache row.

    **Data-minimisation contract (P0-2 / Q-0099):** ``metadata`` MUST be the
    *bounded projection* (the small set of fields surfaced to AI facts), never
    the raw YouTube provider payload — projection happens in the caller
    (:func:`services.youtube_context_service._project_metadata`).  This module
    is provider-shape-agnostic and stores whatever bounded dict it is given.
    """
    ttl_s = _CACHE_TTL_OK_S if fetch_status == "ok" else _CACHE_TTL_ERROR_S
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_s)
    await _db.upsert_video_cache(
        video_id=video_id,
        metadata_json=metadata,
        transcript_text=transcript_text,
        fetch_status=fetch_status,
        transcript_status=None if transcript_text else "unavailable",
        last_error_code=last_error_code,
        last_error_at=datetime.now(timezone.utc) if last_error_code else None,
        expires_at=expires_at,
    )


async def purge_expired() -> int:
    """Physically delete expired cache rows; return the number removed.

    Retention enforcement (P0-2 / Q-0099): reads already ignore expired rows,
    but the content (transcript excerpts + metadata) lingered in storage until
    this is called.  The media-maintenance loop owns the schedule.
    """
    return await _db.purge_expired_video_cache()


__all__ = ["CachedVideoEntry", "get_cached", "put_cached", "purge_expired"]
