-- Migration 105: mineverse WRITE-contract idempotency ledger (`mining_web_actions`).
--
-- FLAG 2 of the mineverse lane (contract of record: superbot-mineverse
-- `docs/mining-write-contract.md` § "Idempotency"): the bot-side action
-- executor must store, per (guild_id, action_id), a digest of the request
-- body plus the complete original response (HTTP status + body) so that
--
--   * a byte-identical replay inside the retention window returns the ORIGINAL
--     response with `replayed: true` and never re-executes;
--   * reuse of an action_id with a DIFFERENT body is rejected 409
--     `replayed_action`;
--   * retention is >= 24 hours ACROSS RESTARTS — which is why this is a table
--     and not an in-process dict (an in-memory store would lose replay
--     protection on every deploy; merge = deploy here).
--
-- guild_id / action_id are TEXT: the contract keys them as string snowflake /
-- lowercase UUIDv4 exactly as they appear on the wire (same IEEE-754 rationale
-- as the READ contract's string snowflakes).
--
-- The write boundary is disbot/mining_write_api.py (the only writer/reader);
-- CRUD primitives live in utils/db/mining_web_actions.py. Rows expire by age:
-- lookups ignore rows older than the retention window and the writer purges
-- them opportunistically. Rollback by dropping the table (no other readers).

CREATE TABLE IF NOT EXISTS mining_web_actions (
    guild_id    TEXT        NOT NULL,
    action_id   TEXT        NOT NULL,
    body_digest TEXT        NOT NULL,
    http_status INTEGER     NOT NULL,
    response    JSONB       NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (guild_id, action_id)
);

-- The opportunistic purge scans by age.
CREATE INDEX IF NOT EXISTS idx_mining_web_actions_created_at
    ON mining_web_actions (created_at);
