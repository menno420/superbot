-- Migration 025: feature_flag_audit (Phase 2d, PR-3).
--
-- Append-only audit log for every mutation that flows through
-- :class:`services.rollout_mutation.RolloutMutationPipeline`.  One row
-- per state change.  Rollback is a NEW audit row, never an UPDATE.
--
-- Three mutation types are recorded:
--
--   * ``set_state``    — write to feature_flag_global_overrides or
--                        feature_flag_guild_overrides.  ``scope`` +
--                        ``guild_id`` discriminate which row was
--                        affected; ``prev_state`` / ``new_state``
--                        carry the transition.
--   * ``set_rollout_percent`` — change to
--                        feature_flag_global_overrides.rollout_percent.
--                        ``prev_rollout_percent`` / ``new_rollout_percent``
--                        carry the transition; state columns repeat
--                        the current state for context.
--   * ``set_tier``     — change to environment_tiers.tier.  ``flag_name``
--                        is set to the literal ``'__environment_tier__'``
--                        so the audit table can host all three event
--                        sources without a second table.
--
-- Schema decisions:
--
--   * ``mutation_type`` and ``scope`` CHECK literals mirror the Python
--     constants in :mod:`services.rollout_mutation`.  Alignment test
--     ``tests/unit/invariants/test_feature_flag_audit_alignment.py``
--     pins them.
--   * ``actor_id`` is nullable — system writes (CI seeds, scripted
--     ops) record actor_type='system' with actor_id=NULL.
--   * Indexed on (flag_name, at) for per-flag history and
--     (guild_id, at) for per-guild history.  ``mutation_id`` indexed
--     for cross-pipeline correlation.
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS feature_flag_audit (
    id                     BIGSERIAL    PRIMARY KEY,
    mutation_id            UUID         NOT NULL,
    flag_name              TEXT         NOT NULL,
    scope                  TEXT         NOT NULL,
    guild_id               BIGINT,
    prev_state             TEXT,
    new_state              TEXT,
    prev_rollout_percent   INTEGER,
    new_rollout_percent    INTEGER,
    prev_tier              TEXT,
    new_tier               TEXT,
    actor_id               BIGINT,
    actor_type             TEXT         NOT NULL DEFAULT 'platform_owner',
    mutation_type          TEXT         NOT NULL,
    at                     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CHECK (scope IN ('global', 'guild')),
    CHECK (mutation_type IN
        ('set_state', 'set_rollout_percent', 'set_tier')),
    CHECK (actor_type IN
        ('platform_owner', 'system', 'backfill'))
);

CREATE INDEX IF NOT EXISTS idx_feature_flag_audit_flag_at
    ON feature_flag_audit (flag_name, at);

CREATE INDEX IF NOT EXISTS idx_feature_flag_audit_guild_at
    ON feature_flag_audit (guild_id, at);

CREATE INDEX IF NOT EXISTS idx_feature_flag_audit_mutation
    ON feature_flag_audit (mutation_id);
