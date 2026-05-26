-- 048: BTD6 ingestion run audit table.
-- Tracks every fetch-parse-store cycle so operators can diagnose
-- freshness, skipped sources, and stale running rows from crashed
-- supervisors.  Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS btd6_ingestion_runs (
    id                  BIGSERIAL PRIMARY KEY,
    source_key          TEXT NOT NULL,
    status              TEXT NOT NULL
        CHECK (status IN ('running', 'ok', 'fetch_error', 'parse_error',
                          'store_error', 'skipped', 'disabled', 'interrupted')),
    triggered_by        TEXT NOT NULL
        CHECK (triggered_by IN ('scheduled', 'manual', 'dependency')),
    started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at         TIMESTAMPTZ,
    duration_ms         INT,
    status_code         INT,
    fact_count          INT,
    raw_body_hash       TEXT,
    path_params_hash    TEXT,
    attempt             INT NOT NULL DEFAULT 1,
    started_by_user_id  BIGINT,
    error_code          TEXT,
    error_message       TEXT,
    path_params_json    JSONB
);

CREATE INDEX IF NOT EXISTS btd6_ingestion_runs_source
    ON btd6_ingestion_runs (source_key, started_at DESC);

CREATE INDEX IF NOT EXISTS btd6_ingestion_runs_status
    ON btd6_ingestion_runs (status, started_at DESC);
