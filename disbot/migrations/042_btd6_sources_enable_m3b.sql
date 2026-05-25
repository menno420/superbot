-- Migration 042: enable the 18 captured Ninja Kiwi BTD6 endpoints (M3B).
--
-- Follow-up to migration 040, which seeded 23 Ninja Kiwi official_api
-- rows with enabled=FALSE and base_url=NULL. M3B captures the response
-- envelope for 18 of those endpoints, sets base_url to the confirmed
-- host (data.ninjakiwi.com), and flips them to enabled=TRUE.
--
-- The 5 endpoints without captured fixtures remain enabled=FALSE with
-- base_url=NULL until parser scope is approved for them:
--   nk_btd6_ct_lb_player, nk_btd6_ct_lb_team, nk_btd6_ct_lb_group,
--   nk_btd6_users, nk_btd6_guild
--
-- The static asset host (static-api.nkstatic.com) appears only inside
-- response body fields (mapURL, bossTypeURL) and is intentionally NOT
-- used as a source_registry base_url.
--
-- updated_by is BIGINT (Discord user id); migrations do not run as a
-- Discord user, so it is left untouched. Provenance is appended to the
-- notes column, guarded against repeat runs.
--
-- Forward-only and idempotent.

UPDATE btd6_source_registry
   SET base_url   = 'https://data.ninjakiwi.com',
       notes      = CASE
           WHEN notes LIKE '%[042]%' THEN notes
           WHEN notes = ''           THEN '[042] base_url confirmed from captured fixtures'
           ELSE notes || ' [042] base_url confirmed from captured fixtures'
       END,
       updated_at = NOW()
 WHERE source_key IN (
   'nk_btd6_maps',            'nk_btd6_maps_filter',      'nk_btd6_maps_one',
   'nk_btd6_events',
   'nk_btd6_races',           'nk_btd6_races_metadata',   'nk_btd6_races_leaderboard',
   'nk_btd6_odyssey',         'nk_btd6_odyssey_diff',     'nk_btd6_odyssey_diff_maps',
   'nk_btd6_challenges',      'nk_btd6_challenges_filter','nk_btd6_challenges_one',
   'nk_btd6_ct',              'nk_btd6_ct_tiles',
   'nk_btd6_bosses',          'nk_btd6_bosses_metadata',  'nk_btd6_bosses_leaderboard'
 );

UPDATE btd6_source_registry
   SET enabled    = TRUE,
       updated_at = NOW()
 WHERE source_key IN (
   'nk_btd6_maps',            'nk_btd6_maps_filter',      'nk_btd6_maps_one',
   'nk_btd6_events',
   'nk_btd6_races',           'nk_btd6_races_metadata',   'nk_btd6_races_leaderboard',
   'nk_btd6_odyssey',         'nk_btd6_odyssey_diff',     'nk_btd6_odyssey_diff_maps',
   'nk_btd6_challenges',      'nk_btd6_challenges_filter','nk_btd6_challenges_one',
   'nk_btd6_ct',              'nk_btd6_ct_tiles',
   'nk_btd6_bosses',          'nk_btd6_bosses_metadata',  'nk_btd6_bosses_leaderboard'
 );
