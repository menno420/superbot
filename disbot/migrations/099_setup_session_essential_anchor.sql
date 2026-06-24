-- Migration 099: setup_session.essential_message_id + essential_step columns.
--
-- Makes the plain-language **Essential Setup** spine survive a bot restart by
-- recording the in-channel wizard message and the step the operator is on, so
-- the on-ready resume sweep can revive that message in place with a Resume
-- button (mirrors the launcher's setup_message_id / _resume_launchers pattern).
--
-- * ``essential_message_id`` — the Discord snowflake of the Essential Setup
--   flow message in the private ``#superbot-setup`` channel
--   (``setup_channel_id``).  NULL when no Essential Setup flow is in flight.
-- * ``essential_step`` — the 0-based index of the step the flow is on, used to
--   rebuild the flow at the right place on resume.  NULL when no flow is in
--   flight.
--
-- These are deliberately separate from ``setup_message_id`` / ``current_step``
-- (which belong to the launcher + advanced wizard respectively): the launcher
-- and the Essential Setup flow are two distinct anchored messages that coexist
-- (launcher in a public channel, the flow in ``#superbot-setup``), so a single
-- pair of columns cannot serve both.
--
-- Essential Setup is direct-apply (every step writes immediately through its
-- audited service), so these columns persist only the *UI position* — no
-- configuration is stored here, and a missing/cleared anchor simply means the
-- next ``/setup`` starts a fresh flow.
--
-- Rollback
-- --------
-- ``ALTER TABLE setup_session DROP COLUMN essential_message_id, DROP COLUMN
-- essential_step`` removes them.  No FK depends on either; the resume sweep
-- treats a missing column / NULL anchor as "nothing to revive".
--
-- Forward-only and idempotent.

ALTER TABLE setup_session
    ADD COLUMN IF NOT EXISTS essential_message_id BIGINT,
    ADD COLUMN IF NOT EXISTS essential_step INTEGER;
