# Discord smoke-test checklist

> **Status:** SuperBot 2.0 — PR-05.
> Run this checklist before merging anything that touches startup,
> task ownership, the consistency report, or the readiness snapshot.

This page is the manual companion to the readiness snapshot
(`services.platform_consistency.build_readiness_snapshot()`).  Every
checklist item below corresponds to a field on the
`ReadinessSnapshot` dataclass, so once you have looked at the live
`!platform diagnostics` output you can tick each item directly from
the rendered snapshot.

The doc-test `tests/unit/docs/test_smoke_test_checklist.py` pins
this 1:1 correspondence, so adding a field to `ReadinessSnapshot`
without surfacing it here (or removing one without removing the
matching bullet) will fail CI.

---

## Boot path

- [ ] **Boot completes without unhandled exception** — `bot.log`
      shows the "Starting bot..." line followed by the discord.py
      ready event.
- [ ] **Runtime lock acquired** — `services.runtime` log line
      "Runtime lock acquired ...".  A loser replica should exit with
      code 0; a leader should proceed to startup.
- [ ] **Heartbeat task spawned** — heartbeat task appears in the
      managed task supervisor.  See *tasks > active_names* below.

## Health & readiness probes

- [ ] **`GET /health`** returns 200 with non-empty body.
- [ ] **`GET /ready`** returns 200 (or 503 until `bot.is_ready()`
      flips).
- [ ] **`GET /metrics`** returns a Prometheus expo with at least
      `task_outcome_total` and `identity_contract_findings_total`.

## Consistency report

Inspect `!platform consistency` and the readiness snapshot's
`consistency_overall_status` / `consistency_blocking_sections`:

- [ ] **`consistency_overall_status` is CLEAN** *or* every WARNING /
      FATAL / SKIPPED section in `consistency_blocking_sections`
      has been triaged.
- [ ] **`consistency_report_at`** is recent (within the last hour
      on a long-running replica).  A `None` value indicates
      `collect_report` was never called — run `!platform consistency`
      to populate the cache.
- [ ] **No collector raised** — every typed `ReadinessKind` must
      have a corresponding section in the report, all stamped by
      the orchestrator.

## Startup outcomes

Inspect the readiness snapshot's `startup_outcomes`:

- [ ] **`command_surface_ledger`** outcome.success == True
- [ ] **`settings_registry`** outcome.success == True
- [ ] **`customization_catalogue`** outcome.success == True
- [ ] **`resource_provisioning_catalogue`** outcome.success == True

A failure here is non-fatal at boot but blocks subsequent setup /
diagnostic surfaces.  Cross-check the `bot.log` warning for the
exception summary.

## Catalogue & registry state

Inspect the snapshot's `catalogues` block (also surfaced as
`get_cached_*()` accessors):

- [ ] **`ledger_built`** == True (`command_surface_ledger.get_cached_ledger()` non-null)
- [ ] **`settings_registry_built`** == True
- [ ] **`customization_catalogue_built`** == True
- [ ] **`provisioning_catalogue_built`** == True

If any of these are False, the corresponding `startup_outcomes`
entry should explain why.

## Background tasks

Inspect the snapshot's `tasks` block (or `!platform tasks`):

- [ ] **`tasks_active_count`** matches the expected set (heartbeat,
      health server, session_gc, process_memory_sampler, optional
      scheduler — see `tasks_active_names` for the canonical list).
- [ ] **No task showing up twice** — PR-02b removed the
      double-supervision of the automation scheduler.  Two entries
      with the same name is a regression.

## Setup wizard smoke

- [ ] **`!setup`** opens the wizard hub without raising.
- [ ] **`/setup-status`** returns the current draft state.
- [ ] **`/setup-reset`** clears staged operations (read-only smoke:
      stage one no-op operation, then run `/setup-reset`).
- [ ] **Final Review apply** runs through `services.setup_operations.
      apply_operations` (verify via the audit row: per-op
      mutation_id present, per-op error empty).

## Help / navigation

- [ ] **`!help`** dropdown opens; the route resolver does not raise.
- [ ] **`!help <subsystem>`** routes to the canonical hub for every
      hub-routable subsystem (smoke a few: economy, games, admin).
- [ ] **`!platform setup-readiness`** renders the per-guild
      inventory and matches the readiness snapshot's setup blocker
      summary.

## Shutdown drain

Trigger `SIGTERM` (or run `kill -TERM $PID`) and observe:

- [ ] **Heartbeat stops** — log line "Runtime lock released" or
      similar within 1 s.
- [ ] **Managed task drain completes within 5 s** — every entry in
      `tasks.active()` is either done or has been cancelled.
- [ ] **DB pool closed** — final log line "Bot exiting cleanly" or
      no `asyncpg` warnings on stderr.

---

## Updating this checklist

When `ReadinessSnapshot` gains a new field, add a matching bullet
above (and a doc-test entry in
`tests/unit/docs/test_smoke_test_checklist.py`).  When a field is
removed, remove the bullet.  CI enforces the 1:1 correspondence so
the snapshot and the checklist cannot drift.
