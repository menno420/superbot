-- Idle egg/chicken farm — the bot's first idle (accrue-over-time) game
-- (owner-directed task "Idle egg/chicken farm"; docs/subsystems/games.md).
--
-- One per-(user, guild) row holding the flock size, the coop upgrade level, and
-- the idle egg accrual state: the stored egg count + the unix timestamp it was
-- last settled at. Effective eggs at any instant are computed from elapsed time
-- in pure code (utils/farm/farm.py settle()) — no background ticker
-- (ADR-001/002: no external state, no scheduler).
--
-- Defaults: every farmer starts with one free starter hen (chickens = 1), an
-- empty coop (eggs = 0, eggs_updated_at = 0 → the first settle simply begins
-- accruing from row creation), and a base coop (coop_level = 0).
CREATE TABLE IF NOT EXISTS chicken_farm (
    user_id          BIGINT  NOT NULL,
    guild_id         BIGINT  NOT NULL DEFAULT 0,
    chickens         INTEGER NOT NULL DEFAULT 1,
    eggs             INTEGER NOT NULL DEFAULT 0,
    eggs_updated_at  BIGINT  NOT NULL DEFAULT 0,
    coop_level       INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, guild_id)
);
