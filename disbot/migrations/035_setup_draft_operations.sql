-- Migration 035: setup_draft_operations (Setup Wizard draft staging).
--
-- Per-guild append-only staging area for SetupOperation drafts that
-- the Setup Wizard's sections accumulate before Final Review applies
-- them.  Final Review is the only path that flushes the draft into
-- the canonical mutation pipelines (settings / bindings / resources /
-- automation); every other section writes here and exits.
--
-- Lifecycle (mirrors services/setup_session.py status flow):
--
--   * Section emits a SetupOperation         → INSERT (or replace on
--                                               UNIQUE conflict).
--   * Final Review apply succeeds            → DELETE every row for
--                                               the guild.
--   * setup_session.mark_complete / dismiss  → DELETE every row.
--   * Operator opens the wizard later        → SELECT ordered by seq;
--                                               existing drafts resume.
--
-- Replace-on-conflict semantics
-- -----------------------------
-- A second edit of the same (subsystem, setting_name, binding_name)
-- supersedes the first within a draft so the operator never sees stale
-- staged values for the slot they just re-edited.  The UNIQUE key uses
-- COALESCE on the nullable name columns because PostgreSQL UNIQUE
-- treats NULL as distinct; without COALESCE a draft with both fields
-- NULL would never collide.
--
-- Fields
-- ------
-- guild_id              FK semantics; not a hard FK because guilds
--                       are tracked via Discord snowflakes only.
-- session_started_at    timestamp tying the draft to a specific
--                       wizard run.  Set by services.setup_draft on
--                       the first append for a guild whose draft was
--                       empty; preserved on subsequent appends.
-- seq                   monotonic per-guild insertion order so list
--                       reads return ops in operator-visible order.
--                       Allocated server-side via a SELECT before
--                       INSERT inside one transaction (see
--                       disbot/utils/db/setup_draft.py).
-- op_kind               must match a known OperationKind literal from
--                       services/setup_operations.py.
-- subsystem             owning subsystem name (settings/binding/etc).
-- binding_name          BindingSpec.name; NULL for set_setting ops.
-- setting_name          SettingSpec.name; NULL for binding/resource ops.
-- target_id / target_name / target_kind
--                       optional Discord target identification for
--                       binding ops.
-- value_raw             already-serialised scalar value (TEXT so
--                       SettingsMutationPipeline coerces at apply
--                       time, matching its existing contract).
-- resource_mode / resource_name / existing_id
--                       provisioning fields (create vs use-existing).
-- automation_rule_id / automation_rule_name / trigger_kind /
-- action_kind / trigger_config_json / action_config_json /
-- schedule / timezone
--                       automation-rule fields populated when the
--                       wizard's automation section drafts a rule.
-- actor_id              Discord user id of the operator who staged
--                       the op; preserved through to apply audit.
-- label                 pre-built operator-facing label for the
--                       Final Review embed; sections build it once
--                       so the embed render is cheap.
-- metadata_json         canonical keys: reason, confidence (high|
--                       medium|low), source (scan|preset:<slug>|
--                       smart_suggestion|manual|readiness_repair),
--                       risk (low|medium|high), rollback_note.
-- created_at            insert timestamp.
--
-- Rollback
-- --------
-- DROP TABLE IF EXISTS setup_draft_operations removes the table.
-- Nothing depends on the data — every wizard section can re-stage
-- drafts after a fresh setup launch.
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS setup_draft_operations (
    id                    BIGSERIAL    PRIMARY KEY,
    guild_id              BIGINT       NOT NULL,
    session_started_at    TIMESTAMPTZ  NOT NULL,
    seq                   INT          NOT NULL,
    op_kind               TEXT         NOT NULL,
    subsystem             TEXT         NOT NULL,
    binding_name          TEXT,
    setting_name          TEXT,
    target_id             BIGINT,
    target_name           TEXT,
    target_kind           TEXT,
    value_raw             TEXT,
    resource_mode         TEXT,
    resource_name         TEXT,
    existing_id           BIGINT,
    automation_rule_id    BIGINT,
    automation_rule_name  TEXT,
    trigger_kind          TEXT,
    action_kind           TEXT,
    trigger_config_json   JSONB,
    action_config_json    JSONB,
    schedule              TEXT,
    timezone              TEXT,
    actor_id              BIGINT,
    label                 TEXT         NOT NULL,
    metadata_json         JSONB,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CHECK (op_kind IN (
        'bind_channel', 'bind_role', 'bind_category', 'bind_thread',
        'bind_member', 'clear_binding', 'set_setting',
        'create_channel', 'create_role', 'create_category',
        'add_automation_rule', 'enable_automation_rule',
        'disable_automation_rule'
    ))
);

-- UNIQUE key for replace-on-conflict.  COALESCE handles the NULLable
-- name columns so a draft for the same slot collides reliably.
CREATE UNIQUE INDEX IF NOT EXISTS idx_setup_draft_operations_slot
    ON setup_draft_operations (
        guild_id,
        op_kind,
        subsystem,
        COALESCE(setting_name, ''),
        COALESCE(binding_name, '')
    );

CREATE INDEX IF NOT EXISTS idx_setup_draft_operations_guild_seq
    ON setup_draft_operations (guild_id, seq);
