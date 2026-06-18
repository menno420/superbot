-- Fishing collection log (ecosystem #2, owner design Q-0175 —
-- docs/planning/fishing-open-world-expansion-plan-2026-06-18.md). One row per
-- (user, guild, species) holding the player's running tally for that fish: how
-- many caught + first/last catch timestamps. An absent row = never caught, so
-- an EMPTY table is byte-identical to the pre-fishing bot (the additive safety
-- property). Fish value/use is an explicitly OPEN owner question, so there is no
-- coin/value column in v1 — the reward is progression (level up → unlock bigger
-- fish, fishing_workflow) + this collection record.
--
-- user_id is BIGINT to match player_skills / game_xp / mining_structures
-- (player-progression identity), NOT mining_inventory's legacy TEXT column.
CREATE TABLE IF NOT EXISTS fishing_catch_log (
    user_id      BIGINT      NOT NULL,
    guild_id     BIGINT      NOT NULL DEFAULT 0,
    species      TEXT        NOT NULL,
    count        INTEGER     NOT NULL DEFAULT 0,
    first_caught TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_caught  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, guild_id, species)
);
