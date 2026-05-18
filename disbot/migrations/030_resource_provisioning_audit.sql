-- Migration 030: resource_provisioning_audit (S4.5).
--
-- Append-only audit log for every mutation that flows through
-- :class:`services.resource_provisioning.ResourceProvisioningPipeline`.
-- One row per provisioning attempt — successful, declined, failed,
-- or permission-blocked.  Rollback is a NEW row, never an UPDATE.
--
-- The pipeline is the canonical creator/binder of Discord resources
-- (channels, roles, categories).  Existing direct callers of
-- ``guild.create_*`` are grandfathered legacy paths allowlisted by
-- ``tests/unit/invariants/test_no_silent_auto_create.py``; they will
-- migrate to the pipeline per-subsystem in S10.
--
-- Audit shape:
--
--   * ``mutation_type='provision'`` — the pipeline ran a provisioning
--     request.  ``mode`` distinguishes ``use_existing`` (the operator
--     selected an already-existing resource) from ``create`` (the
--     pipeline created a new resource on Discord).
--     ``outcome`` records what actually happened.
--
-- Outcomes (defense-in-depth via CHECK):
--
--   * ``success``            — resource created/reused AND binding
--                              written via BindingMutationPipeline.
--   * ``permission_blocked`` — bot lacks the Discord permission to
--                              perform the requested action; no
--                              resource written, no binding written.
--   * ``discord_failed``     — Discord API call raised (HTTPException,
--                              etc.) after permission check passed; no
--                              binding written.
--   * ``binding_failed``     — Discord resource was created/resolved
--                              but BindingMutationPipeline raised.
--                              The resource_id is recorded so an
--                              operator can manually clean up or retry
--                              the bind.  No automatic rollback (the
--                              created resource may carry value the
--                              operator wants to keep).
--   * ``declined``           — pipeline rejected the request before any
--                              Discord call (confirmation missing for
--                              ``mode='create'``, kind mismatch on
--                              ``mode='use_existing'``, etc.).  Listed
--                              so audit history captures rejected
--                              attempts.
--
-- Modes:
--
--   * ``use_existing`` — operator selected an existing resource;
--                        ``existing_id`` is set.
--   * ``create``       — pipeline created a new resource; ``resource_id``
--                        is the newly-created snowflake.
--
-- Kinds (mirror :class:`core.runtime.resource_specs.ResourceKind`):
--
--   * ``channel`` | ``role`` | ``category`` | ``thread``
--
-- Actor model (mirrors settings_mutation_audit / migration 029):
--
--   * ``actor_type='user'`` | ``'moderator'`` | ``'admin'`` |
--                            ``'system'`` | ``'backfill'``
--
-- Indexed on ``(guild_id, at)`` for per-guild history,
-- ``(subsystem, binding_name, at)`` for per-slot history, and
-- ``(mutation_id)`` for cross-pipeline correlation (the same
-- ``mutation_id`` is propagated to the binding-mutation pipeline's
-- audit row, so a "show me everything that happened during this
-- provisioning" query joins on ``mutation_id``).
--
-- Rollback: ``DROP TABLE IF EXISTS resource_provisioning_audit``
-- removes this audit history.  The legacy ``subsystem_bindings``
-- table is untouched (BindingMutationPipeline owns it) and remains
-- the authoritative store for binding state.
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS resource_provisioning_audit (
    id                  BIGSERIAL    PRIMARY KEY,
    mutation_id         UUID         NOT NULL,
    guild_id            BIGINT       NOT NULL,
    subsystem           TEXT         NOT NULL,
    binding_name        TEXT         NOT NULL,
    kind                TEXT         NOT NULL,
    mode                TEXT         NOT NULL,
    outcome             TEXT         NOT NULL,
    created             BOOLEAN      NOT NULL DEFAULT FALSE,
    resource_id         BIGINT,
    suggested_name      TEXT,
    custom_name         TEXT,
    actor_id            BIGINT,
    actor_type          TEXT         NOT NULL DEFAULT 'user',
    mutation_type       TEXT         NOT NULL DEFAULT 'provision',
    error_message       TEXT,
    at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CHECK (mutation_type IN ('provision')),
    CHECK (kind IN ('channel', 'role', 'category', 'thread')),
    CHECK (mode IN ('use_existing', 'create')),
    CHECK (outcome IN
        ('success', 'permission_blocked', 'discord_failed',
         'binding_failed', 'declined')),
    CHECK (actor_type IN
        ('user', 'moderator', 'admin', 'system', 'backfill'))
);

CREATE INDEX IF NOT EXISTS idx_resource_provisioning_audit_guild_at
    ON resource_provisioning_audit (guild_id, at);

CREATE INDEX IF NOT EXISTS idx_resource_provisioning_audit_slot
    ON resource_provisioning_audit (subsystem, binding_name, at);

CREATE INDEX IF NOT EXISTS idx_resource_provisioning_audit_mutation
    ON resource_provisioning_audit (mutation_id);
