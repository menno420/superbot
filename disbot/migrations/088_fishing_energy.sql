-- Fishing energy — the playable-pace "fuel" for casting (owner "soft energy/
-- cooldown" decision, AskUserQuestion 2026-06-22; docs/subsystems/games.md).
-- Each cast spends 1 energy, energy regenerates ~1 / 30s (= 120/hour, the
-- fishing-side throttle), so fishing is finite and a caught fish can sell for
-- real coins.  A SEPARATE bar from mining (the owner's explicit choice): you can
-- fish when mined-out and vice-versa.
--
-- One per-(user, guild) row holding the stored energy value + the unix timestamp
-- it was last settled at.  Effective energy at any instant is computed from
-- elapsed time in pure code (utils/fishing/energy.py) — no background ticker
-- (ADR-001/002: no external state, no scheduler).  energy defaults to the full
-- bar (20) and energy_updated_at to 0, so every existing player and every fresh
-- row starts with a full bar (a huge elapsed-from-0 simply settles to the cap).
CREATE TABLE IF NOT EXISTS fishing_energy (
    user_id           BIGINT  NOT NULL,
    guild_id          BIGINT  NOT NULL DEFAULT 0,
    energy            INTEGER NOT NULL DEFAULT 20,
    energy_updated_at BIGINT  NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, guild_id)
);
