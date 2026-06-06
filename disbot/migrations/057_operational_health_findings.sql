-- Migration 057: persistent operational-health findings (bot-awareness PR6).
--
-- The health read model (services/health_snapshot_service.py) is purely
-- in-memory: a restart loses every finding and there is no way to see that the
-- same problem has recurred across boots. This migration adds the durable store
-- the SOLE writer (services/health_findings_service.py) records into.
--
-- Schema
-- ------
-- operational_health_findings — one row per fingerprint (the natural dedupe key
--   and per-fingerprint cap). ``status`` tracks lifecycle (open on first sight,
--   resolved/ignored by an operator later); ``occurrence_count`` accumulates
--   across boots via the writer's ON CONFLICT upsert. Detail fields mirror
--   services.health_contracts.OperationalHealthFinding (already scrubbed of
--   secrets/IDs/traces before they reach here).
-- operational_health_finding_aggregates — survives retention: when a resolved/
--   ignored row is pruned after its TTL, its occurrence counter is rolled up
--   here first, so long-run history is bounded-detail but never lost.
--
-- Retention (D8/D11): open findings are retained; resolved/ignored detail is
-- pruned after 30 days (rolled up to the aggregates table first). Enforced by
-- services.health_findings_service.run_retention(), not by the DB.
--
-- Ownership: the read-model service owns NO table; this table belongs to
-- health_findings_service (pinned by
-- tests/unit/invariants/test_inv_health_findings_service.py). No new EventBus
-- events — recording is observed via Prometheus counters only.
--
-- Rollback
-- --------
-- DROP TABLE IF EXISTS operational_health_finding_aggregates;
-- DROP TABLE IF EXISTS operational_health_findings;
-- (Reverting the consuming code without this is harmless — the tables are
-- simply unwritten/unread.)
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS operational_health_findings (
    fingerprint         TEXT PRIMARY KEY,
    status              TEXT NOT NULL DEFAULT 'open'
                            CHECK (status IN ('open', 'resolved', 'ignored')),
    severity            TEXT NOT NULL
                            CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    category            TEXT NOT NULL,
    message             TEXT NOT NULL,
    related_subsystem   TEXT,
    related_command     TEXT,
    related_provider    TEXT,
    file_hint           TEXT,
    suggested_next_step TEXT,
    occurrence_count    BIGINT NOT NULL DEFAULT 1,
    first_seen_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    source              TEXT NOT NULL DEFAULT 'unknown',
    last_session_id     TEXT,
    last_snapshot_id    TEXT
);

CREATE INDEX IF NOT EXISTS ix_health_findings_status_last_seen
    ON operational_health_findings (status, last_seen_at);

CREATE TABLE IF NOT EXISTS operational_health_finding_aggregates (
    fingerprint        TEXT PRIMARY KEY,
    category           TEXT NOT NULL,
    severity           TEXT NOT NULL,
    total_occurrences  BIGINT NOT NULL DEFAULT 0,
    first_seen_at      TIMESTAMPTZ,
    last_seen_at       TIMESTAMPTZ
);
