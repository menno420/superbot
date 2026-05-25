-- Migration 040: BTD6 source / fact / patch-notes schema (M3A).
--
-- Lands the typed surface for the BTD6 knowledge pipeline:
-- a global trusted-source registry, an immutable per-fetch
-- snapshot, the normalised fact store, the patch-notes feed,
-- and a write audit for source-registry mutations.
--
-- Identity model: ``source_key`` is the canonical handle so the
-- official Ninja Kiwi BTD6 endpoints can be registered (and tested)
-- before the exact base URL / domain is captured. ``base_url`` is
-- nullable until M3B confirms it; ``full_url`` is derived and NOT
-- UNIQUE.
--
-- All M3A seed rows are inserted with ``enabled=FALSE``. M3B flips
-- the first-priority endpoints to TRUE after base URL + per-endpoint
-- response format are confirmed.
--
-- Forward-only and idempotent.

-- 1) btd6_source_registry ---------------------------------------------------

CREATE TABLE IF NOT EXISTS btd6_source_registry (
    id                BIGSERIAL PRIMARY KEY,
    source_key        TEXT    NOT NULL UNIQUE,
    source_name       TEXT    NOT NULL,
    source_owner      TEXT    NOT NULL,
    source_kind       TEXT    NOT NULL
        CHECK (source_kind IN ('webpage', 'official_api', 'patch_notes')),
    trust_tier        SMALLINT NOT NULL CHECK (trust_tier IN (1, 2)),
    base_url          TEXT    NULL,
    path_template     TEXT    NULL,
    full_url          TEXT    NULL,
    cache_policy_key  TEXT    NULL,
    enabled           BOOLEAN NOT NULL DEFAULT FALSE,
    notes             TEXT    NOT NULL DEFAULT '',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by        BIGINT  NULL,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by        BIGINT  NULL
);

CREATE INDEX IF NOT EXISTS btd6_source_registry_tier_idx
    ON btd6_source_registry (trust_tier, enabled);

-- 2) btd6_source_audit ------------------------------------------------------

CREATE TABLE IF NOT EXISTS btd6_source_audit (
    id            BIGSERIAL PRIMARY KEY,
    actor_id      BIGINT NULL,
    guild_id      BIGINT NULL,
    source_key    TEXT NOT NULL,
    action        TEXT NOT NULL
        CHECK (action IN ('created', 'enabled', 'disabled',
                          'updated', 'tier_changed', 'deleted')),
    old_value     JSONB NULL,
    new_value     JSONB NULL,
    reason        TEXT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS btd6_source_audit_key_idx
    ON btd6_source_audit (source_key, created_at DESC);

-- 3) btd6_source_snapshots --------------------------------------------------

CREATE TABLE IF NOT EXISTS btd6_source_snapshots (
    id            BIGSERIAL PRIMARY KEY,
    source_id     BIGINT NOT NULL REFERENCES btd6_source_registry(id)
                                 ON DELETE CASCADE,
    fetched_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status_code   INTEGER NOT NULL,
    raw_body_hash TEXT NOT NULL,
    raw_body      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS btd6_source_snapshots_source_idx
    ON btd6_source_snapshots (source_id, fetched_at DESC);

-- 4) btd6_facts -------------------------------------------------------------

CREATE TABLE IF NOT EXISTS btd6_facts (
    id            BIGSERIAL PRIMARY KEY,
    source_id     BIGINT NOT NULL REFERENCES btd6_source_registry(id)
                                 ON DELETE RESTRICT,
    fact_type     TEXT NOT NULL,
    entity_kind   TEXT NOT NULL,
    entity_key    TEXT NOT NULL,
    body_json     JSONB NOT NULL,
    game_version  TEXT NULL,
    fetched_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    validated_at  TIMESTAMPTZ NULL,
    confidence    NUMERIC(3,2) NOT NULL DEFAULT 1.00,
    version       INTEGER NOT NULL DEFAULT 1,
    UNIQUE (fact_type, entity_kind, entity_key, version)
);

CREATE INDEX IF NOT EXISTS btd6_facts_lookup_idx
    ON btd6_facts (fact_type, entity_kind, entity_key, version DESC);

-- 5) btd6_patch_notes -------------------------------------------------------

CREATE TABLE IF NOT EXISTS btd6_patch_notes (
    id            BIGSERIAL PRIMARY KEY,
    source_id     BIGINT NOT NULL REFERENCES btd6_source_registry(id)
                                 ON DELETE RESTRICT,
    version       TEXT NOT NULL UNIQUE,
    published_at  TIMESTAMPTZ NULL,
    body          TEXT NOT NULL
);

-- 6) Seed: official Ninja Kiwi BTD6 endpoints (enabled=FALSE in M3A) -------
-- /btd6/save/:oakID is intentionally excluded — OAK token handling needs
-- a dedicated opt-in / redaction design before any code lands.
-- Battles2 endpoints are out of scope.

