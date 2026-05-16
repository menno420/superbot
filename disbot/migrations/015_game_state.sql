-- Migration 015: Game-state checkpoint table.
--
-- Restart-safe game persistence per the P2 PR-13 plan.  Cogs that
-- hold in-flight game state in memory (blackjack hands, RPS
-- tournament rounds, counting per-channel cache) can checkpoint
-- their state here on each turn and reload it on cog_load.
--
-- The table is intentionally generic — the payload column is JSONB
-- so each subsystem owns its schema without requiring a new
-- migration for every game variation.  The (guild_id, user_id,
-- channel_id, subsystem) tuple is UNIQUE so a single game per
-- (player, channel, subsystem) is enforced at the DB level
-- (parallels INV-C / INV-D for panel_anchors / runtime_sessions).
--
-- Cleanup: services/game_state_service.clear() is called when a
-- game completes naturally.  Stale rows older than a configurable
-- horizon will be pruned by a future GC sweep (deferred — initial
-- adoption is conservative).
--
-- Additive only.  Rollback by dropping the table; no downstream
-- readers exist until cogs adopt the service in follow-up PRs.

CREATE TABLE IF NOT EXISTS game_state (
    id           BIGINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guild_id     BIGINT      NOT NULL,
    user_id      BIGINT      NOT NULL,
    channel_id   BIGINT      NOT NULL,
    subsystem    TEXT        NOT NULL,
    state        JSONB       NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_game_state UNIQUE (guild_id, user_id, channel_id, subsystem)
);

-- Active-game lookup for cog_load restoration sweeps.
CREATE INDEX IF NOT EXISTS idx_game_state_subsystem
    ON game_state (subsystem, guild_id);

-- Per-user lookup for "do I have any active games" queries.
CREATE INDEX IF NOT EXISTS idx_game_state_user
    ON game_state (guild_id, user_id);
