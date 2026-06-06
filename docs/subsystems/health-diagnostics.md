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

## Debug router (if X, inspect Y first)

Health/diagnostics is a **reporting layer**. When it surfaces a problem the root
cause is almost always in the subsystem it *reports on*, not here — don't "fix" the
health system for a failure it merely displays.

- **A finding/health card names a failure (e.g. "role automation")** → the bug is in
  that **execution** subsystem, not health. Jump to that subsystem's folio + debug
  router (e.g. server-management for role/cleanup) and to the **runtime logs** for the
  exact exception — grouped findings intentionally scrub/aggregate the raw trace.
- **A repeated error you can't pinpoint from the snapshot** → findings are
  fingerprinted in `services/health_findings_service.py` / `utils/db/health_findings.py`
  (detail redacted); the unredacted exception lives in runtime logs, not the DB row.
  Use the finding's `related_subsystem` / `related_command` to locate it.
- **"Consistency" / bindings-backfill / config-arbitration warnings** → a **separate**
  layer: `services/platform_consistency.py`. Distinguish benign warnings from blockers
  via `docs/platform-consistency-ledger.md`. The health snapshot renders only
  **WARNING/FATAL** sections as "needs attention"; **SKIPPED** ("not applicable / no
  data / no context") go to `facts.skipped_sections`, not findings
  (`_build_consistency_subsystem`, 2026-06-06). Known-benign states (verified live):
  **Bindings SKIPPED** = health asked from a **DM** (runs CLEAN inside a guild);
  **Binding backfill SKIPPED** = no checkpoint rows (no backfill has run — normal);
  **Config arbitration WARNING with `missing=0`** = legacy reads while
  `bindings.primary` is not production-flipped (the designed pre-flip state — ledger §6).
- **`diagnostics_health_snapshot` returned nothing for a user** → it's owner-gated and
  read-only by design; a non-owner getting nothing is correct, not a bug.
- **A health card itself errors / is empty** → check provider isolation in
  `health_snapshot_service` (a failing provider must degrade, not crash the card) and
  the cached-vs-async lane split in `health_contracts`.

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
- Deterministic and DB paths are bootable/testable in the sandbox. The migration-`057`
  persistence/dedupe/retention SQL is now covered by a real-Postgres integration suite
  (`tests/unit/db/test_health_findings_integration.py`) plus a CI-safe static SQL-shape
  pin (`tests/unit/db/test_migration_057_operational_health_findings.py`). The sandbox
  still has no AI provider key — do **not** claim that the model's live tool selection
  is verified.
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

> **DONE (this session):** the migration-`057` persistence/dedupe/retention integration
> gap is closed — test-only, no runtime/architecture change. New
> `tests/unit/db/test_health_findings_integration.py` (real-Postgres; module-local
> `postgres_pool` fixture that `pytest.skip`s when `DATABASE_URL` is unset/unreachable,
> so CI stays green) exercises upsert → occurrence delta-add + `last_seen` advance →
> reopen-on-recurrence → keep-ignored → `list`/`count` by status → roll-up-then-prune
> (summed `total_occurrences`, open rows survive) → `record_findings` /
> `run_retention` end-to-end. New `tests/unit/db/test_migration_057_operational_health_findings.py`
> is the CI-safe static SQL-shape pin (tables, fingerprint PKs, status/severity CHECK
> sets, the `(status, last_seen_at)` index, and the writer's ON CONFLICT delta-add /
> reopen `CASE` / roll-up `GREATEST`/`LEAST` / prune `WHERE status IN`). The false
> "integration-tested against real Postgres" docstring in
> `test_health_findings_service.py` is corrected to point at these files. Verified live:
> local Postgres boot → migration `057` applies clean → `\d` on both tables → clean bot
> boot with `Startup health findings: recorded=0 pruned=0`.

1. Maintainer live-test the production AI path: owner receives
   `diagnostics_health_snapshot`; a non-owner admin does not. **Sandbox cannot do
   this** (no AI-provider key) — it is owed to the maintainer on production.
2. Maintainer live-test grouped findings and recurring-failure count behavior
   (`HEALTH_GROUPED_FINDINGS=1` + induced repeated errors). The cross-restart recurrence
   *persistence* path is now integration-tested (see DONE above); the live Discord render
   of `!platform findings`/`health`/`startup` remains owed to a maintainer walk.

## Related docs

`docs/current-state.md`, `docs/bot-awareness-implementation-plan.md`,
`docs/bot-awareness-diagnostics-plan.md`, `docs/platform-consistency-ledger.md`,
`docs/smoke-test-checklist.md`, `docs/subsystems/ai.md`.
