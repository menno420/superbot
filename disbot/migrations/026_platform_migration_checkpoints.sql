-- Migration 026: platform_migration_checkpoints (Phase 2, PR-5).
--
-- Generic logical-migration checkpoint table.  Records progress of any
-- data migration / backfill / reconciliation that needs:
--
--   * a stable name (so re-runs can resume),
--   * an optional guild scope (per-guild or global),
--   * a status discriminator,
--   * a JSONB summary the operator can inspect,
--   * idempotency under repeat (same (name, guild_id) ⇒ upsert).
--
-- First consumer is :mod:`services.binding_backfill` (PR-5 dry-run +
-- PR-6 write phase).  Subsequent logical migrations register their
-- own ``name`` literals; the table is intentionally generic so a
-- second backfill (e.g. participation data shape changes in PR-9) can
-- reuse it without a new table.
--
-- Schema decisions:
--
--   * ``guild_id`` is nullable to allow a single GLOBAL checkpoint per
--     migration ``name`` (e.g. "binding_backfill" overview row).
--     PostgreSQL does not allow NULL in primary-key columns, so we
--     use a serial ``id`` PK plus two partial unique indexes:
--       - ``(name) WHERE guild_id IS NULL``
--       - ``(name, guild_id) WHERE guild_id IS NOT NULL``
--     This gives the same uniqueness guarantee as a composite PK
--     would without the NULL-in-PK problem.
--   * ``status`` is CHECK-constrained.  Alignment test
--     ``tests/unit/invariants/test_migration_checkpoint_alignment.py``
--     pins the literals to the Python ``Status`` enum.
--   * ``version`` is an explicit counter so a migration can be re-run
--     with a bumped version without losing the previous attempt's
--     summary (PR-6 may bump from 1 → 2 if the dry-run schema
--     changes).
--   * Indexed on (name, started_at) for time-range queries and
--     (guild_id) for guild-scoped lookups.
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS platform_migration_checkpoints (
    id              BIGSERIAL    PRIMARY KEY,
    name            TEXT         NOT NULL,
    guild_id        BIGINT,
    status          TEXT         NOT NULL,
    version         INTEGER      NOT NULL DEFAULT 1,
    started_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    summary_json    JSONB,
    CHECK (status IN (
        'pending',
        'dry_run_complete',
        'in_progress',
        'complete',
        'failed',
        'rolled_back'
    ))
);

CREATE UNIQUE INDEX IF NOT EXISTS
    idx_platform_migration_checkpoints_global_unique
    ON platform_migration_checkpoints (name)
    WHERE guild_id IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS
    idx_platform_migration_checkpoints_guild_unique
    ON platform_migration_checkpoints (name, guild_id)
    WHERE guild_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_platform_migration_checkpoints_name_started
    ON platform_migration_checkpoints (name, started_at);

CREATE INDEX IF NOT EXISTS idx_platform_migration_checkpoints_guild
    ON platform_migration_checkpoints (guild_id);
