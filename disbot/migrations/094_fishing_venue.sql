-- Fishing venue — which water the player is fishing (owner design Q-0175 §5,
-- docs/planning/fishing-minigame-design-2026-06-22.md).  Shore is the relaxed
-- default; setting sail in the boat opens the deepwater venue, with its own
-- boat-only species pool and a tougher minigame (longer bites + far higher
-- escape — the numbers live in pure code, utils/fishing/venue.py).
--
-- One additive per-(user, guild) row holding the current venue string.  An
-- absent row reads as 'shore', so every existing player and every fresh row
-- starts on the shore (the ⛵ Set sail / 🏖️ Dock toggle flips it).  Venue is
-- plain game state — it is set through services.fishing_workflow.set_venue and
-- read on every cast (begin_cast); no audit (like rod tier / energy).
CREATE TABLE IF NOT EXISTS fishing_venue (
    user_id  BIGINT NOT NULL,
    guild_id BIGINT NOT NULL DEFAULT 0,
    venue    TEXT   NOT NULL DEFAULT 'shore',
    PRIMARY KEY (user_id, guild_id)
);
