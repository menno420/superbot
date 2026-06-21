-- Creature PvP battle record (creature-game v1, the result-recording slice).
-- One row per (user, guild) holding that player's lifetime PvP win/loss tally.
-- An absent row = never battled, so an EMPTY table is byte-identical to the
-- pre-PvP bot (the additive safety property, mirroring creature_collection_log /
-- migration 077).
--
-- user_id is BIGINT to match creature_collection_log / game_xp / player_skills
-- (player-progression identity).
--
-- Only the W/L tally lives here — the level-normalized battle math is pure
-- (utils/creatures/battle.py) and the team comes from the collection log; this
-- table is purely "who has won/lost how many PvP battles".
CREATE TABLE IF NOT EXISTS creature_battle_record (
    user_id     BIGINT      NOT NULL,
    guild_id    BIGINT      NOT NULL DEFAULT 0,
    wins        INTEGER     NOT NULL DEFAULT 0,
    losses      INTEGER     NOT NULL DEFAULT 0,
    last_battle TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, guild_id)
);
