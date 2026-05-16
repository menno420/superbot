-- Migration 014: Economy audit log.
--
-- Records every balance mutation routed through services.economy_service.
-- Mirrors the governance_audit_log pattern (migration 006):
--   - immutable, append-only
--   - timestamped + indexed for user-history queries
--   - signed delta so credits and debits share one row shape
--
-- Additive only — no existing table modified, no existing data
-- migrated.  Rollback by dropping the table; no downstream readers
-- yet exist as of this migration.

CREATE TABLE IF NOT EXISTS economy_audit_log (
    id          BIGINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    guild_id    BIGINT      NOT NULL,
    user_id     BIGINT      NOT NULL,
    -- actor_id: invoking member when known; NULL for system / scheduled
    actor_id    BIGINT,
    -- delta: positive = credit, negative = debit
    delta       BIGINT      NOT NULL,
    new_balance BIGINT      NOT NULL,
    -- short reason string ("daily", "work:carpenter", "blackjack:win", …).
    reason      TEXT
);

CREATE INDEX IF NOT EXISTS idx_economy_audit_user
    ON economy_audit_log (guild_id, user_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_economy_audit_actor
    ON economy_audit_log (guild_id, actor_id, occurred_at DESC)
    WHERE actor_id IS NOT NULL;
