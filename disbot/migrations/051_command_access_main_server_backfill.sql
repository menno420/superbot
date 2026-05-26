-- Migration 051: backfill the main server's command-access policy.
--
-- Pre-migration, ``config.ALLOWED_CHANNELS`` carried two hardcoded
-- channel IDs (``1348795460948590622`` and ``1403818013408624642``)
-- as the production fallback when ``BOT_ALLOWED_CHANNELS`` env was
-- unset.  PR-7 of the command-access onboarding fix deletes the env
-- var + hardcoded list from ``disbot/config.py``; this migration
-- preserves the main server's existing behavior by writing a
-- ``selected_channels`` policy keyed on whichever guild owns those
-- channels.
--
-- The migration is data-only (no schema changes) and is **safe on every
-- deployment**:
--
--   * If the channel IDs do not appear in ``panel_anchors`` for any
--     guild, both INSERTs are no-ops and the deployment retains the
--     ``all_channels`` default established in PR-2.
--   * If they do appear (the main server), exactly one policy row +
--     up to two child rows land.  ``ON CONFLICT DO NOTHING`` makes
--     the migration idempotent in case it ever re-runs after the
--     operator has already configured the policy through the
--     settings UI.
--
-- ``panel_anchors`` is the right lookup target because it has the
-- broadest row coverage of any guild-scoped table — every guild that
-- has ever opened a persistent panel has rows there.  Using
-- ``runtime_sessions`` instead would miss guilds that never opened a
-- session, and using a hardcoded ``guild_id`` would require knowing
-- it at migration write time (which we don't).
--
-- Why not query ``subsystem_bindings`` for ``bot_command_channel``:
-- the binding name is not guaranteed to be populated in older
-- deploys, while ``panel_anchors`` is populated on the first
-- restore_anchors() call after on_ready.
--
-- ``updated_by`` / ``created_by`` are intentionally NULL so the
-- audit row reads "system" rather than attributing the backfill to
-- a random operator id. The ``::bigint`` cast on each NULL is
-- required because Postgres infers a bare NULL literal as ``text``
-- in a SELECT projection, which would clash with the ``BIGINT``
-- column type and fail the INSERT with "column is of type bigint
-- but expression is of type text".
--
-- Forward-only and idempotent.

INSERT INTO guild_command_access_policy (guild_id, mode, updated_by)
SELECT DISTINCT guild_id, 'selected_channels', NULL::bigint
  FROM panel_anchors
 WHERE channel_id IN (1348795460948590622, 1403818013408624642)
ON CONFLICT (guild_id) DO NOTHING;

INSERT INTO guild_command_access_channels (guild_id, channel_id, created_by)
SELECT DISTINCT guild_id, channel_id, NULL::bigint
  FROM panel_anchors
 WHERE channel_id IN (1348795460948590622, 1403818013408624642)
ON CONFLICT (guild_id, channel_id) DO NOTHING;
