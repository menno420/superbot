-- Gear wear: remaining durability of the "active" unit of each gear item a
-- player owns.  Direct-lane game state (docs/ownership.md routes mining writes
-- direct via utils/db/games/; the RC-8A ledger catalogues mining as
-- accepted-direct-write).
--
-- Keyed by item NAME, not equipment slot, so wear survives unequip/re-equip —
-- a durability column on mining_equipment (the §6.4 sketch) would reset on
-- every re-equip, a free-repair exploit that guts the resource sink.  A row
-- exists only while the item is worn: absence = full durability; breaking or
-- repairing the item deletes the row.  user_id is TEXT to match
-- mining_inventory's legacy column type.
CREATE TABLE IF NOT EXISTS mining_gear_wear (
    user_id    TEXT        NOT NULL,
    guild_id   BIGINT      NOT NULL,
    item_name  TEXT        NOT NULL,
    durability INTEGER     NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, guild_id, item_name)
);

-- "Quick-craft the last item that broke" pointer (brainstorm §6.4 reserved
-- exactly this column on mining_player_state).
ALTER TABLE mining_player_state ADD COLUMN IF NOT EXISTS last_broken_item TEXT;
