-- Migration 058: cleanup-policy version marker (server-management PR8).
--
-- Adds a lightweight ``policy_version`` column to ``cleanup_policies`` so each
-- stored policy row is self-describing about which policy schema produced it.
-- This is the "versioning" half of the server-management cleanup foundation
-- (docs/planning/server-management-implementation-plan-2026-06-05.md, PR8); the
-- level *vocabulary* round-trip lives in services/cleanup_levels.py.
--
-- Behaviour
-- ---------
-- Purely additive and behaviour-neutral. The cleanup resolver
-- (governance/cleanup.py) does NOT read this column, so resolved cleanup
-- behaviour is byte-identical before and after this migration. Every existing
-- row is backfilled to version 1 by the column DEFAULT; new rows inserted by the
-- unchanged GovernanceMutationPipeline write path also default to 1.
--
-- RC-5 is preserved: this migration does not touch the
-- ``scope_type IN ('guild','category','channel')`` CHECK or the primary key, so
-- threads keep inheriting cleanup policy from their parent (no thread scope).
--
-- Rollback
-- --------
-- ALTER TABLE cleanup_policies DROP COLUMN IF EXISTS policy_version;
-- (Reverting the consuming code without this is harmless — the column is simply
-- unread.)
--
-- Forward-only and idempotent.

ALTER TABLE cleanup_policies
    ADD COLUMN IF NOT EXISTS policy_version INTEGER NOT NULL DEFAULT 1;
