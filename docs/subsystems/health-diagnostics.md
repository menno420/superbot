# Health / diagnostics subsystem — folio

> **Status:** `living-ledger` (area index). Source + `docs/current-state.md` win.
> **Last updated:** 2026-06-06.

## What & where

Health/diagnostics turns existing runtime, startup, consistency, resource, and AI
signals into bounded operator-facing snapshots. Start in
`disbot/services/health_contracts.py`, `disbot/services/health_snapshot_service.py`,
`disbot/services/health_findings_service.py`, `disbot/services/diagnostics_service.py`,
`disbot/services/platform_consistency.py`, `disbot/cogs/diagnostic_cog.py`, and
`disbot/views/diagnostic/`. Persistent findings use
`disbot/utils/db/health_findings.py` and migration
`disbot/migrations/057_operational_health_findings.sql`.

## Rules & approved structures (binding — link, don't restate)

- `docs/bot-awareness-implementation-plan.md` is the execution/status authority;
  `docs/bot-awareness-diagnostics-plan.md` is repository-map context only.
- Preserve the typed, read-only health contracts and the two collection lanes:
  cached/synchronous facts versus bounded asynchronous probes. Preserve provider
  isolation and redaction before operator or AI rendering.
- `docs/runtime_contracts.md`, `docs/ownership.md`, and
  `docs/platform-consistency-ledger.md` own lifecycle, write, and consistency rules.
  `docs/smoke-test-checklist.md` is doc-test-pinned.
- `diagnostics_health_snapshot` is read-only and owner-gated. AI may explain facts,
  but may not remediate, mutate configuration, query arbitrary tables, or resolve
  findings.

## Current state

- Bot-awareness PR1–PR6 are shipped: typed contracts + aggregator, deterministic
  `!platform health`, startup-health snapshot, opt-in grouped recent-error findings,
  the owner-gated AI tool, and persistent operational-health findings.
- Grouping is controlled by `HEALTH_GROUPED_FINDINGS`; persistent dedupe/counting is
  backed by migration `057` and `health_findings_service`.
- Deterministic and DB paths are bootable/testable in the sandbox, but the sandbox has
  no AI provider key and the persistence/dedupe integration walk is still owed. Do **not** claim that the model's live tool selection is verified.
- The accepted operational baseline is #535; it is not a new live retest. Dense
  DiagnosticCog platform subviews remain a known UX follow-up.

## Plans / pending approval

No unshipped bot-awareness implementation phase is pending. Any new remediation or
write-capable diagnostics flow requires a new approved plan and ownership review;
the shipped health surface is deliberately observational.

## Ideas (not approved)

Pagination for dense platform subviews is a known UX idea. Treat broader AI
explanation/tool expansion through `docs/subsystems/ai.md` and the ideas promotion
path rather than adding ad-hoc diagnostics tools.

## Next candidates

1. **Close the migration-`057` persistence/dedupe integration gap (ready — test-only,
   sandbox-verifiable, no runtime/architecture change).** Existing coverage mocks the
   DB: `tests/unit/services/test_health_findings_service.py` monkeypatches `svc._db`,
   and its docstring **wrongly** claims the `ON CONFLICT` path "is integration-tested
   against real Postgres" — no such test exists. Two blockers the implementer must know:
   `tests/conftest.py` has **no** Postgres fixture, and CI (`code-quality.yml`) runs
   **no** Postgres service, so a real-DB test must **skip cleanly** in CI. Deliver, in
   one PR: a CI-safe static SQL-shape test for migration `057` (mirror
   `tests/unit/db/test_migration_051_main_server_backfill.py`) + a real-Postgres
   integration test (module-local `postgres_pool` fixture, `pytest.skip` when
   `DATABASE_URL` is unreachable) exercising upsert → occurrence delta-add → reopen-on-
   recurrence → keep-ignored → `list`/`count` → roll-up-then-prune, and correct the
   false docstring. Boot local Postgres per the journal runbook to run it live.
2. Maintainer live-test the production AI path: owner receives
   `diagnostics_health_snapshot`; a non-owner admin does not. **Sandbox cannot do
   this** (no AI-provider key) — it is owed to the maintainer on production.
3. Maintainer live-test grouped findings and recurring-failure count behavior
   (`HEALTH_GROUPED_FINDINGS=1` + induced repeated errors; recurrence count across a
   restart overlaps candidate #1's persistence path).

## Related docs

`docs/current-state.md`, `docs/bot-awareness-implementation-plan.md`,
`docs/bot-awareness-diagnostics-plan.md`, `docs/platform-consistency-ledger.md`,
`docs/smoke-test-checklist.md`, `docs/subsystems/ai.md`.
