-- Migration 050: guild_command_access (PR-1 of the command-access fix).
--
-- Per-guild policy controlling which channels normal prefix + slash
-- commands are allowed in.  Replaces the legacy global
-- ``BOT_ALLOWED_CHANNELS`` env var + hardcoded fallback IDs that
-- previously controlled command admission for every guild.
--
-- Three modes are supported:
--
--   * ``all_channels``                — normal commands allowed anywhere
--                                       (subject to governance + per-command
--                                       decorators)
--   * ``selected_channels``           — normal commands allowed only in
--                                       channels listed in
--                                       ``guild_command_access_channels``
--   * ``disabled_except_bootstrap``   — normal commands denied; bootstrap
--                                       commands (setup/help/platform/
--                                       settings/diagnostics) still
--                                       reachable for guild operators
--
-- Schema
-- ------
-- guild_command_access_policy
--   guild_id     The guild owning this policy.  Primary key — one row
--                per guild.  Absence of a row means "unconfigured", and
--                the resolver applies the safe default (all_channels).
--   mode         One of the three modes above; CHECK constraint pinned.
--   updated_by   Operator (user id) who last changed the mode.  NULL
--                only for migration-installed rows.
--   updated_at   Bookkeeping (mode change timestamp).
--   created_at   Bookkeeping (first-write timestamp).
--
-- guild_command_access_channels
--   guild_id     Parent guild; FK with ON DELETE CASCADE so dropping the
--                policy row sweeps its channel list.
--   channel_id   Discord channel id allowed under ``selected_channels``
--                mode.  Composite primary key with ``guild_id`` so a
--                channel can appear at most once per guild.
--   created_by   Operator who added this channel.  NULL only for
--                migration-installed rows.
--   created_at   Bookkeeping (add timestamp).
--
-- An index on ``guild_id`` is implicit in the composite primary key
-- (Postgres can use the leading column), so no additional index is
-- needed for the resolver's hot read.
--
-- Rollback
-- --------
-- ``DROP TABLE IF EXISTS guild_command_access_channels;`` then
-- ``DROP TABLE IF EXISTS guild_command_access_policy;`` removes both
-- tables.  Reverting the code that consumes them (PR-4 / PR-5) without
-- this migration leaves orphan rows that are harmless — nothing else
-- references them.
--
-- The main server's existing allowed channels are backfilled by a
-- separate later migration (see plan PR-8) once the env var + hardcoded
-- IDs are deleted from ``disbot/config.py``.  This migration is
-- intentionally schema-only so PR-1 ships with no behavior change.
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS guild_command_access_policy (
    guild_id   BIGINT       PRIMARY KEY,
    mode       TEXT         NOT NULL,
    updated_by BIGINT,
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CHECK (mode IN ('all_channels', 'selected_channels', 'disabled_except_bootstrap'))
);

CREATE TABLE IF NOT EXISTS guild_command_access_channels (
    guild_id   BIGINT       NOT NULL
        REFERENCES guild_command_access_policy(guild_id) ON DELETE CASCADE,
    channel_id BIGINT       NOT NULL,
    created_by BIGINT,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (guild_id, channel_id)
);
