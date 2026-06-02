-- Migration 054: BTD6 deterministic data blobs (Postgres data backend).
--
-- A static reference blob store for the BTD6 fixtures + per-entity stats tree
-- that otherwise live under disbot/data/btd6/. Rows are keyed by repo-relative
-- path, e.g. 'towers.json', 'stats/dart_monkey.json', 'paragon_abilities.json'.
--
-- services.btd6_data_provider.PostgresRawProvider loads these into memory with
-- one query at startup (the asyncpg pool + migrations are ready before any cog
-- loads) when BTD6_DATA_BACKEND=postgres; btd6_data_service / btd6_stats_service
-- then read from that warmed cache, so the synchronous loaders never touch the
-- async DB on a hot path. Seed / refresh via scripts/seed_btd6_data.py.
--
-- body is JSONB (validated, round-tripped as a dict by the jsonb codec).
-- sha256 records the provenance of the source file (informational, not a
-- runtime integrity gate).
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS btd6_data_blobs (
    name        TEXT PRIMARY KEY,
    body        JSONB NOT NULL,
    sha256      TEXT,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
