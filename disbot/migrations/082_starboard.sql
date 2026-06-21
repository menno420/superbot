-- Starboard / Hall-of-Fame (idea B1; plan docs/planning/starboard-plan-2026-06-21.md).
--
-- N star-reactions on any message -> the message is posted to a hall-of-fame
-- channel with a live-updating star count. Two guild-keyed tables:
--   starboard_settings  — per-guild config (one row): where + how many stars.
--   starboard_entries   — one row per source message that has entered the board,
--                         mapping source -> starboard message so the embed can be
--                         edited (recount) / deleted (drop below threshold) and
--                         never double-posted (the PK dedupes).
-- Both register teardown in guild_lifecycle.py (architecture INV-I). Reuses the
-- hardened raw-reaction seam (reaction-roles overhaul, #1234-#1250); additive.

CREATE TABLE IF NOT EXISTS starboard_settings (
    guild_id   BIGINT  PRIMARY KEY,
    channel_id BIGINT  NOT NULL,            -- the hall-of-fame channel
    threshold  INTEGER NOT NULL DEFAULT 3,  -- stars needed to enter
    emoji      TEXT    NOT NULL DEFAULT '⭐',-- the trigger emoji
    enabled    BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS starboard_entries (
    guild_id             BIGINT  NOT NULL,
    source_message_id    BIGINT  NOT NULL,
    starboard_message_id BIGINT,            -- NULL until first posted
    star_count           INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, source_message_id)
);

CREATE INDEX IF NOT EXISTS idx_starboard_entries_guild ON starboard_entries (guild_id);
