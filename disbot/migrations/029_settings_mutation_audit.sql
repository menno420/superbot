-- Migration 029: settings_mutation_audit (S4).
--
-- Append-only audit log for every mutation that flows through
-- :class:`services.settings_mutation.SettingsMutationPipeline`.
-- One row per state change.  Rollback is a NEW audit row, never an
-- UPDATE.
--
-- The pipeline is the canonical write path for scalar guild settings
-- declared by :class:`core.runtime.subsystem_schema.SettingSpec`.
-- Existing direct callers of ``db.set_setting`` are allowlisted by
-- ``tests/unit/invariants/test_no_direct_settings_keys_writes.py`` and
-- will migrate to the pipeline per-subsystem in S10.
--
-- Audit shape:
--
--   * ``mutation_type='set_value'`` — writes a scalar SettingSpec value.
--     Keys: ``(subsystem, name)`` identifies the SettingSpec;
--     ``settings_key`` is the canonical key string from
--     :mod:`utils.settings_keys`.  The redundant ``settings_key`` is
--     retained so the audit table is queryable without joining the
--     schema registry.
--     Values: ``prev_value_raw`` / ``new_value_raw`` carry the
--     transition as strings (the legacy KV is string-typed); typed
--     coercion lives in the pipeline.
--
-- Schema decisions:
--
--   * ``mutation_type`` and ``actor_type`` CHECK literals mirror the
--     Python constants in :mod:`services.settings_mutation`.  An
--     alignment test pins them.
--   * ``actor_id`` is nullable — ``actor_type='system'`` records
--     CI / scripted writes with ``actor_id=NULL``.
--   * Indexed on ``(settings_key, at)`` and ``(guild_id, at)`` for the
--     two common query shapes ("history of this setting" and "recent
--     changes for this guild").  ``mutation_id`` indexed for
--     cross-pipeline correlation.
--
-- Actor model (mirrors user_participation_audit / migration 028):
--
--   * ``actor_type='user'``      — a Discord member initiated the
--                                  change (typically admin-tier).
--   * ``actor_type='moderator'`` — moderator-initiated.  Reserved for
--                                  future moderation tooling.
--   * ``actor_type='admin'``     — admin-initiated.  Reserved for
--                                  future admin tooling that wants to
--                                  distinguish from ``'user'``.
--   * ``actor_type='system'``    — CI seeds, scripted ops.
--                                  ``actor_id`` may be NULL.
--   * ``actor_type='backfill'``  — reserved for future logical
--                                  migrations.  Currently no callers.
--
-- Rollback: ``DROP TABLE IF EXISTS settings_mutation_audit`` removes
-- this audit history.  The legacy ``guild_settings`` KV table is
-- untouched by this migration and remains the authoritative store.
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS settings_mutation_audit (
    id                  BIGSERIAL    PRIMARY KEY,
    mutation_id         UUID         NOT NULL,
    guild_id            BIGINT       NOT NULL,
    subsystem           TEXT         NOT NULL,
    name                TEXT         NOT NULL,
    settings_key        TEXT         NOT NULL,
    prev_value_raw      TEXT,
    new_value_raw       TEXT         NOT NULL,
    actor_id            BIGINT,
    actor_type          TEXT         NOT NULL DEFAULT 'user',
    mutation_type       TEXT         NOT NULL,
    at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CHECK (mutation_type IN ('set_value')),
    CHECK (actor_type IN
        ('user', 'moderator', 'admin', 'system', 'backfill'))
);

CREATE INDEX IF NOT EXISTS idx_settings_mutation_audit_key_at
    ON settings_mutation_audit (settings_key, at);

CREATE INDEX IF NOT EXISTS idx_settings_mutation_audit_guild_at
    ON settings_mutation_audit (guild_id, at);

CREATE INDEX IF NOT EXISTS idx_settings_mutation_audit_mutation
    ON settings_mutation_audit (mutation_id);
