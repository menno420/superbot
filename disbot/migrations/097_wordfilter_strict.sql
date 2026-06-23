-- Migration 097: per-guild prohibited-word filter "strict" (anti-evasion) mode.
--
-- Adds a per-guild opt-in toggle for obfuscation-resistant matching in the
-- cleanup prohibited-words filter. When ON, a message is also checked against a
-- de-obfuscated view of its text (leet / unicode-confusable / fullwidth /
-- zero-width & invisible-character / spaced-letter evasion) -- defeating the
-- bypass tricks that walk straight through the default `\bword\b` match.
--
-- Table
-- -----
-- wordfilter_config
--   guild_id  BIGINT PRIMARY KEY
--   strict    BOOLEAN NOT NULL DEFAULT FALSE
--
-- Default: a guild with no row (or strict = FALSE) behaves exactly as today --
-- only the existing exact `\bword\b` match runs. Operators opt in from the
-- prohibited-words panel. Kept as its own table (mirroring `prohibited_words`)
-- rather than a `guild_settings` KV row, so it stays clear of the settings-key
-- declaration/mutation invariants and needs no SettingSpec.
--
-- Rollback
-- --------
-- DROP TABLE IF EXISTS wordfilter_config;
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS wordfilter_config (
    guild_id BIGINT PRIMARY KEY,
    strict   BOOLEAN NOT NULL DEFAULT FALSE
);
