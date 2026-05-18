-- Migration 027: per-user participation tables (Phase 2c, PR-8).
--
-- Four structurally-separated tables — one per concern — owned by
-- :class:`core.runtime.participation_schema.ParticipationSchema`.  The
-- schema docstring explicitly forbids collapsing these into a single
-- "user settings" object; this migration enforces that separation at
-- the storage layer.
--
--   * user_participation         — opt-in / opt-out toggles
--   * user_subscriptions         — topic-level subscription state
--   * user_preferences           — JSONB UX preferences
--   * user_visibility_overrides  — public / hidden surface toggles
--
-- All four tables include ``guild_id`` so guild-leave teardown can
-- purge the rows for a single guild without touching the same user's
-- participation in OTHER guilds.  The composite PK on every table is
-- ``(user_id, guild_id, ...)`` so per-(user, guild) lookups are
-- O(1) index reads.
--
-- Missing-row semantics (consumed by :mod:`utils.user_config_accessors`):
--
--   user_participation         → 'not_set'        (caller interprets)
--   user_subscriptions         → schema default
--   user_preferences           → preference default
--   user_visibility_overrides  → schema default
--
-- Mutation contract (Phase 2c PR-9 adds the ParticipationMutationPipeline):
--
--   * Writes flow through :class:`services.participation_mutation.
--     ParticipationMutationPipeline` (NOT this migration).
--   * actor_id is recorded on every row so audit / authority checks
--     can resolve later.  Nullable because system writes (CI seeds,
--     future PR-9 backfills) use NULL with actor_type='system' in
--     the associated audit table (PR-9).
--
-- Forward-only and idempotent.

-- ---------------------------------------------------------------------------
-- user_participation — opt-in / opt-out per (user, guild, subsystem)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_participation (
    user_id     BIGINT       NOT NULL,
    guild_id    BIGINT       NOT NULL,
    subsystem   TEXT         NOT NULL,
    state       TEXT         NOT NULL,
    set_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    set_by      BIGINT,
    PRIMARY KEY (user_id, guild_id, subsystem),
    CHECK (state IN ('opted_in', 'opted_out'))
);

CREATE INDEX IF NOT EXISTS idx_user_participation_guild
    ON user_participation (guild_id);


-- ---------------------------------------------------------------------------
-- user_subscriptions — topic-level subscription toggles
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_subscriptions (
    user_id     BIGINT       NOT NULL,
    guild_id    BIGINT       NOT NULL,
    subsystem   TEXT         NOT NULL,
    topic       TEXT         NOT NULL,
    enabled     BOOLEAN      NOT NULL,
    set_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    set_by      BIGINT,
    PRIMARY KEY (user_id, guild_id, subsystem, topic)
);

CREATE INDEX IF NOT EXISTS idx_user_subscriptions_guild
    ON user_subscriptions (guild_id);


-- ---------------------------------------------------------------------------
-- user_preferences — JSONB UX / UI preferences
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id     BIGINT       NOT NULL,
    guild_id    BIGINT       NOT NULL,
    key         TEXT         NOT NULL,
    value       JSONB        NOT NULL,
    set_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    set_by      BIGINT,
    PRIMARY KEY (user_id, guild_id, key)
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_guild
    ON user_preferences (guild_id);


-- ---------------------------------------------------------------------------
-- user_visibility_overrides — public / hidden surface toggles
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS user_visibility_overrides (
    user_id     BIGINT       NOT NULL,
    guild_id    BIGINT       NOT NULL,
    subsystem   TEXT         NOT NULL,
    visibility  TEXT         NOT NULL,
    set_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    set_by      BIGINT,
    PRIMARY KEY (user_id, guild_id, subsystem),
    CHECK (visibility IN ('public', 'hidden'))
);

CREATE INDEX IF NOT EXISTS idx_user_visibility_overrides_guild
    ON user_visibility_overrides (guild_id);
