-- Migration 002: Add guild_id isolation to non-scoped tables
-- Tables: mining_inventory, deathmatch_stats, rps_players
-- DEFAULT 0 allows existing rows to survive; treat 0 as "global/legacy" data.

ALTER TABLE mining_inventory
    ADD COLUMN IF NOT EXISTS guild_id BIGINT NOT NULL DEFAULT 0;

ALTER TABLE deathmatch_stats
    ADD COLUMN IF NOT EXISTS guild_id BIGINT NOT NULL DEFAULT 0;

ALTER TABLE rps_players
    ADD COLUMN IF NOT EXISTS guild_id BIGINT NOT NULL DEFAULT 0;
