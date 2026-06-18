-- Fishing collection log (ecosystem #2, the plan's PR 1 — the "collection-log
-- hook" the survival plan's P3 ecosystem-ready-seams note requires).  One row
-- per (user, guild, species) holding the player's running tally for that fish:
-- how many caught, the heaviest one, total coins earned from it, and first/last
-- catch timestamps.  An absent row = never caught (so an EMPTY table is
-- byte-identical to the pre-fishing bot — the additive safety property).
--
-- user_id is BIGINT to match player_skills / game_xp / mining_structures
-- (player-progression identity), NOT mining_inventory's legacy TEXT column.
CREATE TABLE IF NOT EXISTS fishing_catch_log (
    user_id      BIGINT      NOT NULL,
    guild_id     BIGINT      NOT NULL DEFAULT 0,
    species      TEXT        NOT NULL,
    count        INTEGER     NOT NULL DEFAULT 0,
    best_weight  REAL        NOT NULL DEFAULT 0,
    total_value  BIGINT      NOT NULL DEFAULT 0,
    first_caught TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_caught  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, guild_id, species)
);
