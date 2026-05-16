-- Migration 018: game_state versioning scaffold (PR G0).
--
-- Adds a ``version INT NOT NULL DEFAULT 1`` column to game_state so
-- adopting cogs (PR G1+) can detect and refuse JSONB payloads written
-- by an older code path.  Without this, a cog that changes its
-- payload shape between deploys would silently load incompatible
-- state and either crash or corrupt the game.
--
-- The default value (1) means every existing row migrates implicitly
-- to version 1.  No row data is rewritten.
--
-- Cogs adopting the service will:
--   1. Pass ``version=N`` to ``game_state_service.save``.
--   2. On ``cog_load``, compare the loaded version to the cog's
--      current version and either resume or refund+clear.
--
-- The version column is NOT in the unique constraint — version
-- mismatches are detected by the cog after a load, not by the DB.
--
-- Rollback: ``ALTER TABLE game_state DROP COLUMN version;`` — safe;
-- no production rows reference the column yet.

ALTER TABLE game_state
    ADD COLUMN IF NOT EXISTS version INT NOT NULL DEFAULT 1;
