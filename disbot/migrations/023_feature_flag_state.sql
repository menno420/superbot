-- Migration 023: feature_flag_state — global + guild overrides (Phase 2d, PR-2).
--
-- Storage for the Phase 2d feature-flag evaluator.  Two tables instead of
-- one nullable-PK table because PostgreSQL does not allow NULL in any
-- PRIMARY KEY column.  Separating the surfaces also keeps SQL queries
-- unambiguous: the evaluator's resolution order is explicit ("look up the
-- guild row; on miss look up the global row").
--
-- Resolution order (consumed by core.runtime.feature_flags.is_enabled):
--   1. emergency env override (SUPERBOT_FF_<FLAG>)
--   2. if feature_flag.primary is OFF: declared default (DB bypassed)
--   3. per-guild row (feature_flag_guild_overrides)
--   4. global row (feature_flag_global_overrides)
--   5. environment-tier policy match (RolloutPolicy.tier_gate)
--   6. deterministic rollout hash (RolloutPolicy.percentage_rollout)
--   7. declared default
--
-- Both tables are READ-ONLY in this PR — writes land in PR-3 alongside
-- the RolloutMutationPipeline + feature_flag_audit table.  Until then,
-- operators seed rows manually for canary/owner-tier validation.
--
-- Schema decisions:
--
--   * ``state`` is a CHECK-constrained enum mirroring Python's logical
--     levels.  ``'on'`` and ``'off'`` are hard overrides; the tier names
--     (``owner``, ``canary``, ``beta``, ``production``) are convenience
--     values evaluated against the guild's environment tier.
--   * ``rollout_percent`` only meaningful on the global row.  Per-guild
--     rows are a binary override and ignore rollout.
--   * ``set_by`` is nullable for system writes (backfill, migration).
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS feature_flag_global_overrides (
    flag_name        TEXT         NOT NULL PRIMARY KEY,
    state            TEXT         NOT NULL,
    rollout_percent  INTEGER,
    set_by           BIGINT,
    set_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CHECK (state IN ('off', 'owner', 'canary', 'beta', 'production', 'on')),
    CHECK (rollout_percent IS NULL
           OR (rollout_percent BETWEEN 0 AND 100))
);

CREATE TABLE IF NOT EXISTS feature_flag_guild_overrides (
    flag_name        TEXT         NOT NULL,
    guild_id         BIGINT       NOT NULL,
    state            TEXT         NOT NULL,
    set_by           BIGINT,
    set_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (flag_name, guild_id),
    CHECK (state IN ('off', 'owner', 'canary', 'beta', 'production', 'on'))
);

CREATE INDEX IF NOT EXISTS idx_feature_flag_guild_overrides_guild
    ON feature_flag_guild_overrides (guild_id);
