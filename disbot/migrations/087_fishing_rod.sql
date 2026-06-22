-- Fishing rod tier — the second, orthogonal fishing-progression axis (Q-0175,
-- docs/planning/fishing-minigame-design-2026-06-22.md).  Fishing *level*
-- (game_xp) gates which size bands you can catch; the *rod* gates how well /
-- which-within-band you catch them, via four tuned knobs (window bonus, bite
-- speed, rarity pull, escape resist) that live in pure code (utils/fishing/rods.py).
--
-- One additive per-(user, guild) row holding the owned rod tier (0 = the starter
-- "Bare Rod", up the ladder to diamond).  Rods are bought with coins through the
-- audited services.fishing_workflow.buy_rod seam; this table just stores the tier.
-- Absent row = tier 0, so every existing player and every fresh row starts on the
-- starter rod (which still catches fine — rods only improve, never gate).
CREATE TABLE IF NOT EXISTS fishing_rod (
    user_id  BIGINT  NOT NULL,
    guild_id BIGINT  NOT NULL DEFAULT 0,
    tier     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, guild_id)
);
