-- 085_mining_grid.sql — grid Mine (hub-redesign PR 3): the (x, y, z) world model.
--
-- Owner design (Q-0173): the vertical axis IS the existing depth bands, so z =
-- mining_player_state.depth (unchanged).  This migration adds the LATERAL
-- position (pos_x, pos_y), a per-guild world seed (ONE shared, shareable grid
-- per seed), and a per-player fog-of-war "discovered cells" store.
--
-- All additive: a player with no row reads (0, 0); a guild with no mining_world
-- row defaults to seed = guild_id (the DB read supplies it), so every guild has
-- a stable shared world with no setup and existing play is unchanged.

ALTER TABLE mining_player_state
    ADD COLUMN IF NOT EXISTS pos_x INTEGER NOT NULL DEFAULT 0;
ALTER TABLE mining_player_state
    ADD COLUMN IF NOT EXISTS pos_y INTEGER NOT NULL DEFAULT 0;

-- One shared procedural world per guild (Q-0173: "ONE shared grid per seed").
-- A guild with no row defaults to seed = guild_id in the read layer, so this
-- table only ever holds an explicit owner re-seed (`!mineworld <seed>`).
CREATE TABLE IF NOT EXISTS mining_world (
    guild_id   BIGINT      PRIMARY KEY,
    seed       BIGINT      NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Per-player fog of war: the set of cells a player has stood on or mined.  One
-- row per visited (z, x, y); the map render only ever queries a small window
-- around the player, so reads stay O(window) however far a player has roamed.
CREATE TABLE IF NOT EXISTS mining_discovered (
    user_id  TEXT    NOT NULL,
    guild_id BIGINT  NOT NULL,
    z        INTEGER NOT NULL,
    x        INTEGER NOT NULL,
    y        INTEGER NOT NULL,
    PRIMARY KEY (user_id, guild_id, z, x, y)
);
