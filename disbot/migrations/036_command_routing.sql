-- Migration 036: command_routing_policy (Setup Wizard cog routing).
--
-- Per-scope per-cog enable/disable overrides.  The runtime
-- :func:`services.command_routing.is_cog_enabled` resolves by walking
-- channel → category → guild → default-true so absence of any policy
-- row never silently disables a cog (cogs are enabled by default).
--
-- Schema
-- ------
-- guild_id     The guild this policy belongs to.  Hard FK semantically.
-- scope_type   ``guild`` / ``category`` / ``channel`` — mirrors the
--              cleanup_policies scope vocabulary.  Threads inherit
--              from their parent channel and do not have their own
--              scope here.
-- scope_id     The category / channel id when ``scope_type`` is one of
--              those.  NULL when ``scope_type='guild'``.
-- cog_name     Stable cog name as registered by ``utils.subsystem_registry``.
--              Free-form text so contributors can add a cog without
--              updating an enum here.
-- enabled      True iff the cog is enabled in this scope.
-- actor_id     Operator who set the policy; preserved for audit joins.
-- updated_at   Bookkeeping.
--
-- The UNIQUE index uses COALESCE on ``scope_id`` because PostgreSQL
-- UNIQUE treats NULL as distinct; without COALESCE every guild-scope
-- row would collide on (guild_id, scope_type, NULL, cog_name).
--
-- Rollback
-- --------
-- ``DROP TABLE IF EXISTS command_routing_policy`` removes the table.
-- Nothing depends on the data — the resolver returns enabled=True
-- when no row exists, so an empty table is the production default.
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS command_routing_policy (
    id            BIGSERIAL    PRIMARY KEY,
    guild_id      BIGINT       NOT NULL,
    scope_type    TEXT         NOT NULL,
    scope_id      BIGINT,
    cog_name      TEXT         NOT NULL,
    enabled       BOOLEAN      NOT NULL,
    actor_id      BIGINT,
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CHECK (scope_type IN ('guild', 'category', 'channel'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_command_routing_policy_scope
    ON command_routing_policy (
        guild_id,
        scope_type,
        COALESCE(scope_id, -1),
        cog_name
    );

CREATE INDEX IF NOT EXISTS idx_command_routing_policy_guild_cog
    ON command_routing_policy (guild_id, cog_name);
