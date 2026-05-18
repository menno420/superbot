-- Migration 022: subsystem_bindings + binding_audit_log (Phase 2b).
--
-- Replaces the raw-string `channel_id` / `role_id` pattern in
-- `guild_settings` with a typed binding table.  Phase 2b ships the
-- table + audit log; Phase 4c diagnostics + Phase 6.5 routing + Phase
-- 7 wizard all read from here.  Settings-KV legacy fallback stays in
-- place until `bindings.primary` (Phase 1d declared flag) flips,
-- which is gated on Phase 2d's feature-flag runtime.
--
-- Schema decisions:
--
--   * Composite PK on (guild_id, subsystem, binding_name) — bindings
--     are scope-aware from day one.  Same channel can be a different
--     binding in different subsystems.
--   * CHECK constraints on `kind` and `status` mirror the Python enums
--     (core.runtime.subsystem_schema.BindingKind +
--     core.resources.status.ResourceStatus).  Phase 2b's invariant
--     test `tests/unit/invariants/test_binding_constraints_alignment.py`
--     pins the literals.
--   * `target_id` is nullable — clearing a binding sets it to NULL
--     and writes an audit row; the table row is retained so the
--     subsystem's slot is still declared.
--   * `binding_audit_log` is append-only.  Indexed on
--     `(guild_id, at)` for time-range queries and `(mutation_id)` for
--     cross-pipeline correlation.
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS subsystem_bindings (
    guild_id           BIGINT       NOT NULL,
    subsystem          TEXT         NOT NULL,
    binding_name       TEXT         NOT NULL,
    kind               TEXT         NOT NULL,
    target_id          BIGINT,
    status             TEXT         NOT NULL DEFAULT 'unresolved',
    last_validated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    version            INTEGER      NOT NULL DEFAULT 1,
    PRIMARY KEY (guild_id, subsystem, binding_name),
    CHECK (kind IN ('channel', 'role', 'category', 'thread', 'member')),
    CHECK (status IN ('bound', 'unresolved', 'missing', 'invalid'))
);

CREATE INDEX IF NOT EXISTS idx_subsystem_bindings_guild_status
    ON subsystem_bindings (guild_id, status);

CREATE INDEX IF NOT EXISTS idx_subsystem_bindings_guild_subsystem
    ON subsystem_bindings (guild_id, subsystem);

-- Append-only audit log.  One row per mutation (set or clear).
-- ``actor_type`` discriminator distinguishes user-initiated mutations
-- (``'user'``) from system-driven ones (``'backfill'``, ``'system'``).
CREATE TABLE IF NOT EXISTS binding_audit_log (
    id              BIGSERIAL    PRIMARY KEY,
    mutation_id     UUID         NOT NULL,
    guild_id        BIGINT       NOT NULL,
    subsystem       TEXT         NOT NULL,
    binding_name    TEXT         NOT NULL,
    actor_id        BIGINT       NOT NULL,
    actor_type      TEXT         NOT NULL DEFAULT 'user',
    action          TEXT         NOT NULL,
    old_target_id   BIGINT,
    new_target_id   BIGINT,
    old_status      TEXT,
    new_status      TEXT,
    at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CHECK (action IN ('set', 'clear', 'backfill'))
);

CREATE INDEX IF NOT EXISTS idx_binding_audit_guild_at
    ON binding_audit_log (guild_id, at);

CREATE INDEX IF NOT EXISTS idx_binding_audit_mutation
    ON binding_audit_log (mutation_id);
