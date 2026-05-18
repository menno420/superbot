-- Migration 024: environment_tiers (Phase 2d, PR-2).
--
-- One row per guild mapping the guild to its deployment tier
-- (production, beta, canary, owner_guild_only, development).  The
-- feature-flag evaluator consults this table to decide whether a flag
-- whose RolloutPolicy.tier_gate is, say, BETA, is eligible for a given
-- guild.
--
-- Missing row → guild is treated as PRODUCTION (the most-restrictive
-- default).  Operators seed rows manually for canary/owner guilds.
--
-- Schema decisions:
--
--   * ``tier`` CHECK enumerates exactly the values of
--     ``core.runtime.feature_flags.EnvironmentTier``; the invariant test
--     ``tests/unit/invariants/test_environment_tier_alignment.py`` pins
--     the literals.
--   * Single-column PK — at most one tier per guild.  Reassigning is an
--     UPDATE, not an INSERT.
--   * ``set_by`` nullable for system writes (CI seed, migration).
--   * Per-guild rows are deleted on guild leave via
--     :func:`guild_lifecycle.teardown`.
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS environment_tiers (
    guild_id   BIGINT       NOT NULL PRIMARY KEY,
    tier       TEXT         NOT NULL DEFAULT 'production',
    set_by     BIGINT,
    set_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CHECK (tier IN ('production', 'beta', 'canary',
                    'owner_guild_only', 'development'))
);
