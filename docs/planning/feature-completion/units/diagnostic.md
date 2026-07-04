# Diagnostics — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `diagnostic` · **Type:** server-fn · **Family:** platform
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> Source: `disbot/cogs/diagnostic_cog.py` (`!diagnostics`/`!diag` hub + `!ping`) ·
> `disbot/cogs/diagnostic/platform_group.py` (`!platform` + 30+ typed routes) ·
> `disbot/services/health_snapshot_service.py` (bounded redaction-aware read model) ·
> `disbot/services/health_findings_service.py` (sole-writer findings lifecycle, Q-0097) ·
> `disbot/cogs/health_maintenance_cog.py` (daily retention) · migration 057 · folio
> `docs/subsystems/health-diagnostics.md`

> Assessed during the completion-first arc (Q-0209). Diagnostics surfaces **bot/subsystem operational
> health** to operators: a deterministic, per-source-isolated, audience-redacted `HealthSnapshot` (nine
> adapters), 30+ `!platform` typed routes, and a persistent **findings store** with an operator-managed
> lifecycle (`resolve`/`ignore`/`reopen`) through the **sole-writer** `health_findings_service.set_status`
> (emits `audit.action_recorded` on a genuine change, AST-guarded), plus 30-day retention on a daily
> loop. Read-only/observational (no remediation), administrator-gated, owner-redacted. The honest gaps:
> a hub-completeness doc claim (startup/findings are typed-only by design), pagination for dense subviews,
> and the owner-led live health walk.

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise delivered** — `!diagnostics` hub + `!platform health/startup/findings` render the
      bounded snapshot; per-subsystem checks (runtime/gateway/db/consistency/startup/extensions/tasks/
      diagnostics/ai/resources); findings resolve/ignore/reopen + daily retention.
- [x] **Every best-in-class sub-option** — per-subsystem checks, findings lifecycle, retention,
      grouped-findings opt-in, audience redaction, owner AI health tool.
- [x] **Failure modes honest** — per-source isolation (`_safe`/`_safe_async`): one failed provider →
      an `_error` key, never crashes the snapshot.
- [x] **Idempotent** — findings upsert by fingerprint (occurrence recount); no-op transitions don't audit.

### B. Reachability & UI
- [x] **A command panel exists** — `!diagnostics` → 7-button hub; `!platform` → platform hub + 30+ typed
      routes.
- [x] **Reachable every natural way** — entries `diagnostics`/`ping`/`platform` + two Help hooks
      (`build_help_menu_view` + `build_platform_help_menu_view`) + Admin-hub child.
- [N/A] **Integrated into Setup** — observational tool, not onboarding config.
- [x] **Return navigation** — ✓ "↩ Back" on sub-panels; the dense `!platform consistency` / `!platform
      findings` command output now paginates (◀ Prev / Next ▶, `_PaginatorView`) instead of dropping
      trailing sections / capping rows — punch #2 DONE 2026-06-30 (PR #1584).
- [x] **In-place, not spammy** — `safe_defer`+`safe_edit` throughout.

### C. Convenience
- [x] **Defaults** — `!findings` defaults to open status; default channels staff/bot-spam.
- [x] **Clear feedback** — lifecycle transitions report applied/unchanged/not_found; findings count
      summary; redaction footer (owner vs admin view).

### D. Authority & safety
- [x] **Authority re-checked at callback** — all commands `administrator`; registry tier administrator;
      audience redaction (`project_for_audience`) downscopes admin vs owner.
- [x] **Findings writes through the audited sole-writer seam** — `health_findings_service.set_status`
      emits `audit.action_recorded` on a genuine change (AST-guarded sole writer;
      `test_inv_health_findings_service.py`).
- [N/A] **Provisioning pipeline** — read-only; no resource creation / no remediation.
- [x] **Reuses governance** — governance healthcheck folded into the consistency report; administrator
      floor; owner-gated AI health tool.

### E. Configuration
- [x] **Retention setting** — `RETENTION_DAYS=30` (override-able); daily loop cadence; `HEALTH_GROUPED_FINDINGS`
      env opt-in for error grouping.
- [N/A] **config-input widgets** — mostly N/A (observational; provider registration is code-time).
- [x] **Everything configurable that should be** — retention + grouping are the meaningful knobs.

### F. Wiring & discoverability
- [x] **Registry** — key `diagnostic`, `visibility_tier: administrator`, entries
      `diagnostics`/`ping`/`platform`, `parent_hub: admin`, capabilities (`diagnostic.health.view`,
      `diagnostic.latency.check`).
