-- 004: governance subsystem visibility + cleanup policy tables
--
-- subsystem_visibility: per-scope (guild/category/channel/role) enabled overrides.
--   enabled=TRUE  → force visible
--   enabled=FALSE → force hidden
--   enabled=NULL  → inherit from next-wider scope (tri-state)
--
-- cleanup_policies: per-scope cleanup behavior overrides.
--   Scope resolution order: channel > category > guild > hardcoded default.

CREATE TABLE IF NOT EXISTS subsystem_visibility (
    guild_id    BIGINT  NOT NULL,
    scope_type  TEXT    NOT NULL
        CHECK (scope_type IN ('guild', 'category', 'channel', 'role')),
    scope_id    BIGINT  NOT NULL,
    subsystem   TEXT    NOT NULL,
    enabled     BOOLEAN,           -- NULL = inherit from parent scope
    PRIMARY KEY (guild_id, scope_type, scope_id, subsystem)
);

CREATE INDEX IF NOT EXISTS idx_sv_lookup
    ON subsystem_visibility (guild_id, scope_type, scope_id);

CREATE TABLE IF NOT EXISTS cleanup_policies (
    guild_id                BIGINT  NOT NULL,
    scope_type              TEXT    NOT NULL
        CHECK (scope_type IN ('guild', 'category', 'channel')),
    scope_id                BIGINT  NOT NULL,
    delete_invalid_commands BOOLEAN NOT NULL DEFAULT TRUE,
    delete_failed_commands  BOOLEAN NOT NULL DEFAULT TRUE,
    delete_after_seconds    INTEGER NOT NULL DEFAULT 5,
    PRIMARY KEY (guild_id, scope_type, scope_id)
);

