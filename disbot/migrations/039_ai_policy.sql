-- Migration 039: AI Platform policy + decision audit (M2).
--
-- Lands the typed runtime source of truth for the AI subsystem and
-- backfills M1's scalar settings into it. After this migration runs,
-- ai_natural_language_policy reads from these tables; the M1
-- guild_settings scalars become presentation/backcompat only.
--
-- Tables (created in dependency order so the FK targets exist):
--   1. ai_instruction_profile  — free-text instruction bodies
--   2. ai_guild_policy         — per-guild scalars, FKs profile id
--   3. ai_channel_policy       — sparse per-channel overrides
--   4. ai_category_policy      — sparse per-category overrides
--   5. ai_role_policy          — flexible admin role allow/deny
--   6. ai_decision_audit       — persistent reply-attempt audit
--
-- The audit_log_channel binding is NOT migrated here — it stays in
-- subsystem_bindings under the M1 BindingSpec (single source of truth).
--
-- Forward-only and idempotent.

-- 1) Instruction profiles ----------------------------------------------------

CREATE TABLE IF NOT EXISTS ai_instruction_profile (
    id              BIGSERIAL PRIMARY KEY,
    guild_id        BIGINT NULL,
    name            TEXT    NOT NULL,
    body            TEXT    NOT NULL,
    scope           TEXT    NOT NULL
        CHECK (scope IN ('guild', 'channel', 'category', 'feature', 'system')),
    feature_key     TEXT    NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      BIGINT  NULL,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (guild_id, scope, name)
);

CREATE INDEX IF NOT EXISTS ai_instruction_profile_guild_idx
    ON ai_instruction_profile (guild_id) WHERE guild_id IS NOT NULL;

-- 2) Per-guild policy --------------------------------------------------------

CREATE TABLE IF NOT EXISTS ai_guild_policy (
    guild_id                       BIGINT PRIMARY KEY,
    enabled                        BOOLEAN NOT NULL DEFAULT FALSE,
    natural_language_enabled       BOOLEAN NOT NULL DEFAULT FALSE,
    default_provider               TEXT    NOT NULL DEFAULT 'deterministic',
    default_model                  TEXT    NOT NULL DEFAULT '',
    minimum_level_default          INTEGER NOT NULL DEFAULT 2,
    cooldown_seconds               INTEGER NOT NULL DEFAULT 30,
    fresh_user_mention_allowance   INTEGER NOT NULL DEFAULT 1,
    guild_instruction_profile_id   BIGINT  NULL
        REFERENCES ai_instruction_profile(id) ON DELETE SET NULL,
    generation                     BIGINT  NOT NULL DEFAULT 0,
    updated_at                     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by                     BIGINT  NULL
);

-- 3) Per-channel override ----------------------------------------------------

CREATE TABLE IF NOT EXISTS ai_channel_policy (
    guild_id                       BIGINT NOT NULL,
    channel_id                     BIGINT NOT NULL,
    mode                           TEXT   NOT NULL
        CHECK (mode IN ('inherit', 'always_reply', 'mention_only', 'disabled')),
    min_level                      INTEGER NULL,
    cooldown_seconds               INTEGER NULL,
    instruction_profile_id         BIGINT  NULL
        REFERENCES ai_instruction_profile(id) ON DELETE SET NULL,
    updated_at                     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by                     BIGINT  NULL,
    PRIMARY KEY (guild_id, channel_id)
);

CREATE INDEX IF NOT EXISTS ai_channel_policy_guild_idx
    ON ai_channel_policy (guild_id);

-- 4) Per-category override ---------------------------------------------------

CREATE TABLE IF NOT EXISTS ai_category_policy (
    guild_id                       BIGINT NOT NULL,
    category_id                    BIGINT NOT NULL,
    mode                           TEXT   NOT NULL
        CHECK (mode IN ('inherit', 'always_reply', 'mention_only', 'disabled')),
    min_level                      INTEGER NULL,
    cooldown_seconds               INTEGER NULL,
    instruction_profile_id         BIGINT  NULL
        REFERENCES ai_instruction_profile(id) ON DELETE SET NULL,
    updated_at                     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by                     BIGINT  NULL,
    PRIMARY KEY (guild_id, category_id)
);

CREATE INDEX IF NOT EXISTS ai_category_policy_guild_idx
    ON ai_category_policy (guild_id);

-- 5) Role policy -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ai_role_policy (
    guild_id                       BIGINT NOT NULL,
    role_id                        BIGINT NOT NULL,
    decision                       TEXT   NOT NULL
        CHECK (decision IN ('allow', 'deny', 'inherit')),
    min_level_override             INTEGER NULL,
    bypass_cooldown                BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by                     BIGINT  NULL,
    PRIMARY KEY (guild_id, role_id)
);

CREATE INDEX IF NOT EXISTS ai_role_policy_guild_idx
    ON ai_role_policy (guild_id);

-- 6) Decision audit ----------------------------------------------------------
-- reason_code is NOT NULL; success rows (decision IN ('allowed','replied'))
-- use the sentinel 'none'. Denial rows use a PolicyDenialReason enum value.

