-- Mining player position: a player's persistent depth in the mining "Descent".
-- Direct-lane game state (docs/ownership.md routes mining writes direct via
-- utils/db/games/; the RC-8A ledger catalogues mining as accepted-direct-write).
-- One row per (user_id, guild_id); user_id is TEXT to match mining_inventory's
-- legacy column type.  depth is the integer band index (0 = Surface); the biome
-- is derived from it (cogs.mining.world), never stored.  Survival columns
-- (health, stamina) are intentionally deferred to a later slice (brainstorm §6.4).
CREATE TABLE IF NOT EXISTS mining_player_state (
    user_id    TEXT        NOT NULL,
    guild_id   BIGINT      NOT NULL,
    depth      INTEGER     NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, guild_id)
);
