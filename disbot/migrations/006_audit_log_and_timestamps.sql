-- Migration 006: Governance audit log + mod_logs timestamp fix.
--
-- Part A: governance_audit_log
--   Records every governance write (set_subsystem_visibility, set_cleanup_policy)
--   with actor, before/after values, and wall-clock time. Enables rollback,
--   drift detection, and AI governance reasoning from historical state.
--
-- Part B: mod_logs.timestamp TEXT → TIMESTAMPTZ
--   Existing TEXT timestamps (ISO-8601 strings) are cast to TIMESTAMPTZ so
--   time-range queries and dashboard pagination work correctly.

-- Part A: governance audit log
CREATE TABLE IF NOT EXISTS governance_audit_log (
    id          BIGINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    guild_id    BIGINT      NOT NULL,
    actor_id    BIGINT      NOT NULL,
    action      TEXT        NOT NULL,  -- 'set_visibility' | 'set_cleanup'
    scope_type  TEXT,
    scope_id    BIGINT,
    subsystem   TEXT,
    old_value   JSONB,
    new_value   JSONB
);

CREATE INDEX IF NOT EXISTS idx_governance_audit_guild
    ON governance_audit_log (guild_id, occurred_at DESC);

-- Part B: mod_logs timestamp column migration
-- Only run if the column is still TEXT (idempotent guard via pg_typeof check).
DO $$
BEGIN
    IF (
        SELECT data_type
        FROM information_schema.columns
        WHERE table_name = 'mod_logs' AND column_name = 'timestamp'
    ) = 'text' THEN
        ALTER TABLE mod_logs
            ALTER COLUMN timestamp TYPE TIMESTAMPTZ
            USING timestamp::TIMESTAMPTZ;
        ALTER TABLE mod_logs
            ALTER COLUMN timestamp SET DEFAULT NOW();
    END IF;
END $$;
