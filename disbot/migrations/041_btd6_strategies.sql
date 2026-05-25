-- Migration 041: BTD6 strategy memory + audit (M4).
--
-- ``btd6_strategies`` is the searchable store; ``btd6_strategy_audit``
-- records every state transition so AI-approved guild rows and
-- staff-published rows are both reversible.
--
-- Retention rules (enforced by ``btd6_strategy_mutation`` +
-- ``disbot/guild_lifecycle.py``):
--   - visibility='guild' rows are deleted on guild leave.
--   - visibility='published' rows are RETAINED after the origin
--     guild leaves. current_guild_id flips to NULL but
--     origin_guild_id and origin_metadata are preserved for
--     attribution.
--   - submitter_identity_state transitions ('present' →
--     'anonymized' → 'deleted') happen via the mutation service.
--     submitted_by is nullable so anonymisation clears identity
--     attribution without forcing the row out of the table.
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS btd6_strategies (
    id                              BIGSERIAL PRIMARY KEY,
    origin_guild_id                 BIGINT NOT NULL,
    current_guild_id                BIGINT NULL,
    visibility                      TEXT NOT NULL
        CHECK (visibility IN ('guild', 'published')),
    approval_status                 TEXT NOT NULL
        CHECK (approval_status IN ('draft', 'pending', 'approved',
                                   'rejected', 'unpublished')),
    approved_by                     TEXT NULL
        CHECK (approved_by IN ('ai', 'staff')),
    approved_by_id                  BIGINT NULL,
    approval_provider               TEXT NULL,
    approval_model                  TEXT NULL,
    title                           TEXT NOT NULL,
    summary                         TEXT NOT NULL,
    map                             TEXT NULL,
    mode                            TEXT NULL,
    difficulty                      TEXT NULL,
    hero                            TEXT NULL,
    towers                          JSONB NOT NULL DEFAULT '[]'::jsonb,
    upgrade_paths                   JSONB NOT NULL DEFAULT '[]'::jsonb,
    round_range                     JSONB NULL,
    steps                           JSONB NOT NULL DEFAULT '[]'::jsonb,
    common_failures                 JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_links                    JSONB NOT NULL DEFAULT '[]'::jsonb,
    submitted_by                    BIGINT NULL,
    submitter_display_snapshot      TEXT NULL,
    submitter_identity_state        TEXT NOT NULL DEFAULT 'present'
        CHECK (submitter_identity_state IN ('present', 'anonymized', 'deleted')),
    origin_metadata                 JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version                         INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS btd6_strategies_origin_guild_idx
    ON btd6_strategies (origin_guild_id);

CREATE INDEX IF NOT EXISTS btd6_strategies_current_guild_idx
    ON btd6_strategies (current_guild_id)
    WHERE current_guild_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS btd6_strategies_visibility_idx
    ON btd6_strategies (visibility, approval_status);

CREATE INDEX IF NOT EXISTS btd6_strategies_map_mode_idx
    ON btd6_strategies (map, mode, difficulty)
    WHERE map IS NOT NULL;

CREATE TABLE IF NOT EXISTS btd6_strategy_audit (
    id            BIGSERIAL PRIMARY KEY,
    strategy_id   BIGINT NOT NULL REFERENCES btd6_strategies(id)
                                 ON DELETE CASCADE,
    actor_kind    TEXT NOT NULL
        CHECK (actor_kind IN ('user', 'ai', 'staff', 'system')),
    actor_id      BIGINT NULL,
    action        TEXT NOT NULL
        CHECK (action IN ('submitted', 'ai_refined', 'ai_approved',
                          'staff_approved', 'rejected', 'published',
                          'unpublished', 'reverted', 'submitter_detached',
                          'submitter_anonymized', 'submitter_deleted')),
    detail        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS btd6_strategy_audit_strategy_idx
    ON btd6_strategy_audit (strategy_id, created_at DESC);
