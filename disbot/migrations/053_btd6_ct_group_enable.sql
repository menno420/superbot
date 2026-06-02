-- Migration 053: enable the CT group (bracket) leaderboard source.
--
-- Migration 040 seeded nk_btd6_ct_lb_group with the template
--   /btd6/ct/:ctID/leaderboard/group/:groupID
-- but left it enabled=FALSE with base_url=NULL; migration 042 deferred it
-- ("until parser scope is approved") because no fixtures were captured.
--
-- The per-team CT standings feature consumes this endpoint on demand: a guild
-- pastes its bracket (group) id, and btd6_live_query_service.get_ct_bracket()
-- fetches /btd6/ct/<active>/leaderboard/group/<groupId> live to show the team's
-- score and rank against its weekly bracket. Confirm the host and enable it.
--
-- The global player / team leaderboard rows (nk_btd6_ct_lb_player,
-- nk_btd6_ct_lb_team) stay disabled until their own read path lands.
--
-- Forward-only and idempotent.

UPDATE btd6_source_registry
   SET base_url   = 'https://data.ninjakiwi.com',
       enabled    = TRUE,
       notes      = CASE
           WHEN notes LIKE '%[053]%' THEN notes
           WHEN notes = ''           THEN '[053] enabled for per-team CT bracket standings'
           ELSE notes || ' [053] enabled for per-team CT bracket standings'
       END,
       updated_at = NOW()
 WHERE source_key = 'nk_btd6_ct_lb_group';
