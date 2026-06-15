-- Player skill tree (brainstorm §7.4: "capped skill tree → forced
-- specialization").  One row per (user, guild, branch) holding how many points
-- the player has allocated into that branch.  Points are spent from the shared
-- game-XP level (services/game_xp_service): available = min(level, soft cap) −
-- sum(allocated), and a per-branch cap plus a soft total cap below 4×per-branch
-- means you CANNOT max every branch — that forced trade-off (digger / duelist /
-- tycoon / smith) is the whole point of the feature.
--
-- Allocations map onto the shared EffectiveStats block (utils/mining/skills.py
-- skill_stats), merged with equipped gear by utils/mining/character.py, so an
-- EMPTY allocation is byte-identical to today's gear-only stats (the additive
-- safety property — no existing play changes until a player spends a point).
-- user_id is BIGINT to match game_xp (skills derive from the game-XP level),
-- NOT mining_inventory's legacy TEXT column.
CREATE TABLE IF NOT EXISTS player_skills (
    user_id   BIGINT  NOT NULL,
    guild_id  BIGINT  NOT NULL DEFAULT 0,
    branch    TEXT    NOT NULL,
    points    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, guild_id, branch)
);
