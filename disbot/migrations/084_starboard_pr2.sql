-- Starboard PR 2 — config polish (idea B1; plan docs/planning/starboard-plan-2026-06-21.md §6).
--
-- Adds the two config knobs PR 1 deferred:
--   self_star  — count the author's own ⭐ toward the threshold? (default OFF —
--                most starboards exclude self-stars so a post can't board itself).
--   ignore-channels — a per-guild list of channels whose messages never enter the
--                board (spam/bot/staff channels). One row per (guild, channel).
-- Both are read on the (gated, rare) star-change path; the ignore list is a new
-- guild-keyed table, so it registers teardown in guild_lifecycle.py (INV-I)
-- alongside the existing starboard_settings/_entries purge.

ALTER TABLE starboard_settings
    ADD COLUMN IF NOT EXISTS self_star BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS starboard_ignore_channels (
    guild_id   BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    PRIMARY KEY (guild_id, channel_id)
);