- [x] **Discoverable in Help** — both Help hooks; the platform hub regrouped under Admin (#1290).

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_health_snapshot_service.py`, `test_health_redaction.py`,
      `test_health_observations.py`, `test_platform_diagnostics_commands.py`, `test_lifecycle_diagnostics.py`,
      `test_startup_health_pr3.py`.
- [x] **Authority tests** — sole-writer AST guard (`test_inv_health_findings_service.py`), redaction tests,
      command `administrator` gates.
- [x] **Mutation-seam tests** — `test_health_findings_service.py` (set_status applied/unchanged/not_found
      + audit on genuine change), real-Postgres `test_health_findings_integration.py`, migration-057 pin,
      `test_platform_commands.py` (finding lifecycle), `test_health_maintenance_cog.py` (retention loop).
- [ ] **Live walkthrough recorded** — pending → punch #3.
- [ ] **Owner ✔** — pending → punch #4.

## Punch-list (clear these to certify)
1. ✅ **Platform-hub completeness claim** — DONE 2026-06-30 (PR #1575). `startup` + `findings` (both
   read-only health reports) are now grouped into the `!platform` hub's **Runtime/status** category
   select (audience-preserving `_dispatch` branches; `findings` shows the default `open` status, the
   typed `!platform findings <status>` keeps the status filter). The panel docstring + the lockstep
   hub-view test were updated together; the `finding` *lifecycle mutation* stays excluded from the
   read-only Selects (the segregated Mutations row is the only write surface).
2. ✅ **Pagination for dense subviews** — DONE 2026-06-30 (PR #1584). `!platform consistency` and
   `!platform findings` now render through `build_consistency_pages` / `build_findings_pages` and send
   the existing `_PaginatorView` when there is more than one page, so the full report is reachable via
   ◀ Prev / Next ▶ instead of `build_consistency_embed` *dropping* trailing sections / `build_findings_embed`
   capping to `_HEALTH_FINDINGS_SHOWN` rows (single-page output is byte-identical to before). The findings
   fetch was raised 15 → 60 so the extra pages have content. (The `!platform` hub-*panel* keeps its
   single-embed select navigation by design.)
3. **Maintainer live health walk** *(needs-live-bot / owner)* — boot, `!platform health` as admin vs owner
   (redaction), findings lifecycle → audit, grouped-findings, recurrence across restarts, the owner AI
   health tool, with screenshots.
4. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."
5. ✅ **Health metrics reconcile** — DONE 2026-06-30 (PR #1584). The bot-awareness plan §3.6
   collection-observability metrics are now implemented (not deferred): `health_snapshot_collection_seconds`
   (Histogram, `lane=sync|async`), `health_snapshot_source_failure_total` (Counter, `source`), and
   `health_snapshot_redaction_total` (Counter, `audience`) in `services/metrics.py`, wired at the snapshot
   seams — duration in `collect_snapshot`/`collect_cached_snapshot`, source-failure in `_safe`/`_safe_async`,
   redaction-outcome in `project_for_audience`. Low-cardinality labels only (the unbounded source values
   are bounded by the fixed adapter set).

## Evidence
- **Tests:** `tests/unit/services/test_health_snapshot_service.py` · `…/test_health_findings_service.py` ·
  `tests/unit/invariants/test_inv_health_findings_service.py` · `tests/unit/db/test_health_findings_integration.py` ·
  `…/test_migration_057_operational_health_findings.py` · `tests/unit/runtime/test_platform_commands.py` ·
  `tests/unit/cogs/test_health_maintenance_cog.py` · `…/test_platform_health_embed.py`
- **Walkthrough:** pending (punch #3) · **Owner sign-off:** pending (punch #4)

## Verdict
Diagnostics is a **structurally complete, fully-audited, read-only** health surface — a deterministic
per-source-isolated redaction-aware snapshot, 30+ platform routes, and a sole-writer findings lifecycle
with audit + daily retention, comprehensively tested (incl. real-Postgres + an AST sole-writer guard).
It is **not yet `✔ certified`**, but the **offline** punch-list is now CLOSED — hub-completeness (#1,
#1575), dense-subview pagination (#2, #1584), and the metrics reconcile (#5, #1584) are all done. The
only remaining gaps are the **owner-led live health walk + sign-off** (#3/#4, `[needs-live-bot]`/`[owner]`).
No safety/audit/dead-end issues found.
