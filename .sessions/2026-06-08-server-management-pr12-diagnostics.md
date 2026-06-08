# 2026-06-08 — server-management PR12: setup diagnostics & repair

## Arc

Implemented PR12 of the server-management queue: a **read-only diagnostics &
repair layer** for setup. Verified the starting state first (branch
`claude/sleepy-noether-di8W6` at #570 merge; no open PRs; PR11 moderation+roles
shipped, governance deferred Q-0008; PR10 complete) — the hypothesis was correct
in full, no corrections needed.

## Shipped

- **`services/setup_diagnostics.py` (new, service-owned)** — `SetupDiagnosticFinding`
  + `SetupDiagnosticsReport` + `collect_setup_diagnostics` + `staged_repair_ops`.
  Severities (`blocker`/`warning`/`advisory`/`info`) + repairability
  (`auto_repairable`/`conditionally_repairable`/`advisory_only`/`blocked`). It
  **composes existing read-only detectors** (`resource_health.inspect`,
  `utils.db.roles` + `utils.role_feasibility`, `config_arbitration`,
  `cleanup_diagnostics`) — no re-detection, no mutation. Lives in `services/` so
  the PR14 hub reuses it.
- **The one safe auto-repair this slice ships:** dead binding
  (`stale_binding`/`wrong_type`) → a single **`clear_binding`** SetupOperation
  (deterministic, id-free, reversible). Everything else is advisory/blocked by
  design (no auto-create, no role reorder, no second mutation path).
- **`views/setup/sections/diagnostics.py` (new section, order 85)** — grouped
  findings embed + "Stage safe repairs" (drafts `staging_kind="repair"`) +
  "Re-scan". No `recommended_ops_builder` (repairs are staged deliberately, never
  swept by the hub). **Final Review remains the only apply gate** — partial-apply
  rendering inherited for free (repairs are ordinary SetupOperations).
- Tests: `test_setup_diagnostics.py`, `test_diagnostics_section.py`,
  `test_setup_diagnostics_readonly.py` (AST: no mutation pipeline import/call, no
  `setup_draft` import — generation ≠ staging), + registration manifest.
- Docs: status tracker (PR12 subsection + queue), folio, current-state (▶ Next →
  PR13), implementation plan. Also reconciled PR11 → merged via #570.

## Gates

- `check_quality.py --full` green (**7949 passed, 16 skipped**; black/isort/ruff/
  mypy/pytest/check_docs all ✓).
- `check_architecture.py --mode strict` exit 0 (no new findings).
- **Live boot** (Galaxy Bot#6724, boot_id `a4017961`): clean — `setup_cog` loaded,
  logged in, **0 ERROR/CRITICAL/Traceback**; in-process registry confirmed the
  `diagnostics` section (order 85). Postgres brought up via `pg_ctlcluster 16 main
  start` (Debian layout — see Context delta).

## Context delta

- **Needed but not pointed to:** the existing detector seam was the whole game —
  `services/resource_health.py` (`inspect` → per-binding stale/missing/perm/
  hierarchy verdicts) + `cleanup_diagnostics.collect_cleanup_diagnostics` already
  do the detection PR12 needed; the folio's debug-router lists the *services* but
  not that they emit a reusable **findings model** to compose. The
  `setup_draft.append` `staging_kind="repair"` provenance + `source="readiness_repair"`
  were already designed for exactly this and aren't mentioned in any setup doc.
- **Pointed to but didn't need:** `services/setup_blockers.py` /
  `setup_readiness.py` looked like "diagnostics" from the names but are
  *platform-readiness* (is the bot's substrate built?), a different axis from
  *per-guild config health* — reading them was a detour the orientation could
  pre-empt.
- **Discovered by hand:** (1) the **black↔ruff ISC001 trap** is live — black
  collapses a 2-line implicit f-string concat onto one line and ruff ISC001 then
  rejects it; fix by writing one f-string (already a CLAUDE.md theme, now bitten
  in practice). (2) **Postgres here is Debian-packaged** — config lives in
  `/etc/postgresql/16/main/`, not the data dir, so `pg_ctl -D <data>` fails with
  "could not access postgresql.conf"; use `pg_ctlcluster 16 main start`. The
  journal runbook describes the raw `initdb`/`pg_ctl` recipe but not this
  Debian-cluster wrinkle on an already-initialized dir.

## Next

PR13 (deterministic + AI role templates) is unblocked. A natural PR12 follow-up
(not required): a `clear_role_threshold` op-kind so stale auto-role tiers become
auto-repairable, and a conditional "pick-a-target" binding repair — both
deliberately deferred here to keep the first slice deterministic.
