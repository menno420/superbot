-- Mining equipment: which item a player has equipped in each slot.
-- Direct-lane game state (docs/ownership.md routes mining writes direct via
-- utils/db/games/; the RC-8A ledger catalogues this as accepted-direct-write).
-- One row per (user_id, guild_id, slot); user_id is TEXT to match
-- mining_inventory's legacy column type.
CREATE TABLE IF NOT EXISTS mining_equipment (
    user_id     TEXT        NOT NULL,
    guild_id    BIGINT      NOT NULL,
    slot        TEXT        NOT NULL,
    item_name   TEXT        NOT NULL,
    equipped_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, guild_id, slot)
);
