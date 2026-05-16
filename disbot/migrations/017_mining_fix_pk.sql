-- Migration 017: composite PK swap for mining_inventory (PR M2).
--
-- This migration is forward-only — it widens the primary key from
-- (user_id, item_name) to (user_id, guild_id, item_name).  Migration
-- 005 did the same thing for rps_players and deathmatch_stats; mining
-- was omitted at the time and the audit surfaced the gap.
--
-- Why it's safe to apply with the old CRUD still running:
--   * The old CRUD never passes guild_id at all, so every new row
--     keeps using the column default (0).  The new PK accepts
--     guild_id=0 just like any other value.
--   * Every existing row was unique on (user_id, item_name) under the
--     old PK, so widening the key cannot introduce conflicts — every
--     guild_id is currently 0 across the whole table.
--   * The bug we are fixing in PR M3 — every guild's inventory
--     collapsing at the (user_id, item_name) row — does not get worse
--     between M2 and M3; the broken CRUD continues to write at
--     guild_id=0.
--
-- Why the prep index from 016 is dropped:
--   The new primary key is itself a covering index on
--   (user_id, guild_id, item_name); queries with predicate
--   ``WHERE user_id=$1 AND guild_id=$2`` are answered by the PK's
--   leading-prefix scan, making idx_mining_user_guild redundant.
--
-- Rollback (must be coordinated with a revert of PR M3):
--   ALTER TABLE mining_inventory DROP CONSTRAINT mining_inventory_pkey;
--   ALTER TABLE mining_inventory ADD PRIMARY KEY (user_id, item_name);
--   CREATE INDEX IF NOT EXISTS idx_mining_user_guild
--       ON mining_inventory (user_id, guild_id);
--
-- The pre-2026 ``guild_id = 0`` rows are preserved by design (Mfix-A
-- from the stabilization plan); operators can selectively prune them
-- via a one-shot tool later if desired.

ALTER TABLE mining_inventory
    DROP CONSTRAINT IF EXISTS mining_inventory_pkey;

ALTER TABLE mining_inventory
    ADD PRIMARY KEY (user_id, guild_id, item_name);

DROP INDEX IF EXISTS idx_mining_user_guild;