CREATE TABLE IF NOT EXISTS ai_decision_audit (
    id                              BIGSERIAL PRIMARY KEY,
    guild_id                        BIGINT NOT NULL,
    channel_id                      BIGINT NOT NULL,
    category_id                     BIGINT NULL,
    user_id                         BIGINT NOT NULL,
    message_id                      BIGINT NULL,
    task                            TEXT   NULL,
    route                           TEXT   NULL,
    decision                        TEXT   NOT NULL
        CHECK (decision IN ('allowed', 'denied', 'skipped', 'replied',
                            'degraded', 'errored')),
    reason_code                     TEXT   NOT NULL,
    policy_snapshot_hash            TEXT   NULL,
    instruction_profile_ids         BIGINT[] NULL,
    provider                        TEXT   NULL,
    model                           TEXT   NULL,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at                      TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ai_decision_audit_guild_idx
    ON ai_decision_audit (guild_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ai_decision_audit_channel_idx
    ON ai_decision_audit (guild_id, channel_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ai_decision_audit_user_idx
    ON ai_decision_audit (guild_id, user_id, created_at DESC);

-- 7) Backfill ---------------------------------------------------------------
-- For every guild that has set any M1 AI scalar, upsert ai_guild_policy
-- and (if non-empty) create the matching ai_instruction_profile.
-- Wrapped in a DO block so the migration is idempotent.

DO $$
DECLARE
    rec RECORD;
    profile_id BIGINT;
    body TEXT;
BEGIN
    FOR rec IN
        SELECT DISTINCT guild_id
        FROM guild_settings
        WHERE key IN (
            'ai_enabled',
            'ai_natural_language_enabled',
            'ai_default_provider',
            'ai_default_model',
            'ai_minimum_level_default',
            'ai_cooldown_seconds',
            'ai_fresh_user_mention_allowance',
            'ai_guild_instruction_profile'
        )
    LOOP
        SELECT value INTO body
        FROM guild_settings
        WHERE guild_id = rec.guild_id
          AND key = 'ai_guild_instruction_profile';

        profile_id := NULL;
        IF body IS NOT NULL AND body <> '' THEN
            INSERT INTO ai_instruction_profile (
                guild_id, name, body, scope
            ) VALUES (
                rec.guild_id, 'default', body, 'guild'
            )
            ON CONFLICT (guild_id, scope, name)
            DO UPDATE SET body = EXCLUDED.body, updated_at = NOW()
            RETURNING id INTO profile_id;
        END IF;

        INSERT INTO ai_guild_policy (
            guild_id,
            enabled,
            natural_language_enabled,
            default_provider,
            default_model,
            minimum_level_default,
            cooldown_seconds,
            fresh_user_mention_allowance,
            guild_instruction_profile_id,
            generation,
            updated_at
        )
        SELECT
            rec.guild_id,
            COALESCE((SELECT value FROM guild_settings
                      WHERE guild_id = rec.guild_id
                        AND key = 'ai_enabled'), 'false') IN ('true','True','1'),
            COALESCE((SELECT value FROM guild_settings
                      WHERE guild_id = rec.guild_id
                        AND key = 'ai_natural_language_enabled'), 'false')
                IN ('true','True','1'),
            COALESCE((SELECT value FROM guild_settings
                      WHERE guild_id = rec.guild_id
                        AND key = 'ai_default_provider'), 'deterministic'),
            COALESCE((SELECT value FROM guild_settings
                      WHERE guild_id = rec.guild_id
                        AND key = 'ai_default_model'), ''),
            COALESCE(NULLIF((SELECT value FROM guild_settings
                             WHERE guild_id = rec.guild_id
                               AND key = 'ai_minimum_level_default'), '')::INT, 2),
            COALESCE(NULLIF((SELECT value FROM guild_settings
                             WHERE guild_id = rec.guild_id
                               AND key = 'ai_cooldown_seconds'), '')::INT, 30),
            COALESCE(NULLIF((SELECT value FROM guild_settings
                             WHERE guild_id = rec.guild_id
                               AND key = 'ai_fresh_user_mention_allowance'),
                            '')::INT, 1),
            profile_id,
            0,
            NOW()
        ON CONFLICT (guild_id) DO UPDATE SET
            enabled                      = EXCLUDED.enabled,
            natural_language_enabled     = EXCLUDED.natural_language_enabled,
            default_provider             = EXCLUDED.default_provider,
            default_model                = EXCLUDED.default_model,
            minimum_level_default        = EXCLUDED.minimum_level_default,
            cooldown_seconds             = EXCLUDED.cooldown_seconds,
            fresh_user_mention_allowance = EXCLUDED.fresh_user_mention_allowance,
            guild_instruction_profile_id = COALESCE(
                EXCLUDED.guild_instruction_profile_id,
                ai_guild_policy.guild_instruction_profile_id
            ),
            generation                   = ai_guild_policy.generation + 1,
            updated_at                   = NOW();
    END LOOP;
END $$;
