-- Migration 046: setup_session.acknowledged_sections column.
--
-- Mirrors migration 037 (skipped_sections) for the inverse signal —
-- which sections the operator has explicitly acknowledged complete.
-- Used by metadata-only and link-only setup sections (Purpose,
-- AI link-only) whose progress cannot be inferred from a staged
-- draft because they emit zero draft operations.
--
-- ``services.setup_progress`` reads this set and surfaces matching
-- sections as APPLIED so the hub doesn't show them as NOT_STARTED
-- forever.  ``services.setup_session.mark_complete`` / ``dismiss``
-- clear the set alongside ``skipped_sections``.
--
-- Stored as an unordered set semantically (no PG SET type, so TEXT[]
-- with COALESCE on read); empty array means no sections acknowledged.
-- Section slugs are stable per setup_sections.REGISTRY validation
-- (lowercase letters / digits / underscores, max 64 chars).
--
-- Rollback
-- --------
-- ``ALTER TABLE setup_session DROP COLUMN acknowledged_sections``
-- removes the column.  No downstream FK depends on the contents.
--
-- Forward-only and idempotent.

ALTER TABLE setup_session
    ADD COLUMN IF NOT EXISTS acknowledged_sections TEXT[] NOT NULL DEFAULT '{}';
