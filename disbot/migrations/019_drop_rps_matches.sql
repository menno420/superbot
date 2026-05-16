-- Migration 019: drop orphaned ``rps_matches`` table (PR C1).
--
-- ``rps_matches`` was created in the inlined baseline schema for an
-- envisioned match-history feature that never shipped.  No CRUD ever
-- referenced it; the audit confirmed zero reads and zero writes
-- against the table across the lifetime of the codebase.
--
-- This migration is forward-only.  The companion code change removes
-- the table from the inlined ``create_tables`` baseline, so fresh
-- installs never recreate it.  Existing deploys hit this DROP and
-- shed the empty table.
--
-- Rollback: re-add the inlined CREATE TABLE in
-- ``disbot/utils/db/migrations.py`` and a follow-up migration to
-- recreate the table.  Skip the rollback unless a future feature
-- needs the schema — the table was carrying zero data when removed.

DROP TABLE IF EXISTS rps_matches;
