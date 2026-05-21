-- Migration 037: setup_session.skipped_sections column.
--
-- Adds a TEXT[] column to setup_session so the wizard can remember
-- which sections the operator explicitly skipped during a run.
-- Skipped sections render with a distinct status badge on the hub
-- and tell readiness/summary to omit "needs attention" hints for
-- those slugs.
--
-- Stored as an unordered set semantically (no PG SET type, so TEXT[]
-- with COALESCE on read); empty array means no sections skipped yet.
-- Section slugs are stable per setup_sections.REGISTRY validation
-- (lowercase letters / digits / underscores, max 64 chars).
--
-- Rollback
-- --------
-- ``ALTER TABLE setup_session DROP COLUMN skipped_sections``
-- removes the column. No downstream FK depends on the contents.
--
-- Forward-only and idempotent.

ALTER TABLE setup_session
    ADD COLUMN IF NOT EXISTS skipped_sections TEXT[] NOT NULL DEFAULT '{}';
