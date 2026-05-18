-- Migration 028: user_participation_audit (Phase 2c PR-9).
--
-- Append-only audit log for every mutation that flows through
-- :class:`services.participation_mutation.ParticipationMutationPipeline`.
-- One row per mutation; rollback is a NEW row, never an UPDATE.
--
-- The single audit table hosts all four participation concerns via
-- a ``mutation_type`` discriminator:
--
--   * ``set_participation``  — writes ``user_participation`` row.
--                              Keys: ``subsystem``.
--                              Values: ``prev_state`` / ``new_state``.
--   * ``set_subscription``   — writes ``user_subscriptions`` row.
--                              Keys: ``subsystem`` + ``topic``.
--                              Values: ``prev_enabled`` / ``new_enabled``.
--   * ``set_preference``     — writes ``user_preferences`` row.
--                              Keys: ``key``.
--                              Values: ``prev_value`` / ``new_value`` (JSONB).
--   * ``set_visibility``     — writes ``user_visibility_overrides`` row.
--                              Keys: ``subsystem``.
--                              Values: ``prev_visibility`` / ``new_visibility``.
--
-- Per-``mutation_type`` shape CHECK constraints (defense-in-depth,
-- mirrors the feature_flag_audit pattern from PR-3): a future
-- caller that bypasses ``ParticipationMutationPipeline`` cannot
-- insert a mis-shaped row.  ``mutation_type='set_subscription'``
-- with a NULL ``topic`` is rejected at INSERT, etc.
--
-- Retention policy (per ``docs/platform-consistency-ledger.md`` §3):
-- audit rows are **preserved** on guild leave, matching
-- ``binding_audit_log`` and ``feature_flag_audit``.  The same user
-- re-joining a guild sees the historical trail of their prior
-- participation decisions.  Active participation rows (in the four
-- migration-027 tables) ARE purged on guild leave so re-joining
-- starts with the implicit default state.
--
-- Actor model:
--
--   * ``actor_type='user'`` — the user mutating their own state
--     (self-authorised).  ``actor_id`` MUST equal ``user_id``.
--   * ``actor_type='moderator'`` / ``'admin'`` — privileged
--     override.  Modeled here so future PRs (Discord-facing
--     commands, audit tooling) can land without a migration.
--     ``actor_id`` is the moderator/admin's snowflake.
--   * ``actor_type='system'`` — CI seeds, scripted ops.
--     ``actor_id`` may be NULL.
--   * ``actor_type='backfill'`` — reserved for future logical
--     migrations.  Currently no callers.
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS user_participation_audit (
    id                  BIGSERIAL    PRIMARY KEY,
    mutation_id         UUID         NOT NULL,
    user_id             BIGINT       NOT NULL,
    guild_id            BIGINT       NOT NULL,
    mutation_type       TEXT         NOT NULL,
    -- Per-concern key fields (vary by mutation_type)
    subsystem           TEXT,
    topic               TEXT,
    key                 TEXT,
    -- Per-concern value transitions (vary by mutation_type)
    prev_state          TEXT,
    new_state           TEXT,
    prev_enabled        BOOLEAN,
    new_enabled         BOOLEAN,
    prev_value          JSONB,
    new_value           JSONB,
    prev_visibility     TEXT,
    new_visibility      TEXT,
    actor_id            BIGINT,
    actor_type          TEXT         NOT NULL DEFAULT 'user',
    at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CHECK (mutation_type IN
        ('set_participation', 'set_subscription', 'set_preference', 'set_visibility')),
    CHECK (actor_type IN
        ('user', 'moderator', 'admin', 'system', 'backfill')),
    -- set_participation rows carry subsystem + state transition;
    -- topic/key/enabled/value/visibility columns must be NULL.
    CHECK (
        mutation_type <> 'set_participation' OR (
            subsystem IS NOT NULL
            AND new_state IS NOT NULL
            AND topic IS NULL
            AND key IS NULL
            AND prev_enabled IS NULL AND new_enabled IS NULL
            AND prev_value IS NULL AND new_value IS NULL
            AND prev_visibility IS NULL AND new_visibility IS NULL
        )
    ),
    -- set_subscription rows carry subsystem + topic + enabled transition.
    CHECK (
        mutation_type <> 'set_subscription' OR (
            subsystem IS NOT NULL
            AND topic IS NOT NULL
            AND new_enabled IS NOT NULL
            AND key IS NULL
            AND prev_state IS NULL AND new_state IS NULL
            AND prev_value IS NULL AND new_value IS NULL
            AND prev_visibility IS NULL AND new_visibility IS NULL
        )
    ),
    -- set_preference rows carry key + JSONB value transition.
    CHECK (
        mutation_type <> 'set_preference' OR (
            key IS NOT NULL
            AND new_value IS NOT NULL
            AND subsystem IS NULL
            AND topic IS NULL
            AND prev_state IS NULL AND new_state IS NULL
            AND prev_enabled IS NULL AND new_enabled IS NULL
            AND prev_visibility IS NULL AND new_visibility IS NULL
        )
    ),
    -- set_visibility rows carry subsystem + visibility transition.
    CHECK (
        mutation_type <> 'set_visibility' OR (
            subsystem IS NOT NULL
            AND new_visibility IS NOT NULL
            AND topic IS NULL
            AND key IS NULL
            AND prev_state IS NULL AND new_state IS NULL
            AND prev_enabled IS NULL AND new_enabled IS NULL
            AND prev_value IS NULL AND new_value IS NULL
        )
    ),
    -- prev_state / new_state literals match user_participation CHECK.
    CHECK (prev_state IS NULL OR prev_state IN ('opted_in', 'opted_out')),
    CHECK (new_state IS NULL OR new_state IN ('opted_in', 'opted_out')),
    -- prev_visibility / new_visibility literals match user_visibility_overrides CHECK.
    CHECK (prev_visibility IS NULL OR prev_visibility IN ('public', 'hidden')),
    CHECK (new_visibility IS NULL OR new_visibility IN ('public', 'hidden'))
);

CREATE INDEX IF NOT EXISTS idx_user_participation_audit_user_guild_at
    ON user_participation_audit (user_id, guild_id, at);

CREATE INDEX IF NOT EXISTS idx_user_participation_audit_guild_at
    ON user_participation_audit (guild_id, at);

CREATE INDEX IF NOT EXISTS idx_user_participation_audit_mutation
    ON user_participation_audit (mutation_id);
