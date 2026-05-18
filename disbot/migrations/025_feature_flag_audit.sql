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
-- Per-``mutation_type`` shape (defense-in-depth via CHECK constraints).
-- These complement the pipeline-level validation; even a future caller
-- that bypasses :class:`RolloutMutationPipeline` cannot insert a
-- mis-shaped audit row.
--
--   * ``set_state`` rows: ``new_state`` must be non-null; ``flag_name``
--     must NOT be the environment-tier sentinel; tier columns must be
--     NULL.
--   * ``set_rollout_percent`` rows: ``new_rollout_percent`` must be
--     non-null; ``scope`` must be ``'global'``; ``flag_name`` must NOT
--     be the sentinel; tier columns must be NULL.
--   * ``set_tier`` rows: ``flag_name`` must be the sentinel literal
--     ``'__environment_tier__'``; ``scope`` must be ``'guild'``;
--     ``guild_id`` must be non-null; ``new_tier`` must be non-null;
--     state and rollout columns must be NULL.
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
        ('platform_owner', 'system', 'backfill')),
    -- set_state rows must carry a non-null new_state, must NOT use the
    -- environment-tier sentinel flag_name, and must leave tier columns
    -- unset.
    CHECK (
        mutation_type <> 'set_state' OR (
            new_state IS NOT NULL
            AND flag_name <> '__environment_tier__'
            AND prev_tier IS NULL
            AND new_tier IS NULL
        )
    ),
    -- set_rollout_percent rows are global-scoped, carry a non-null
    -- new_rollout_percent, must not use the sentinel, and leave tier
    -- columns unset.
    CHECK (
        mutation_type <> 'set_rollout_percent' OR (
            scope = 'global'
            AND guild_id IS NULL
            AND new_rollout_percent IS NOT NULL
            AND flag_name <> '__environment_tier__'
            AND prev_tier IS NULL
            AND new_tier IS NULL
        )
    ),
    -- set_tier rows use the sentinel flag_name, are guild-scoped with
    -- non-null guild_id and new_tier, and leave state + rollout
    -- columns unset.  This is the explicit contract that lets the
    -- single audit table host all three event sources.
    CHECK (
        mutation_type <> 'set_tier' OR (
            flag_name = '__environment_tier__'
            AND scope = 'guild'
            AND guild_id IS NOT NULL
            AND new_tier IS NOT NULL
            AND prev_state IS NULL
            AND new_state IS NULL
            AND prev_rollout_percent IS NULL
            AND new_rollout_percent IS NULL
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_feature_flag_audit_flag_at
    ON feature_flag_audit (flag_name, at);

CREATE INDEX IF NOT EXISTS idx_feature_flag_audit_guild_at
    ON feature_flag_audit (guild_id, at);

CREATE INDEX IF NOT EXISTS idx_feature_flag_audit_mutation
    ON feature_flag_audit (mutation_id);
