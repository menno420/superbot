-- Migration 055: seed the Steam update-notes source for BTD6 patch notes.
--
-- Adds one row to btd6_source_registry for the public Steam Web API
-- ISteamNews/GetNewsForApp feed for Bloons TD 6 (Steam appid 960090).
-- This endpoint requires NO API key and returns the official Ninja Kiwi
-- update announcements ("Bloons TD 6 - Update 54.0", ...), so it is the
-- patch-notes feed the M3A seam (btd6_patch_service + btd6_patch_notes)
-- was built to consume. The ingestion service routes source_kind
-- 'patch_notes' through btd6_patch_service.store_parsed_notes, which the
-- steam_btd6_news parser feeds.
--
-- Identity / policy notes:
--   * source_kind = 'patch_notes' — already a valid kind from migration 040.
--   * trust_tier  = 2 — patch-note prose ranks below Tier-1 official_api
--     facts in fetch_facts_for_intent (announcements, not structured data).
--   * base_url is set (the fetcher's allowlist refuses a NULL base_url),
--     and full_url carries the complete request incl. query string:
--       count=20      — the 20 most recent news items
--       maxlength=0   — full announcement body (no Steam-side truncation)
--       format=json   — JSON, not the default RSS/ATOM
--   * enabled = FALSE — same opt-in convention as the M3A/M3B NK seeds: a
--     human flips it on (services.btd6_source_mutation.set_enabled) once
--     they want the bot polling Steam. The supervisor is additionally
--     gated behind BTD6_INGESTION_ENABLED, so nothing fetches until both
--     the env flag and this row are enabled.
--
-- Structured balance NUMBERS (tower/hero stat JSON) are NOT updated by
-- this source — those come from scripts/fetch_bloonswiki.py. Steam supplies
-- the human-readable notes + the "a new version dropped" signal.
--
-- Forward-only and idempotent.

INSERT INTO btd6_source_registry (
    source_key, source_name, source_owner, source_kind, trust_tier,
    base_url, path_template, full_url, enabled, notes
) VALUES (
    'steam_btd6_news',
    'Steam ISteamNews — Bloons TD 6 update notes',
    'Valve / Ninja Kiwi',
    'patch_notes',
    2,
    'https://api.steampowered.com',
    NULL,
    'https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/'
        || '?appid=960090&count=20&maxlength=0&format=json',
    FALSE,
    'Public Steam news feed (no API key). appid 960090. Enable to let the '
        || 'ingestion supervisor poll BTD6 update notes into btd6_patch_notes.'
)
ON CONFLICT (source_key) DO NOTHING;
