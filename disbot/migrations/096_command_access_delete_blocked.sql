-- Migration 096: command-access "delete blocked commands" toggle.
--
-- Adds a per-guild opt-in to the command-access policy: when ON, a
-- command-style message typed in a channel where Command Access denies
-- it (``selected_channels`` non-listed channel, or
-- ``disabled_except_bootstrap``) is auto-deleted on sight by the cleanup
-- auto-mod path, instead of being silently ignored.  Restores the
-- old-bot behaviour ("instantly delete commands where commands aren't
-- allowed") on top of the existing Command Access setting.
--
-- Column
-- ------
-- delete_blocked_commands
--   BOOLEAN NOT NULL DEFAULT FALSE.  Default FALSE = no behaviour change
--   for any existing guild; the operator opts in via the Command Access
--   settings panel.  Bootstrap commands by operators are always exempt
--   (the resolver admits them before this gate is ever consulted).
--
-- Rollback
-- --------
-- ``ALTER TABLE guild_command_access_policy DROP COLUMN IF EXISTS
-- delete_blocked_commands;``
--
-- Forward-only and idempotent.

ALTER TABLE guild_command_access_policy
    ADD COLUMN IF NOT EXISTS delete_blocked_commands BOOLEAN NOT NULL DEFAULT FALSE;
