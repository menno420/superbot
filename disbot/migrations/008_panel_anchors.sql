-- Migration 008: Panel anchor persistence.
--
-- panel_anchors stores Discord message IDs so the runtime layer can find
-- and edit existing panel messages instead of sending new ones on each command.
--
-- The UNIQUE constraint on (user_id, channel_id, subsystem) enforces the
-- platform invariant: one active panel per user per channel per subsystem.
-- is_stale marks anchors whose Discord message was deleted; GC prunes them.

CREATE TABLE IF NOT EXISTS panel_anchors (
    anchor_id       UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id         BIGINT      NOT NULL,
    guild_id        BIGINT      NOT NULL,
    channel_id      BIGINT      NOT NULL,
    message_id      BIGINT      NOT NULL,
    subsystem       TEXT        NOT NULL,
    is_stale        BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, channel_id, subsystem)
);

CREATE INDEX IF NOT EXISTS idx_panel_anchors_message
    ON panel_anchors (message_id)
    WHERE NOT is_stale;

CREATE INDEX IF NOT EXISTS idx_panel_anchors_guild
    ON panel_anchors (guild_id)
    WHERE NOT is_stale;
