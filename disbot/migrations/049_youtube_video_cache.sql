-- 049: YouTube video metadata/transcript cache.
-- Stores fetched video metadata and transcript excerpts with TTL-based
-- expiry.  Success rows expire after 24 h; error/negative-cache rows
-- after 10 min.  Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS youtube_video_cache (
    video_id            TEXT PRIMARY KEY,
    metadata_json       JSONB NOT NULL,
    transcript_text     TEXT,
    fetch_status        TEXT NOT NULL DEFAULT 'ok'
        CHECK (fetch_status IN ('ok', 'metadata_error', 'transcript_unavailable',
                                'private_or_deleted', 'quota_limited',
                                'disabled_missing_api_key')),
    transcript_status   TEXT,
    last_error_code     TEXT,
    last_error_at       TIMESTAMPTZ,
    fetched_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at          TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS youtube_video_cache_expires
    ON youtube_video_cache (expires_at);
