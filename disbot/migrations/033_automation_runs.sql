-- Migration 033: automation_runs (Phase 9g / Track 6 PR 15).
--
-- Append-only history of every automation rule execution attempt.
-- One row per ``execute_rule(...)`` call from
-- :func:`services.automation_executor`. Stays append-only so the
-- operator can read the audit trail without truncation risk.
--
-- Schema
-- ------
-- id                BIGSERIAL primary key.
-- rule_id           FK to ``automation_rules.id`` with
--                   ``ON DELETE CASCADE`` so deleting a rule cleans
--                   up its history.
-- guild_id          Redundant with rule_id's guild but indexed for
--                   per-guild queries (``!automation history``).
-- status            One of: ``queued`` (claimed by the scheduler),
--                   ``running`` (executor in flight), ``success``,
--                   ``failure``, ``skipped`` (e.g. quiet-hours).
-- dry_run           True when the executor ran in dry-run mode and
--                   did NOT perform any Discord-side side effect.
-- idempotency_key   UUID-derived string unique per
--                   (rule_id, scheduler-tick). Enforces "claim once
--                   per tick" so two concurrent schedulers cannot
--                   double-run the same rule.
-- started_at        When the executor began work.
-- finished_at       When the executor finished (success or failure).
-- result_summary    JSONB; per-action-kind summary. e.g.
--                   ``{"sent_to": 123, "skipped": 0}`` for
--                   ``send_message``.
-- error             Exception text on failure; truncated by the
--                   executor.
--
-- Indexes
-- -------
-- * ``UNIQUE (idempotency_key)`` — defense-in-depth against
--   double-run.
-- * ``(rule_id, started_at DESC)`` — per-rule history queries.
--
-- Rollback
-- --------
-- ``DROP TABLE IF EXISTS automation_runs`` removes the history.
-- The ``automation_rules`` table is untouched (no FK in that
-- direction).
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS automation_runs (
    id               BIGSERIAL    PRIMARY KEY,
    rule_id          BIGINT       NOT NULL REFERENCES automation_rules(id) ON DELETE CASCADE,
    guild_id         BIGINT       NOT NULL,
    status           TEXT         NOT NULL CHECK (
        status IN ('queued', 'running', 'success', 'failure', 'skipped')
    ),
    dry_run          BOOLEAN      NOT NULL DEFAULT FALSE,
    idempotency_key  TEXT         NOT NULL UNIQUE,
    started_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    finished_at      TIMESTAMPTZ,
    result_summary   JSONB        NOT NULL DEFAULT '{}'::JSONB,
    error            TEXT
);

CREATE INDEX IF NOT EXISTS automation_runs_rule_idx
    ON automation_runs (rule_id, started_at DESC);
