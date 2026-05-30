-- Migration 052: role_automation_exemptions.
--
-- Per-guild, per-role exemptions from the two role-automation systems.
-- Replaces the flat, name-based ``skip_roles`` setting (which only ever
-- affected the time-based engine) with a structured, role-id-keyed table
-- that exempts a role from the XP and the time engines INDEPENDENTLY.
--
-- Schema
-- ------
-- role_automation_exemptions
--   guild_id     The guild owning this exemption row.
--   role_id      Discord role id.  Id-keyed (not name-keyed like the old
--                skip_roles) so a role rename never silently breaks the
--                exemption.  Composite primary key with guild_id so a role
--                appears at most once per guild.
--   exempt_xp    When TRUE, members holding this role are NOT granted
--                XP/level (xp_auto_assign) roles by the XP listener.
--   exempt_time  When TRUE, members holding this role are skipped entirely
--                by the time-based (days-in-guild) progression engine.
--
-- A row with both flags FALSE carries no meaning; the write path deletes
-- the row instead of storing all-false (so the table only ever lists
-- roles that are exempt from something).
--
-- An index on ``guild_id`` is implicit in the composite primary key
-- (Postgres uses the leading column), so the per-guild read needs no
-- extra index.
--
-- Backward compatibility
-- ----------------------
-- The legacy ``skip_roles`` KV setting is intentionally NOT migrated
-- (clean break — operators re-add exemptions via the new Roles settings
-- UI).  The runtime read paths stop consulting ``skip_roles`` entirely.
--
-- Rollback
-- --------
-- ``DROP TABLE IF EXISTS role_automation_exemptions;``.  Reverting the
-- consuming code without this migration leaves an orphan table that is
-- harmless — nothing else references it.
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS role_automation_exemptions (
    guild_id    BIGINT  NOT NULL,
    role_id     BIGINT  NOT NULL,
    exempt_xp   BOOLEAN NOT NULL DEFAULT FALSE,
    exempt_time BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (guild_id, role_id)
);
