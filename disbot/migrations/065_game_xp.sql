-- Shared cross-game progression track (mining brainstorm §7.4, Wave 2).
-- One row per (user, guild, game): per-game attribution + per-game daily
-- soft caps + the crafting leaderboard; the player's SHARED level derives
-- from SUM(xp) through the existing chat-XP curve — deliberately NO stored
-- level column (the shared track must not fragment per game; owner taste
-- §7.2: prestige + leaderboard + later skill points, never content gates).
-- Separate from chat XP on purpose — chat XP drives the auto-role tiers.
CREATE TABLE IF NOT EXISTS game_xp (
    user_id    BIGINT      NOT NULL,
    guild_id   BIGINT      NOT NULL,
    game       TEXT        NOT NULL,
    xp         BIGINT      NOT NULL DEFAULT 0,
    day        DATE,
    day_xp     INTEGER     NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, guild_id, game)
);

CREATE INDEX IF NOT EXISTS idx_game_xp_guild ON game_xp (guild_id, xp DESC);
