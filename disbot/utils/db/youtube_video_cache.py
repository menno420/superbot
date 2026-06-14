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


async def get_cache_stats() -> dict[str, Any]:
    """Return a **content-free** aggregate health snapshot of the cache table.

    Content-free contract (P0-2 / Q-0099 follow-up): this query selects **no
    content columns** — no ``metadata_json``, ``transcript_text``, ``video_id``,
    title/description/etc.  ``with_transcript_rows`` is a ``COUNT(*) FILTER``
    over a ``transcript_text IS NOT NULL`` predicate, which reads the column for
    a null-check and returns only an integer; no transcript content leaves the
    database.  The result is purely counts + row timestamps for the
    ``!platform media`` operator diagnostic.
    """
    row = await pool.get().fetchrow(
        """
        SELECT
            count(*)                                          AS total_rows,
            count(*) FILTER (WHERE expires_at <= now())       AS expired_rows,
            count(*) FILTER (WHERE fetch_status = 'ok')       AS ok_rows,
            count(*) FILTER (WHERE fetch_status <> 'ok')      AS error_rows,
            count(*) FILTER (WHERE transcript_text IS NOT NULL) AS with_transcript_rows,
            min(fetched_at)                                   AS oldest_fetched_at,
            max(fetched_at)                                   AS newest_fetched_at,
            min(expires_at) FILTER (WHERE expires_at > now()) AS next_expiry_at
        FROM youtube_video_cache
        """,
    )
    return dict(row) if row else {}
