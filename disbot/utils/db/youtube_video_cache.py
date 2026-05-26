"""DB primitives for youtube_video_cache.

The only module that issues SQL against this table.  Service layers
above must not contain raw SQL.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from utils.db import pool


async def get_video_cache(video_id: str) -> dict[str, Any] | None:
    row = await pool.get().fetchrow(
        """
        SELECT video_id, metadata_json, transcript_text, fetch_status,
               transcript_status, last_error_code, last_error_at,
               fetched_at, expires_at
        FROM youtube_video_cache
        WHERE video_id = $1
          AND expires_at > now()
        """,
        video_id,
    )
    return dict(row) if row else None


async def upsert_video_cache(
    *,
    video_id: str,
    metadata_json: dict[str, Any],
    transcript_text: str | None,
    fetch_status: str,
    transcript_status: str | None,
    last_error_code: str | None,
    last_error_at: datetime | None,
    expires_at: datetime,
) -> None:
    await pool.get().execute(
        """
        INSERT INTO youtube_video_cache (
            video_id, metadata_json, transcript_text, fetch_status,
            transcript_status, last_error_code, last_error_at,
            fetched_at, expires_at
        ) VALUES ($1, $2::jsonb, $3, $4, $5, $6, $7, now(), $8)
        ON CONFLICT (video_id) DO UPDATE SET
            metadata_json    = EXCLUDED.metadata_json,
            transcript_text  = EXCLUDED.transcript_text,
            fetch_status     = EXCLUDED.fetch_status,
            transcript_status = EXCLUDED.transcript_status,
            last_error_code  = EXCLUDED.last_error_code,
            last_error_at    = EXCLUDED.last_error_at,
            fetched_at       = now(),
            expires_at       = EXCLUDED.expires_at
        """,
        video_id,
        json.dumps(metadata_json),
        transcript_text,
        fetch_status,
        transcript_status,
        last_error_code,
        last_error_at,
        expires_at,
    )


async def purge_expired_video_cache() -> int:
    result = await pool.get().execute(
        "DELETE FROM youtube_video_cache WHERE expires_at <= now()",
    )
    return int(result.split()[-1])
