-- Migration 031: setup_session (Phase 9e / Track 4 PR 8).
--
-- Per-guild record of where the owner is in the setup-wizard flow.
-- One row per guild; the row is upserted on every guild-join event
-- and updated as the wizard advances.
--
-- Schema
-- ------
-- guild_id              PRIMARY KEY. Hard FK semantically (no SQL FK
--                       because guilds are tracked via Discord IDs,
--                       not stored locally).
-- guild_name            cached at join time so the bot can describe
--                       a guild it has been removed from.
-- owner_id              guild owner's user id at session create.
-- joined_at             when the bot last joined this guild (NOW()
--                       on insert; preserved on update).
-- setup_status          'pending'      — joined, launcher posted but
--                                        owner has not started.
--                       'in_progress'  — owner clicked Start; wizard
--                                        is mid-flow.
--                       'complete'     — owner finished the flow at
--                                        least once.
--                       'dismissed'    — owner chose to defer/ignore
--                                        the launcher.
-- setup_channel_id      channel id of the posted launcher message.
-- setup_message_id      message id of the launcher.  Stored so the
--                       cog can edit/refresh the launcher in place
--                       across restarts (persistent view).
-- last_readiness_score  most recent percentage from
--                       :func:`services.setup_readiness.collect` —
--                       used to surface drift between sessions.
-- current_step          step token within the wizard for resume
--                       semantics; nullable when no flow is active.
-- delegated_admins      BIGINT[] of user ids the owner authorised to
--                       run setup on their behalf.  Empty by default;
--                       Track 4 PR 8 ships the column, Track 4 PR 9
--                       starts surfacing it in the launcher.
-- created_at / updated_at — bookkeeping. ``updated_at`` is
--                       maintained by the CRUD primitive on every
--                       write (no DB trigger to keep the schema
--                       simple).
--
-- Rollback
-- --------
-- ``DROP TABLE IF EXISTS setup_session`` removes the table.  Nothing
-- depends on the data — the launcher cog can re-create rows from
-- ``on_ready``.
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS setup_session (
    guild_id              BIGINT       PRIMARY KEY,
    guild_name            TEXT         NOT NULL,
    owner_id              BIGINT       NOT NULL,
    joined_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    setup_status          TEXT         NOT NULL DEFAULT 'pending'
        CHECK (setup_status IN ('pending', 'in_progress', 'complete', 'dismissed')),
    setup_channel_id      BIGINT,
    setup_message_id      BIGINT,
    last_readiness_score  INT,
    current_step          TEXT,
    delegated_admins      BIGINT[]     NOT NULL DEFAULT '{}',
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
