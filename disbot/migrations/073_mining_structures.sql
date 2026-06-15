-- Player-built mining structures (brainstorm §7.5: built coin + material sinks
-- that tie into progression).  One row per (user, guild, structure) holding the
-- structure's built level; absent row = level 0 (not built).  Generic on
-- purpose: the Forge (Slice B — gates higher-tier gear crafting) is the first
-- structure, and the Home backdrop (Slice C) reuses this same table + the
-- services/mining_workflow build boundary.
--
-- The forge level required to craft a recipe is derived from its gear tier in
-- pure code (utils/mining/structures.forge_level_required) — bronze/iron/silver
-- gear, tools, and structures need level 0 (no forge), so an EMPTY table is
-- byte-identical to today's crafting (the additive safety property; only gold/
-- diamond gear gates).  user_id is BIGINT to match player_skills / game_xp
-- (player-progression identity), NOT mining_inventory's legacy TEXT column.
CREATE TABLE IF NOT EXISTS mining_structures (
    user_id   BIGINT  NOT NULL,
    guild_id  BIGINT  NOT NULL DEFAULT 0,
    structure TEXT    NOT NULL,
    level     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, guild_id, structure)
);
