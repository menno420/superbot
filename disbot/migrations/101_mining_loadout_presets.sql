-- Migration 101: named gear loadout presets (V-14 / Q-0175 Phase-1 unified-loadout model).
--
-- The remaining Phase-1 piece of the unified-character plan
-- (docs/planning/fishing-open-world-expansion-plan-2026-06-18.md): a player can
-- save their current equipped gear under a name (e.g. `mining`, `combat`,
-- `fishing`) and swap their whole loadout back to it later.  Switching is an
-- optimisation, never a gate.
--
-- Direct-lane game state, same lane as mining_equipment (docs/ownership.md
-- routes mining writes direct via utils/db/games/; the RC-8A ledger catalogues
-- this as an accepted-direct-write).  CRUD primitives live in
-- utils/db/games/mining_loadout.py.
--
-- One row per (user_id, guild_id, name, slot).  A preset is the set of rows
-- sharing a (user_id, guild_id, name) — each row pins one slot's saved item.
-- user_id is TEXT to match mining_equipment / mining_inventory's legacy column
-- type.  Additive only (no existing table touched); rollback by dropping the
-- table (no readers exist outside utils/db/games/mining_loadout.py as of this
-- migration).
CREATE TABLE IF NOT EXISTS mining_loadout_presets (
    user_id    TEXT        NOT NULL,
    guild_id   BIGINT      NOT NULL,
    name       TEXT        NOT NULL,
    slot       TEXT        NOT NULL,
    item_name  TEXT        NOT NULL,
    saved_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, guild_id, name, slot)
);
