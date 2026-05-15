-- Migration 007: Runtime session infrastructure.
--
-- Introduces the core/runtime/ layer persistence tables:
--
--   runtime_sessions    — one persistent session per (user, channel, subsystem)
--   runtime_session_state — typed key-value state owned by a session
--
-- The UNIQUE constraint on runtime_sessions enforces the platform invariant:
-- exactly one active panel per user per channel per subsystem at any time.
-- Concurrent panel creation attempts resolve to a single winner via ON CONFLICT.

CREATE TABLE IF NOT EXISTS runtime_sessions (
    session_id      UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id         BIGINT      NOT NULL,
    guild_id        BIGINT      NOT NULL,
    channel_id      BIGINT      NOT NULL,
    subsystem       TEXT        NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_active_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata        JSONB       NOT NULL DEFAULT '{}',
    UNIQUE (user_id, channel_id, subsystem)
);

CREATE INDEX IF NOT EXISTS idx_runtime_sessions_guild
    ON runtime_sessions (guild_id, subsystem);

CREATE INDEX IF NOT EXISTS idx_runtime_sessions_active
    ON runtime_sessions (last_active_at);

CREATE TABLE IF NOT EXISTS runtime_session_state (
    session_id  UUID    NOT NULL REFERENCES runtime_sessions (session_id) ON DELETE CASCADE,
    key         TEXT    NOT NULL,
    value       JSONB   NOT NULL,
    PRIMARY KEY (session_id, key)
);
