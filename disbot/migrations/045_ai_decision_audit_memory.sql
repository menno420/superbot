-- Migration 045: ai_decision_audit memory + effective-source columns (PR-5).
--
-- Adds six nullable columns to ``ai_decision_audit``:
--
--   memory_turns_used        INTEGER   — turns supplied to the prompt on
--                                        a `replied` row.
--   memory_window_minutes    INTEGER   — active memory window at decision time.
--   memory_scan_attempted    BOOLEAN   — whether the Discord history-scan
--                                        backfill was attempted.
--   memory_scan_added_turns  INTEGER   — turns appended by the scan, if any.
--   effective_source         TEXT      — precedence scope that won
--                                        (channel / category / guild).
--   effective_mode           TEXT      — mode the winning source produced
--                                        (always_reply / mention_only / disabled).
--
-- All nullable so the migration is non-destructive — legacy rows keep
-- their existing values and the new columns stay NULL. Audit readers
-- in ``disbot/cogs/ai_cog.py`` and the support-report renderer render
-- "—" for NULL fields per ``docs/ai-config-ownership.md`` § "Audit
-- fields" (the I-4 legacy-NULL rendering rule).
--
-- Forward-only and idempotent. Safe to apply after migration 039
-- (the original ai_decision_audit definition).

ALTER TABLE ai_decision_audit
    ADD COLUMN IF NOT EXISTS memory_turns_used       INTEGER,
    ADD COLUMN IF NOT EXISTS memory_window_minutes   INTEGER,
    ADD COLUMN IF NOT EXISTS memory_scan_attempted   BOOLEAN,
    ADD COLUMN IF NOT EXISTS memory_scan_added_turns INTEGER,
    ADD COLUMN IF NOT EXISTS effective_source        TEXT,
    ADD COLUMN IF NOT EXISTS effective_mode          TEXT;
