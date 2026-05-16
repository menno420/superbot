-- Migration 016: schema-prep for the mining multi-guild fix (PR M1).
--
-- Adds a covering index on (user_id, guild_id) for the queries that
-- migration 017 will introduce when the primary key is widened to
-- include guild_id and the CRUD functions in disbot/utils/db/games/
-- mining.py start filtering by guild_id.
--
-- This migration is additive and non-breaking.  The current CRUD path
-- ignores guild_id entirely, so this index is unused by present-day
-- traffic.  The plan is:
--
--   M1 (this file) — add the index, bake 24-48h.
--   M2 — drop the current PK (user_id, item_name), add the composite
--        PK (user_id, guild_id, item_name), drop this prep index
--        (subsumed by the new PK prefix).
--   M3 — flip the CRUD signatures to require guild_id and update all
--        call sites in mining_cog, leaderboard_cog, inventory_cog.
--
-- Rollback: ``DROP INDEX IF EXISTS idx_mining_user_guild;`` — safe.

CREATE INDEX IF NOT EXISTS idx_mining_user_guild
    ON mining_inventory (user_id, guild_id);
