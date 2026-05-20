-- Migration 032: automation_rules (Phase 9g / Track 6 PR 15).
--
-- Per-guild rule store for the automation substrate. Each row is
-- one operator-configured behaviour: "post a welcome message when a
-- new member joins", "post a weekly readiness summary", "give
-- @veteran to anyone with 30 days of activity", etc.
--
-- The substrate is deliberately generic. Specific behaviours land
-- as named ``trigger_kind`` / ``action_kind`` rows; the executor
-- (Track 6 PR 17) dispatches per ``action_kind``.
--
-- Schema
-- ------
-- id                      BIGSERIAL primary key (used by FK from
--                         ``automation_runs``).
-- guild_id                Discord guild id.
-- name                    Operator-assigned label; unique per guild
--                         so the operator can refer to a rule by
--                         name in commands.
-- enabled                 Master switch. Defaults FALSE so a freshly-
--                         created rule never runs until the operator
--                         explicitly turns it on.
-- trigger_kind            One of the documented kinds (see CHECK).
-- trigger_config          JSONB; trigger-specific parameters
--                         (schedule string, threshold, etc.).
-- action_kind             One of the documented kinds (see CHECK).
-- action_config           JSONB; action-specific parameters
--                         (template, target role id, etc.).
-- schedule                Optional cron-like schedule string. Set
--                         when ``trigger_kind = 'scheduled_time'``;
--                         interpreted by the scheduler (Track 6
--                         PR 18).
-- timezone                IANA timezone for ``schedule``. Defaults
--                         to UTC.
-- last_run_at             Timestamp of the most recent execution
--                         attempt (success or failure). NULL until
--                         the executor first picks the rule up.
-- next_run_at             Computed next-run timestamp. Indexed for
--                         the scheduler's "due rules" query.
-- failure_count           Consecutive failures since the last
--                         success. The scheduler auto-disables a
--                         rule when this exceeds the threshold
--                         (5 by default).
-- last_error              Exception text from the most recent
--                         failed run; truncated by the executor.
-- created_by              Discord user id of the operator who
--                         created the rule.
-- created_at / updated_at Bookkeeping; ``updated_at`` is bumped by
--                         every mutation pipeline write.
--
-- CHECK constraints mirror the documented trigger / action kind
-- enums so a future code change that adds a kind must also bump
-- this migration.
--
-- Indexes
-- -------
-- * ``UNIQUE (guild_id, name)`` — operator references rules by
--   name within a guild.
-- * Partial index on ``next_run_at`` for enabled rules — the
--   scheduler's hot path.
--
-- Rollback
-- --------
-- ``DROP TABLE IF EXISTS automation_rules CASCADE`` removes the
-- table and its dependent ``automation_runs`` rows (migration 033
-- declares ``ON DELETE CASCADE``).
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS automation_rules (
    id              BIGSERIAL    PRIMARY KEY,
    guild_id        BIGINT       NOT NULL,
    name            TEXT         NOT NULL,
    enabled         BOOLEAN      NOT NULL DEFAULT FALSE,
    trigger_kind    TEXT         NOT NULL CHECK (
        trigger_kind IN (
            'scheduled_time',
            'interval',
            'member_join',
            'setup_readiness_below',
            'binding_missing',
            'channel_inactive',
            'manual'
        )
    ),
    trigger_config  JSONB        NOT NULL DEFAULT '{}'::JSONB,
    action_kind     TEXT         NOT NULL CHECK (
        action_kind IN (
            'send_message',
            'assign_role',
            'remove_role',
            'post_readiness_summary',
            'post_leaderboard_summary',
            'bind_channel',
            'create_channel',
            'notify_owner'
        )
    ),
    action_config   JSONB        NOT NULL DEFAULT '{}'::JSONB,
    schedule        TEXT,
    timezone        TEXT         NOT NULL DEFAULT 'UTC',
    last_run_at     TIMESTAMPTZ,
    next_run_at     TIMESTAMPTZ,
    failure_count   INT          NOT NULL DEFAULT 0,
    last_error      TEXT,
    created_by      BIGINT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (guild_id, name)
);

CREATE INDEX IF NOT EXISTS automation_rules_next_run_idx
    ON automation_rules (next_run_at)
    WHERE enabled;
