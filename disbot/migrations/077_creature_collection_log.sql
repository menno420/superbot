-- Creature collection log (creature-game v1, the catch+collection slice).
-- One row per (user, guild, creature) holding the player's running tally for
-- that creature: how many caught, and first/last catch timestamps. An absent
-- row = never caught, so an EMPTY table is byte-identical to the pre-creature
-- bot (the additive safety property, mirroring fishing_catch_log / migration 076).
--
-- user_id is BIGINT to match player_skills / game_xp / fishing_catch_log
-- (player-progression identity), NOT mining_inventory's legacy TEXT column.
--
-- Stats/battle are NOT stored here — the catalog (disbot/data/creatures/) is the
-- creature definition, the log is only "who has caught what, how many times".
CREATE TABLE IF NOT EXISTS creature_collection_log (
    user_id      BIGINT      NOT NULL,
    guild_id     BIGINT      NOT NULL DEFAULT 0,
    creature     TEXT        NOT NULL,
    count        INTEGER     NOT NULL DEFAULT 0,
    first_caught TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_caught  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, guild_id, creature)
);
