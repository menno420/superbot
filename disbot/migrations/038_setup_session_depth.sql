-- Migration 038: setup_session.depth column.
--
-- Adds a nullable ``depth`` column to ``setup_session`` that records
-- the operator's choice of wizard depth (quick / standard /
-- advanced). The hub uses the value to filter which registered
-- :class:`SetupSection`s appear; ``NULL`` means "operator has not
-- yet chosen", which signals the hub to show the depth picker
-- before rendering section buttons.
--
-- Existing rows keep ``depth IS NULL`` so a re-run of the wizard
-- will surface the picker once and persist the choice. New guilds
-- get the same treatment on first launcher open.
--
-- Rollback
-- --------
-- ``ALTER TABLE setup_session DROP COLUMN depth`` removes the
-- column. The hub falls back to "all sections" when the column is
-- absent (the SELECT in utils/db/setup_session.py SELECTs the
-- column explicitly, so removing it requires reverting that change
-- as well).
--
-- Forward-only and idempotent.

ALTER TABLE setup_session
    ADD COLUMN IF NOT EXISTS depth TEXT
        CHECK (depth IS NULL OR depth IN ('quick', 'standard', 'advanced'));
