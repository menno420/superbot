# 2026-06-10 — Batch 1: low-risk runtime truth/clarity (PR #650)

**Arc:** parallel-lane implementation session (Agent 1 of 2; Agent 2 ran Batch 2
concurrently). Executed the consolidated plan's **Batch 1**
(`docs/planning/consolidated-implementation-plan-2026-06-10.md` §5 — RS04 · RS09 ·
RS13 · RS14 · RS16 · RS11-rename) end-to-end: source-verify each finding → fix →
test → full CI mirror → draft PR at first push (Q-0052) → ready at session end.

**Shipped (PR #650 — verify merged):**

- **RS04** — deleted `BindingMutationPipeline._invalidate_cache` (logging-only no-op
  promising "Phase 4c"). Proven: no binding read cache exists (`get_binding` →
  `bindings_db.get_one` hits the DB every call). Module docstring now states the
  honest 6-step contract + the no-cache property; 2 new tests pin it (uncached
  reads; set/clear immediately visible).
- **RS09** — deleted the `core/resources/mutation.py` `ResourceMutationPipeline`
  shell + its contract tests (zero runtime consumers by grep; all methods raised
  NotImplementedError; live owner = `services.resource_provisioning`). Package
  init/tests, `test_no_silent_auto_create` allowlist, consistency-ledger cells,
  and a `roadmap_setup_platform.md` banner note updated.
- **RS13** — `diagnostics_service` boundary docstring: process-local **sync**
  snapshot registry only; names the adjacent owners it does NOT cover
  (health_snapshot_service · domain read models). Rename deferred per the map.
- **RS14** — `panel_command` **deprecated** (not adopted): zero adopters; the
  Q-0025 scaffold registers panels via `KNOWN_PANEL_COMMANDS`; Settings Phase 2
  (Batch 4) is the successor. Detection stays wired; new test pins the
  `panels_by_source` diagnostics counts.
- **RS16** — `utils/db/migrations.py` responsibility note: `create_tables` =
  frozen pre-001 bootstrap (never gains DDL); all schema changes = new
  `NNN_*.sql`. No historical migrations touched.
- **RS11 rename slice** — `get_economy` → `ensure_and_get_economy` (it INSERTs
  before reading); 6 call sites + exports + 2 test refs + the direct-DB exception
  ledger row, all by grep. (Transaction ownership = Q-0071/Batch 7, untouched.)

**Verification:** `check_quality.py --full` green (8520 passed / 22 skipped);
`check_architecture.py --mode strict` 0 errors; focused suites for every touched
module green; context_map run before each `disbot/` edit.

**Parallel-lane notes (§9):** stayed out of Batch 2 scope entirely
(`command_surface_ledger.py`, its tests, per-cog classifications, Help filtering).
No conflicts encountered. Grooming pass skipped per the parallel-mode convention.
Cross-cutting ledger edits kept surgical (one-token annotations) for easy UNION.

## Decisions made alone (ratify if they matter)

1. **RS04 = delete** the no-op hook (plan allowed implement-or-rename/document;
   deletion + docstring contract is the stronger truth fix — a fake step documented
   honestly is still a fake step).
2. **RS14 = deprecate** (plan offered adopt-or-deprecate). Evidence: zero adopters,
   the scaffold maintains KNOWN_PANEL_COMMANDS, `interface-completion-roadmap.md`
   already says "do not use @panel_command", Settings Phase 2 supersedes, and
   adoption would touch ~18 cogs inside Batch 2's parallel blast radius.
3. **RS11 = single rename** (`ensure_and_get_economy`), not an ensure/get split —
   zero behavior change; split would alter 6 call patterns for no Batch-1 gain.
4. Fixed two **adjacent** stale consistency-ledger cells beyond the named scope
   (bindings "Cache authority ✅ guild_config" — a cache that never existed — and
   the resources "post-Phase 2" wording): same defect class, source-verified.

## Flagged for maintainer / known limits

- `panel_command` deprecation is docstring-level — no lint/invariant blocks a new
  adopter. Fine for now (detection still works); **Batch 4 should finish it**
  (delete the decorator or fold it into the per-domain registrations).
- The new uncached-read pin guards the `get_binding` accessor seam; a cache added
  *inside* `utils.db.bindings.get_one` itself would evade it (unlikely seam, noted).
- Both new binding tests simulate the DB row store — no live-Postgres binding
  round-trip was added (existing live coverage unchanged).

## Context delta

- **Needed but not pointed to:** deciding "is there really no cache?" (RS04) needed
  the sibling pipelines (`settings_mutation`/`participation_mutation`) as the
  reference for what a *real* invalidation step looks like — worth one line in the
  bindings folio. Also the same-name collision: the shell's `ResourceProvisioningError`
  ≠ the live `services.resource_provisioning.ResourceProvisioningError` (two distinct
  classes, same name) — found only by grep; exactly the CLAUDE.md name-collision class.
- **Pointed to but didn't need:** the context-map hook's full recommended read set
  (all importers) for docstring-only edits — skimming sufficed; the hook's
  once-per-file display is the right weight, no change proposed.
- **Discovered by hand:** `scripts/new_subsystem.py:217` registers panels via
  `KNOWN_PANEL_COMMANDS` — the decisive RS14 evidence; the
  `test_no_silent_auto_create.py` allowlist comment had pre-authorized the shell
  deletion ("future cleanup PR may remove this file").
- **One change that would have helped:** the consolidated plan was unusually precise
  (file:line evidence made verification fast); a per-item "decision pre-made vs
  implementer's call" marker would have saved the adopt-vs-deprecate deliberation.
