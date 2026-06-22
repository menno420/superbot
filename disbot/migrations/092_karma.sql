-- Migration 092: Karma (thanks/upvote reputation).
--
-- Members grant each other peer reputation through services.karma_service.
-- Two tables, mirroring the economy pattern (economy + economy_audit_log,
-- migrations 001 + 014):
--
--   karma            — per-user running totals (one row per member/guild)
--   karma_audit_log  — immutable, append-only grant history; doubles as the
--                      anti-abuse source of truth (cooldown + daily-cap queries)
--
-- Additive only — no existing table modified, no existing data migrated.
-- Rollback by dropping both tables; no downstream readers exist outside
-- services.karma_service as of this migration.

CREATE TABLE IF NOT EXISTS karma (
    user_id        BIGINT      NOT NULL,
    guild_id       BIGINT      NOT NULL,
    -- running total; clamped >= 0 at the write site (GREATEST(0, …))
    karma_points   INT         NOT NULL DEFAULT 0,
    -- lifetime grants received / given (for the karma card + abuse review)
    received_count INT         NOT NULL DEFAULT 0,
    given_count    INT         NOT NULL DEFAULT 0,
    last_received  TIMESTAMPTZ,
    PRIMARY KEY (user_id, guild_id)
);

-- Leaderboard ordering: highest karma first, oldest-received as a stable
-- tie-break so equal totals rank deterministically.
CREATE INDEX IF NOT EXISTS idx_karma_guild_points
    ON karma (guild_id, karma_points DESC, last_received ASC);

CREATE TABLE IF NOT EXISTS karma_audit_log (
    id          BIGINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    guild_id    BIGINT      NOT NULL,
    -- from_user: the granter; to_user: the recipient
    from_user   BIGINT      NOT NULL,
    to_user     BIGINT      NOT NULL,
    -- delta: +1 per grant today; signed leaves room for a future downvote
    delta       INT         NOT NULL,
    -- short source label ("command", "reaction")
    source      TEXT        NOT NULL,
    -- optional free-text reason supplied by the granter
    reason      TEXT
);

-- Recipient history (karma card) + leaderboard tie-break support.
CREATE INDEX IF NOT EXISTS idx_karma_audit_to
    ON karma_audit_log (guild_id, to_user, occurred_at DESC);

-- Anti-abuse: per-(giver) and per-(giver -> receiver) recent-grant queries
-- (cooldown + daily cap) read this index.
CREATE INDEX IF NOT EXISTS idx_karma_audit_from
    ON karma_audit_log (guild_id, from_user, occurred_at DESC);
