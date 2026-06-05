-- Migration 056: role-id groundwork for role_thresholds (server-management PR6).
--
-- The time/XP role-automation table ``role_thresholds`` is keyed by
-- ``(guild_id, role_name)`` and matched against the guild's roles by name.
-- A role rename silently orphans its threshold, and the free-text "Add" modal
-- could persist a name for a role that does not exist.
--
-- This migration lays the ID groundwork (the original PR5 deferral, landed with
-- its PR6 selector consumer): two **nullable, additive** columns.
--
-- Schema
-- ------
-- role_thresholds (existing PK: guild_id, role_name)
--   role_id       Discord role id captured at configuration time.  Lets the
--                 readers resolve the role id-first (surviving a rename) and the
--                 panels diagnose a stale row whose role no longer exists.
--                 NULL for legacy rows written before the selector UI.
--   display_name  Snapshot of the role's name at configuration time, for stale
--                 diagnostics ("stored as X, now Y / gone").  NULL for legacy.
--
-- Backward compatibility
-- ----------------------
-- Purely additive: existing name-only rows keep working (both columns NULL).
-- The dual-read is ID-first with a normalized-name fallback, so a NULL role_id
-- resolves exactly as before.  No destructive name -> id flip happens here; the
-- PK stays (guild_id, role_name).
--
-- Rollback
-- --------
-- ALTER TABLE role_thresholds DROP COLUMN IF EXISTS role_id, DROP COLUMN IF
-- EXISTS display_name;  (Reverting the consuming code without this is harmless —
-- the columns are simply unread.)
--
-- Forward-only and idempotent.

ALTER TABLE role_thresholds
    ADD COLUMN IF NOT EXISTS role_id BIGINT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS display_name TEXT DEFAULT NULL;
