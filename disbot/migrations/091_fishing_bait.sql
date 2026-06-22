-- Fishing bait — the optional second pre-cast economy knob (Q-0175 §4,
-- docs/planning/fishing-minigame-design-2026-06-22.md).  Fishing *level*
-- (game_xp) gates which size bands you can catch and the *rod* is the permanent
-- how-well axis; *bait* is the consumable how-well axis — a coin-bought pack of
-- charges that, while held, biases each cast toward rarer fish (multiplies the
-- rod's rarity pull) until the charges run out.  Bait is bought with coins
-- through the audited services.fishing_workflow.buy_bait seam.
--
-- One additive per-(user, guild) row holding the player's currently-loaded bait
-- key + remaining charges (a player loads at most one bait at a time).  The bait
-- knob values + the purchase/consume policy live in pure code
-- (utils/fishing/bait.py, services/fishing_workflow.py); this table just stores
-- the active loadout.  Absent row (or charges = 0) = no bait, so every existing
-- player and every fresh row fishes bait-less (which catches fine — bait only
-- improves, never gates).
CREATE TABLE IF NOT EXISTS fishing_bait (
    user_id  BIGINT  NOT NULL,
    guild_id BIGINT  NOT NULL DEFAULT 0,
    bait_key TEXT    NOT NULL DEFAULT '',
    charges  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, guild_id)
);