INSERT INTO btd6_source_registry (
    source_key, source_name, source_owner, source_kind, trust_tier,
    base_url, path_template, full_url, enabled, notes
) VALUES
    ('nk_btd6_races',              'Ninja Kiwi BTD6 /races',
     'Ninja Kiwi', 'official_api', 1, NULL, '/btd6/races', NULL, FALSE,
     'M3B first-priority — public, structured.'),
    ('nk_btd6_races_leaderboard',  'Ninja Kiwi BTD6 /races/:raceID/leaderboard',
     'Ninja Kiwi', 'official_api', 1, NULL,
     '/btd6/races/:raceID/leaderboard', NULL, FALSE, ''),
    ('nk_btd6_races_metadata',     'Ninja Kiwi BTD6 /races/:raceID/metadata',
     'Ninja Kiwi', 'official_api', 1, NULL,
     '/btd6/races/:raceID/metadata', NULL, FALSE, ''),
    ('nk_btd6_bosses',             'Ninja Kiwi BTD6 /bosses',
     'Ninja Kiwi', 'official_api', 1, NULL, '/btd6/bosses', NULL, FALSE,
     'M3B first-priority — public, structured.'),
    ('nk_btd6_bosses_leaderboard',
     'Ninja Kiwi BTD6 /bosses/:bossID/leaderboard/:type/:teamSize',
     'Ninja Kiwi', 'official_api', 1, NULL,
     '/btd6/bosses/:bossID/leaderboard/:type/:teamSize', NULL, FALSE, ''),
    ('nk_btd6_bosses_metadata',
     'Ninja Kiwi BTD6 /bosses/:bossID/metadata/:difficulty',
     'Ninja Kiwi', 'official_api', 1, NULL,
     '/btd6/bosses/:bossID/metadata/:difficulty', NULL, FALSE, ''),
    ('nk_btd6_users',              'Ninja Kiwi BTD6 /users/:userID',
     'Ninja Kiwi', 'official_api', 1, NULL, '/btd6/users/:userID', NULL,
     FALSE, 'M3B second-priority — confirm privacy / rate limits.'),
    ('nk_btd6_challenges',         'Ninja Kiwi BTD6 /challenges',
     'Ninja Kiwi', 'official_api', 1, NULL, '/btd6/challenges', NULL,
     FALSE, 'M3B first-priority.'),
    ('nk_btd6_challenges_filter',
     'Ninja Kiwi BTD6 /challenges/filter/:challengeFilter',
     'Ninja Kiwi', 'official_api', 1, NULL,
     '/btd6/challenges/filter/:challengeFilter', NULL, FALSE, ''),
    ('nk_btd6_challenges_one',
     'Ninja Kiwi BTD6 /challenges/challenge/:challengeID',
     'Ninja Kiwi', 'official_api', 1, NULL,
     '/btd6/challenges/challenge/:challengeID', NULL, FALSE, ''),
    ('nk_btd6_ct',                 'Ninja Kiwi BTD6 /ct',
     'Ninja Kiwi', 'official_api', 1, NULL, '/btd6/ct', NULL, FALSE,
     'M3B second-priority.'),
    ('nk_btd6_ct_tiles',           'Ninja Kiwi BTD6 /ct/:ctID/tiles',
     'Ninja Kiwi', 'official_api', 1, NULL,
     '/btd6/ct/:ctID/tiles', NULL, FALSE, ''),
    ('nk_btd6_ct_lb_player',
     'Ninja Kiwi BTD6 /ct/:ctID/leaderboard/player',
     'Ninja Kiwi', 'official_api', 1, NULL,
     '/btd6/ct/:ctID/leaderboard/player', NULL, FALSE, ''),
    ('nk_btd6_ct_lb_team',
     'Ninja Kiwi BTD6 /ct/:ctID/leaderboard/team',
     'Ninja Kiwi', 'official_api', 1, NULL,
     '/btd6/ct/:ctID/leaderboard/team', NULL, FALSE, ''),
    ('nk_btd6_ct_lb_group',
     'Ninja Kiwi BTD6 /ct/:ctID/leaderboard/group/:groupID',
     'Ninja Kiwi', 'official_api', 1, NULL,
     '/btd6/ct/:ctID/leaderboard/group/:groupID', NULL, FALSE, ''),
    ('nk_btd6_guild',              'Ninja Kiwi BTD6 /guild/:guildID',
     'Ninja Kiwi', 'official_api', 1, NULL, '/btd6/guild/:guildID', NULL,
     FALSE, 'M3B second-priority.'),
    ('nk_btd6_odyssey',            'Ninja Kiwi BTD6 /odyssey',
     'Ninja Kiwi', 'official_api', 1, NULL, '/btd6/odyssey', NULL, FALSE,
     'M3B first-priority.'),
    ('nk_btd6_odyssey_diff',
     'Ninja Kiwi BTD6 /odyssey/:odysseyID/:difficulty',
     'Ninja Kiwi', 'official_api', 1, NULL,
     '/btd6/odyssey/:odysseyID/:difficulty', NULL, FALSE, ''),
    ('nk_btd6_odyssey_diff_maps',
     'Ninja Kiwi BTD6 /odyssey/:odysseyID/:difficulty/maps',
     'Ninja Kiwi', 'official_api', 1, NULL,
     '/btd6/odyssey/:odysseyID/:difficulty/maps', NULL, FALSE, ''),
    ('nk_btd6_maps',               'Ninja Kiwi BTD6 /maps',
     'Ninja Kiwi', 'official_api', 1, NULL, '/btd6/maps', NULL, FALSE,
     'M3B first-priority — long-stable, daily cadence.'),
    ('nk_btd6_maps_filter',        'Ninja Kiwi BTD6 /maps/filter/:mapFilter',
     'Ninja Kiwi', 'official_api', 1, NULL,
     '/btd6/maps/filter/:mapFilter', NULL, FALSE, ''),
    ('nk_btd6_maps_one',           'Ninja Kiwi BTD6 /maps/map/:mapID',
     'Ninja Kiwi', 'official_api', 1, NULL,
     '/btd6/maps/map/:mapID', NULL, FALSE, ''),
    ('nk_btd6_events',             'Ninja Kiwi BTD6 /events',
     'Ninja Kiwi', 'official_api', 1, NULL, '/btd6/events', NULL, FALSE,
     'M3B first-priority — hourly cadence.')
ON CONFLICT (source_key) DO NOTHING;
