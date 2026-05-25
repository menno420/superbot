-- Migration 045: setup_draft_operations provenance columns.
--
-- Phase 0 of the setup wizard safety foundation.  Adds four nullable
-- provenance columns to ``setup_draft_operations`` so Final Review
-- recovery, ``Skip section``, the progress read model, and
-- recommended-replacement can identify rows by stable provenance
-- rather than by label or rendered text:
--
--   * section_slug   — owning setup section, e.g. "channels".
--   * staging_kind   — staging source ("recommended" / "custom" /
--                      "preset" / "manual" / "repair").  NULL is
--                      treated as "legacy / manual / preserve" so
--                      pre-existing rows survive unchanged.
--   * group_id       — opaque key tying parent/child rows into one
--                      retry group (e.g. a create_channel and its
--                      dependent bind_channel).  Reserved for future
--                      dependency-group support; the immediate Phase
--                      0 bug fix targets ProvisioningResult.outcome
--                      == "binding_failed" misclassification in
--                      services/setup_operations._apply_resource_create.
--   * parent_seq     — parent row's ``seq`` within the same draft;
--                      alternative to ``group_id`` for simple
--                      parent/child pairs.
--
-- The unique slot index from migration 035 stays unchanged.  The
-- only writer of ``staging_kind = 'recommended'`` is
-- ``services.setup_draft.replace_recommended_for_section``, which
-- performs a transactional preflight that never overwrites
-- non-recommended rows.  ``services.setup_draft.append`` defaults
-- the column to ``NULL`` for backward compatibility and explicitly
-- rejects ``'recommended'``.
--
-- Rollback
-- --------
-- ``ALTER TABLE setup_draft_operations
--   DROP COLUMN section_slug,
--   DROP COLUMN staging_kind,
--   DROP COLUMN group_id,
--   DROP COLUMN parent_seq;``
-- removes the columns.  No FK depends on them.  The recovery /
-- progress paths fall back to label-free identity by row ``id`` /
-- ``seq`` when the columns are absent.
--
-- Forward-only and idempotent.

ALTER TABLE setup_draft_operations
    ADD COLUMN IF NOT EXISTS section_slug TEXT,
    ADD COLUMN IF NOT EXISTS staging_kind TEXT,
    ADD COLUMN IF NOT EXISTS group_id     TEXT,
    ADD COLUMN IF NOT EXISTS parent_seq   INT;

CREATE INDEX IF NOT EXISTS idx_setup_draft_operations_section_slug
    ON setup_draft_operations (guild_id, section_slug)
    WHERE section_slug IS NOT NULL;
