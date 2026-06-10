# Consolidated implementation plan — 2026-06-10

> **Status:** `plan` — **the one live execution queue**, produced by the 2026-06-10
> verification/reconciliation session. It reconciles the two untapped mapping PRs
> (**#646** [runtime/services/workflows](untapped-runtime-services-workflows-map-2026-06-10.md) ·
> **#647** [docs/tests/verification](untapped-docs-tests-verification-map-2026-06-10.md)),
> carries the superseded
> [06-09 consolidated plan](consolidated-productive-session-plan-2026-06-09.md) §5
> gated tail item-by-item (§6 below), and replaces the completed
> [multi-lane scoreboard](multi-lane-execution-plan-2026-06-09.md) as the execution
> pointer. **Source and merged PRs win over this file.** Entry: `docs/current-state.md`
> ▶ Next action → this plan → the batch you're executing.
> **Last updated:** 2026-06-10.

## §1 Verified current state (2026-06-10)

- **Main HEAD at session end:** `46f59f1` (merge of #647; #646 = `25de6f5`); the
  mapping PRs' own baseline was `ed62697` (merge of #645).
- **Open PRs:** none besides this session's docs PR. The maps' "zero open PRs"
  statements were mapping-time facts (the open set was #646/#647 themselves).
- **Merged PRs that moved routing** (all verified live): **#584** (2026-06-08 — PR14
  unified Server Management Hub; initiative structurally complete, only the gated
  PR13 AI layer remains) · **#638** (BTD6 ABR/income decode tail) · **#639**
  (answerability Phase 3) · **#640** (Settings Phases 0+1, Lane 7) · **#641**
  (mapping standard) · **#642** (Help counts + characterization net, Lane 8) ·
  **#643/#644** (mapping Agents A/B) · **#645** (Q-0070 presets posture) ·
  **#646/#647** (the untapped maps, merged + reconciled this session).
- **Stale docs found and fixed this session:** the server-management tracker
  *header* (still queued PR14; its body was already correct), `docs/roadmap.md`
  (PR14 "Next", mapping campaign "Next", adaptive P1C horizon conflict, stale
  verify-merge hedges), `docs/current-state.md` (Next-candidates still queued PR14),
  the implementation-plan header ("PR1–PR9 shipped"), `AGENT_ORIENTATION` (same),
  the A/B reports' mapping-time "live PR" framing (annotated, not rewritten), the
  standard's §2.4 queue rows, the Help/Settings audits' "queued as Lane 7/8" notes,
  and the settings-customization-roadmap banner. The 06-09 consolidated plan §3
  SRV-2 row was stale *at write time* (#584 had merged the day before) — the drift
  class this plan's queue-truth discipline exists to kill.

## §2 PR #646 reconciliation (runtime/services/workflows map)

Every finding was independently re-verified against source this session
(file:line evidence in the map; verification notes in
`.sessions/2026-06-10-verification-cleanup-plan-consolidation.md`).

| Finding | Verdict | Disposition |
|---|---|---|
| RS01 economy purchase = two commits (debit → `add_item`, both shop callbacks, no transaction) | **confirmed** | **Batch 7** (gated on **Q-0071**) |
| RS02 mining mutations orchestrated by cogs/views; no `services/mining_*` exists | **confirmed** | **Batch 7**, after RS01 (gated on Q-0071 + **Q-0072**) |
| RS03 cog-routing write returns `None`; setup dispatcher owns the audit, `prev_value=None` | **confirmed** | **Batch 3** |
| RS04 `BindingMutationPipeline._invalidate_cache` = logging-only no-op ("until Phase 4c") | **confirmed** | **Batch 1** |
| RS05 `event_emitted`/`audit_emitted` = publish-accepted, not subscriber-delivered | **confirmed** | **Batch 9** (contract-first; don't change failure propagation casually) |
| RS06 role-threshold **clears** bypass the audited seam; invariant fences setters only | **confirmed** (xp_roles_panel:229 · time_roles_panel:256 · role_cog:482) | **Batch 3** |
| RS07 chain game owns config/state mutation in-cog | **confirmed** | **Batch 3** (optional third slice) |
| RS08 diagnostic embed builders own raw SQL read models | **confirmed** | **Batch 9** |
| RS09 `core/resources/mutation.py` `ResourceMutationPipeline` = unimplemented shell beside the live `ResourceProvisioningPipeline` | **confirmed** | **Batch 1** |
| RS10 38× local `interaction_check` / 17× `on_timeout` under `views/` (duplicate economy variants in shop_panel) | **confirmed** (counts exact) | **Batch 9** (bounded families) |
| RS11 `get_economy` INSERTs before reading (mutating getter); cross-domain transaction owner unspecified | **confirmed** | rename-cleanup may ride **Batch 1**; the ownership question is **Q-0071** |
| RS12 access-projection availability axis intentionally `skipped` | **confirmed** | stays inert until **Batch 5** (P1C lane) |
| RS13 `diagnostics_service` name overstates scope (sync process-local registry only) | **confirmed** | **Batch 1** (docs/boundary note now; rename later) |
| RS14 `panel_command` declaration API has **zero adopters**, silently best-effort | **confirmed** | **Batch 1** (truth cleanup: adopt-or-deprecate) |
| RS15 AI gateway shim/core naming; core imports services/db | **confirmed** | gated (AI structural work) — docs note only |
| RS16 migration runner + base-table bootstrap DDL in one module; 63 migration files | **confirmed** (count exact) | **Batch 1** (responsibility note only; no historical-migration edits) |
| RS17 setup dispatcher accreting cross-domain mutation policy | **confirmed** | rides **Batch 3** (thin per-domain as RS03-style fixes land) |
| RS18 EventBus process-local (sharding blocker) | **confirmed** | deferred — no multi-process runtime is approved |

**Corrections to the map's "active-current" wording:** none of substance; its §2
"no open PRs" line is annotated as mapping-time state (the map's own preamble now
says so). Its three owner questions route: **Q-RS01 → Q-0071**, **Q-RS02 → Q-0072**
(merged with Q-DT04), **Q-RS03** (event-result semantics) is *not* routed — it is an
engineering-contract choice the Batch 9 implementer proposes with the change itself.

## §3 PR #647 reconciliation (docs/tests/verification map)

| Finding | Verdict | Disposition |
|---|---|---|
| DT01 PR14 queue-truth split across tracker/current-state/roadmap | **split verdict:** tracker *header* stale, tracker *body* already correct (PR14 subsection + Remaining-queue rows); current-state/roadmap genuinely stale | **fixed this session** |
| DT02 mapping campaign still routed "Next" | **confirmed** | **fixed** (roadmap Building section) |
| DT03 A/B reports carry mapping-time live-PR claims | **confirmed** | **annotated** (evidence preserved) |
| DT04 no surface-classification completeness invariant | **confirmed** (ledger tests pin vocabulary/filtering only) | **Batch 2** |
| DT05 Help characterization pins divergence, not the projection contract | **confirmed** (`test_help_render_paths.py` = 23 tests, not 28) | **Batch 6** |
| DT06 Settings Phase 2 lacks a declaration-coverage acceptance test | **confirmed** (`DOMAIN_CONFIG_SUBSYSTEMS` at `customization_catalogue.py:239`; comment says Phase 2 replaces it — not literally labeled "temporary") | **Batch 4** |
| DT07 A02/B03/B06 need owner decisions | **confirmed** | **Q-0073/Q-0074** routed; B06 held (no behavior change) |
| DT08 adaptive P1C horizon conflict + stale P1B wording | **confirmed** | **fixed** (roadmap + adaptive plan status lines) |
| DT09 setup-wizard finalization "Next" without a bounded slice | **confirmed** | **Batch 10** (selection/planning, not implementation) |
| DT10 AI "next" needs a selected contract, not generic continuation | **confirmed** | gated (§7); selection happens in a planning session |
| DT11 BTD6 cutover ready only as a dedicated decision-routed session | **confirmed** | **Batch 8** |
| DT12 platform-consistency ledger = stale-status-shaped contract inventory | **confirmed, already self-aware** (header says "not a current work queue") | no action; do not select it as a queue |
| DT13 mining next slice ambiguous (structures vs game-XP) | **confirmed** | **Q-0072** (also folds the RS02 workshop-boundary option) |
| DT14 health live-test debt closable only in production | **confirmed** | stays owed (§7) |
| DT15 no cross-game terminal-state regression pin | **confirmed** | deferred — characterize when a game slice activates |

**Queue-truth corrections to the map itself:** its Batch 1 (queue-truth
reconciliation) is **done** — this session. Its Batches 2–6 map onto Batches 2/6/4/5/8
below; its Batch 7 (next-slice selection) becomes Batch 10 + the Q-0071–Q-0074 round.
Count nits recorded: 23 help render tests (not 28); 38 invariant files (not 39).

## §4 Documentation cleanup log (this session)

- **Kept active (correct as found):** server-management tracker *body* + folio;
  BTD6 decode-status; games folio; platform-consistency ledger (self-aware);
  multi-lane per-lane executor notes; settings/help audits' design content.
- **Updated (queue truth):** `docs/roadmap.md` · `docs/current-state.md` ·
  server-management tracker header · server-management implementation-plan header ·
  `docs/AGENT_ORIENTATION.md` plan row · adaptive plan status lines (P1B → complete
  #632) · help audit `:8` · settings audit `:6` · settings-customization-roadmap
  banner · mapping standard §2.4 + §7.1.
- **Annotated, evidence preserved (`audit` docs):** mapping A/B reports; both
  untapped maps (merged-as / mapping-time-state preambles).
- **Re-badged `historical`:** [`multi-lane-execution-plan-2026-06-09.md`](multi-lane-execution-plan-2026-06-09.md)
  (scoreboard complete) · [`consolidated-productive-session-plan-2026-06-09.md`](consolidated-productive-session-plan-2026-06-09.md)
  (queue superseded by this plan; kept as the 06-09 reasoning/decision record).
  Already `historical`, small accuracy note added: `server-management-pr14-hub-plan.md`
  (Decision #1 was reversed in-build — Q-0016 registered the hub first-class).
- **Consolidated:** the 06-09 §5 gated tail + the #646/#647 batches → this plan
  (§5/§6). One queue, one home.
- **Still questionable (verify before relying):** `setup_wizard_finalization_plan.md`
  (predates many shipped slices — Batch 10 re-verifies); the roadmap's
  building-roadmap backlogs (`command-expansion-backlog`, `admin-powers
  config-coverage`) remain cross-check-before-use.

## §5 Active executable queue

Ordering rule: batches are sequenced by risk and dependency; **1–4 are
implementation-ready now**, 5–6 are design-ready in order, 7 is decision-gated,
8 is a dedicated session, 9–10 are contract-first/planning. **Parallel lanes:**
Batches 1+2 touch disjoint files and may run as parallel sessions
(`ai-project-workflow.md` §9 conventions); Batch 4 is parallel-safe with 1+2;
Batches 5→6 are strictly sequential; Batch 3 should not run beside 1 (both touch
services) without partitioning by module.

### Batch 1 — Low-risk runtime truth/clarity (RS04 · RS09 · RS13 · RS14 · RS16 · RS11-rename) — executed in **#650** (2026-06-10, verify merged)

> Outcome notes: RS04 = no-op hook **deleted** (no binding read cache exists —
> contract + 2 pinning tests); RS09 = shell **deleted** (consumer proof in the PR);
> RS14 = `panel_command` **deprecated** (known-list canonical until Settings
> Phase 2); RS11 rename = `ensure_and_get_economy`. Details: PR #650 +
> `.sessions/2026-06-10-batch1-runtime-truth-clarity.md`.

- **Objective:** make names/contracts say what the code does; retire the dead shell.
- **Files:** `disbot/services/binding_mutation.py` (`_invalidate_cache` —
  implement a real invalidation target if a cached consumer exists, else rename +
  document the no-op honestly and drop the stale "Phase 4c" language);
  `disbot/core/resources/mutation.py` (prove zero runtime consumers by grep, then
  delete or deprecate the `ResourceMutationPipeline` shell; fix imports/tests/docs
  that referenced it); `disbot/services/diagnostics_service.py` (boundary
  docstring: process-local sync registry vs health-snapshot vs operator read
  services); `disbot/services/customization_catalogue.py` (`panel_command`:
  adopt-or-deprecate — if kept, attach it to at least the known panel commands and
  surface fallback-source counts in diagnostics; if not, mark deprecated);
  `disbot/utils/db/migrations.py` (comment pinning bootstrap-vs-migration
  responsibility; **never edit historical migrations**); optional
  `disbot/utils/db/economy.py` `get_economy` → `ensure_and_get_economy` (or split)
  with callers greped (incl. tests).
- **Tests:** binding cache-observation test across set/clear; import/consumer
  proof for the shell removal; catalogue fallback-count test. Run
  `python3.10 scripts/context_map.py <file>` before each `disbot/` edit.
- **Risk/rollback:** low; renames are the only churn — grep ALL references (incl.
  tests) before renaming. Revert = restore module.
- **Stop:** if the resource shell has a live consumer, deprecate instead of delete.

### Batch 2 — Surface-classification completeness invariant (DT04: FIND-A01/A05/B04/B07) — SHIPPED PR #651 (2026-06-10)

> **Status:** executed 2026-06-10 (parallel session beside Batch 1), **PR #651** —
> verify merge state on live GitHub. The invariant runs twice: at build time
> (`findings.unclassified_entry_points` now populated — hidden-route +
> alias-pile rules) and as a static AST mirror in
> `tests/unit/runtime/test_command_surface_ledger.py` (incl. the two-way
> top-level slash-surface pin + the canonical-literal guard). All 40 hidden
> routes, both alias piles (leaderboard → legacy per **Q-A03**, deathmatch →
> power_user_shortcut), and `/setup-hub` → legacy_duplicate (B07 — the slash
> walker already ingested `extras`; no new seam was needed) are declared.
> Classification-only; Help output byte-identical; alias *display* integration
> deliberately deferred to Batch 6's projection seam.

- **Objective:** every surfaced/hidden/panel-action/slash-legacy/alias route has a
  *deliberate* ledger classification or an explicit exception — drift can't recur
  silently.
- **Files:** `disbot/core/runtime/command_surface_ledger.py` (+ wherever
  classification is declared per-cog); new/extended
  `tests/unit/runtime/test_command_surface_ledger.py` invariant generated from
  loaded/static declarations (not a prose count); then bounded classification
  slices: mining hidden typed commands (A01), utility hidden compat commands (A05),
  panel-action defaults (B04), `/setup-hub` slash classification wiring (B07 — may
  need a small slash-side seam; if it grows, split it out).
- **Tests:** the invariant itself + Help-filter regression (Help tests already pin
  filtering). Q-A03's recommended default (leaderboard aliases → legacy
  classification) is implemented *by* this batch.
- **Risk/rollback:** low-medium; classification-only (no renames/removals — those
  need Q-0073-class decisions). Revert = drop declarations.
- **Stop:** any classification that would *change execution access* — that is
  governance, not ledger work.

### Batch 3 — Service-boundary fixes (RS03 · RS06 · RS17; RS07 optional) — shipped in **#652** (2026-06-10; **RS07 still open**)

> Outcome notes: RS03 = `set_policy` owns old-value read + audit (real
> `prev_value`) + typed `RoutingMutationResult`, with a new import-fence
> invariant; RS17 = dispatcher arm thinned to validation + result consumption;
> RS06 = audited `clear_{time,xp}_threshold` seam methods + the three direct
> clear sites migrated + the threshold fence widened to clears/full-row
> remove. **RS07 (chain service extraction) was deferred** — optional slice,
> new-service design; it remains the only open item in this batch. Details:
> PR #652 + `.sessions/2026-06-10-batch3-service-boundaries.md`.

- **Objective:** writes and their audit live in the domain owner, not the caller.
- **Files:** `disbot/services/command_routing.py` (typed mutation result; audit
  emission with real `prev_value` inside the owner) + `disbot/services/setup_operations.py`
  `_apply_set_cog_routing` consumes the result (RS17: dispatcher thins as each
  domain fixes land); `disbot/services/role_automation.py` gains field-specific
  **clear** methods + migrate the three direct callers
  (`views/roles/xp_roles_panel.py:229`, `views/roles/time_roles_panel.py:256`,
  `cogs/role_cog.py:482`) + widen
  `tests/unit/invariants/test_no_direct_role_threshold_writes.py` to fence clear
  primitives; optional `disbot/services/chain_service.py` extraction (RS07).
- **Tests:** mutation-result contract tests (old/new values, failure semantics);
  audit/cache assertions on clears. **Trap:** keep the
  `test_xp_cog_caching.py::test_threshold_role_mutation_sites_import_invalidator`
  invariant green — the migrated modules must keep importing
  `invalidate_xp_threshold_roles` (journal rule, P0C precedent).
- **Risk/rollback:** medium; behavior-preserving by intent (same writes, owned
  properly). `docs/ownership.md` updates ride the same PR.
- **Stop:** any schema change; any new mutation path that bypasses the audited seam.

### Batch 4 — Settings Phase 2: declaration coverage (DT06 + BTD-2/Q-0064) — core shipped in **#654** (2026-06-10)

> Outcome notes: `DomainPanelSpec` + `SubsystemSchema.domain_panels` replace the
> curated `DOMAIN_CONFIG_SUBSYSTEMS` frozenset (cleanup = first real
> registration; coverage invariant `test_domain_panel_declarations.py` pins the
> declared set — DT06 closed). Q-0064 rows landed: `btd6.version_announce_channel`
> binding (binding-first read, KV fallback, shadow warning on the typed command)
> + the CT-group guided flow (parse → preview → confirm,
> `views/btd6/ct_group_flow.py`). Q-0073-B verified already satisfied (economy
> log channel projects via its declared scalar + binding). **Open Phase 2 tail:**
> per-subsystem pointer-migration classification (proof/logging rows) — ride a
> later slice; the dual-write seam stays untouched (Phase 3).

- **Objective:** real per-domain panel registrations replace the curated
  `DOMAIN_CONFIG_SUBSYSTEMS` frozenset (`customization_catalogue.py:239`), with an
  exhaustive coverage invariant so a missing domain reddens CI; the decided BTD6
  rows land with it (Q-0064: announcement channel → first-class **binding** with
  native selector; CT group → **guided advanced flow**).
- **Source route:** settings audit §11 Phase 2 (+ its §4/§5 taxonomy); #640's
  `actionable_settings_groups()` is the consumer.
- **Files:** `disbot/services/customization_catalogue.py`, per-subsystem schema/
  registration modules, `disbot/views/settings/hub.py` (only if discovery shape
  changes), `tests/unit/cogs/test_settings_cog.py` + navigation/docs pins + the new
  declaration-coverage invariant.
- **Tests first:** define the registration-completeness contract before swapping
  the seam. Live smoke: >25 pagination + group navigation still reachable.
- **Risk/rollback:** medium; discovery-only (no mutation-service absorption —
  Phase 3 territory, Q-0063 converge-gradually). Revert = restore frozenset.
- **Stop:** anything that touches the dual-write seam (`settings_mutation.py:335`)
  — that is Phase 3, sequenced after this.
- **Then:** Phase 3 convergence (Q-0063) → Phase 4 structured editors/presets
  (Q-0070) → Phase 5 Setup/Settings convergence (own planning session first).

### Batch 5 — Adaptive P1C: Access Map + Help Preview staff-hub subpanels (ADP-2) — executed in **#656** (2026-06-10, verify merged)

> Outcome notes: both subpanels shipped in `views/server_management/access_map.py`
> as the first `project_access_map` consumers (Q-0032: hub buttons only, no new
> command names; Q-0045 declared-tier simulation with the §16.4 limit label;
> authority re-checked per interaction; display-only pinned by a
> mutation-import test). Live-smoked (clean boot, hub registers).
> The Help projection seam (Batch 6) can now build on this lane as planned.

- **Objective:** the read-only operator surface over `services/access_projection`
  (#589) + the #632 tier-input path: staff-hub **subpanels, no new command names**
  (Q-0032), Server-Management hub link.
- **Source route:** adaptive plan **§16.8** (read before starting) + §9 P1C row.
- **Files:** `disbot/views/server_management/` subpanels (or `views/access/`),
  thin cog hooks, `tests/unit/services/test_access_projection.py` extensions +
  new view/authority tests.
- **Tests:** staff-only authority re-checked at callback time; redaction (no
  sensitive policy internals below admin); **display-only** — zero writes; Help
  preview labeled as simulation (§16.4).
- **Why before Help seam:** Help-consumes-projection belongs to this lane — the
  standard (§2.4) explicitly forbids a parallel Help lock/preview detector.
- **Risk/rollback:** medium (UI only); rollback = unregister panels.
- **Stop:** any mutation affordance; any denial-copy *wiring* (ADP-3 stays gated on
  the owner's markup of the #632 table).

### Batch 6 — Help projection seam (HLP-2/DT05/B01), then overlay (HLP-3) — seam **merged #657**; overlay executed in **#659** (2026-06-10, verify merged)

> **HLP-3 outcome notes (#659, same session — the #657 merge cleared its
> gate):** migration 064 `help_overlay` + sole-writer DB module + the
> audited `help_overlay_mutation` seam (admin gate · write-time
> catalogue-key validation · partial-edit merge · per-field/full reset ·
> cache invalidation · `audit.action_recorded`) + the cached fault-tolerant
> read model, flowing through the HLP-2 projection into all five render
> paths (hide parity with governance hides; renames as presentations with
> defaults riding along, Q-0058; orphans reported, never rendered;
> no-rows = byte-identical, pinned). Q-0055 display-only = an import fence
> on admission paths. The `help_cog` 800-LOC ceiling forced the sanctioned
> decomposition (`cogs/help/panels.py`). **Open Help-lane tail:** the
> overlay **editor UI** (audit Phase 5, incl. the Q-0059 embed-builder Home
> message — preview mandatory) and Phase 4 command/panel-action records
> (Q-0057 rider).

> Outcome notes: `services/help_catalogue.py` (stable-keyed inventory; four
> drift-finding kinds pinned empty) + `services/help_projection.py` (the
> audit-§9 reason-coded `HelpProjection`; only `display_hidden`/
> `governance_hidden` hide — lock states stay advertised, HLP-4) shipped,
> and **all five render paths consume the one projection**: Home gained
> host-subsystem governance awareness, typed/dropdown routes now check
> their target (hidden ⇒ the same not-found as nonexistent), the
> single-command route applies the shared display filter, and the
> Advanced dropdown re-checks at click time. **Q-0074 executed in the same
> PR** (admin `visibility_tier` owner → administrator; placement ==
> admission pinned via the catalogue `tier_mismatch` finding). Net
> extended to 29 tests + 26 new contract tests; dead `build_overview_embed`
> deleted. **HLP-3 (the overlay) remains the open tail of this batch** —
> all decisions answered; activation gated on #657 merged + smoke-tested.
> Details: PR #657 + `.sessions/2026-06-10-batch6-help-projection-seam.md`.

- **Objective:** one effective-access projection consumed by **all five** Help
  render paths (today: five filter sets; the #642 characterization net pins the
  divergence).
- **Source route:** help audit **§9 + §11 internal order** (projection contract →
  catalogue → read model → renderers), on the #642 net.
- **Files:** new `HelpCatalogue`/`HelpProjectionService` (services layer; composes
  governance + command-access + routing + `access_projection`), Help cog/renderers,
  `tests/unit/cogs/test_help_render_paths.py` extended with projection-result
  fixtures **before** renderers change.
- **Tests-first requirement:** add effective-access assertions per path
  (home/advanced/typed/subsystem/dedicated) so unification is observable.
- **Then HLP-3:** the guild Help overlay/editor — all five decisions answered
  (Q-0055–Q-0059, incl. Q-0059 = embed builder); activate only after the seam
  lands. Hiding stays display-only; never execution denial (HLP-4).
- **Risk/rollback:** medium; behavior changes are the *point* — characterize first.
- **Stop:** overlay mutation work before the seam is merged + smoke-tested.

### Batch 7 — Mutation-path hardening (RS01 → RS02) — decisions answered 2026-06-10

**Q-0071 answered: A** — the **domain workflow service owns ONE DB transaction**
(coins + inventory commit or roll back together; rule now in `docs/ownership.md`
§ "Cross-domain transactions"). **Q-0072 answered: C** — mining's first slice is
the **workshop-workflow service boundary**. The batch is decision-cleared; it runs
in plan order (after the smaller batches), not immediately.

> **Execution record (2026-06-10, mining-finalization session):** **RS01 executed
> in PR #661** (`services/shop_purchase_workflow.py` + conn-aware primitives +
> `db.transaction()` + the view-write invariant; live-verified incl. the
> concurrent double-click). **RS02 stage 1 executed in the follow-up PR**
> (characterize → relocate the pure domain to `utils/mining/` → conn-aware
> mining primitives → `services/mining_workflow.py` owning the workshop ops,
> one transaction each; the three views→cogs allowlist entries deleted).
> **RS02 stage 2 executed in the next PR of the same session**: market
> sell/sell-all/buy (both legs atomic), the action writers mine/harvest/
> explore (loot + wear in one transaction), use/equip/unequip, descent, and
> admin writes all converged; `cogs/mining/` deleted; the AST write-boundary
> ratchet landed (`test_mining_write_boundary.py`); recipes.json reconciled to
> the item catalog under the new alignment lint. **RS01 + RS02 = Batch 7
> COMPLETE** — the maintainer-commissioned mining/tool/gear finalization plan
> pulled this batch forward of the remaining smaller batches.

- **Objective:** close the two-commit purchase hole first (smallest high-value
  slice), then converge mining writes behind workflow services.
- **RS01 slice:** purchase **workflow service owning one transaction** (Q-0071=A;
  DB primitives gain transaction-awareness as in-scope plumbing); both
  `shop_panel.py` callbacks consume it; invariant prevents view-level purchase
  writes; concurrency + failure-injection tests. Files:
  `disbot/services/economy_service.py` or a new bounded purchase module,
  `disbot/views/economy/shop_panel.py`, `disbot/utils/db/inventory.py`,
  `docs/ownership.md`.
- **RS02 program (staged, separate PRs):** characterize → extract the **workshop**
  workflow first (Q-0072=C — densest multi-write invariant) → ratchet direct
  writes down per area (market/exploration follow), command/panel parity tests
  throughout. Structures (§7.5) and game-XP (§7.4) land after, on the safer base.
- **Risk/rollback:** high (balances/items); migration-aware tests mandatory;
  never bundle mining into the RS01 PR.
- **Stop:** any schema change beyond transaction plumbing; any leg committed
  separately from a cog/view.

### Batch 8 — BTD6 `--all` towers cutover — dedicated session (decisions already routed)

- **Objective:** execute the routed cutover: game-native committed stats,
  Farm/Village full tier structures (attack-suppressed), per-tier beast names,
  name-guard joins, ~25 value-pinned test updates, legacy-fallback disposition.
- **Source route:** `docs/btd6/btd6-gamedata-decode-status.md` (the ordered
  backlog) + router §29 (Q-0066–Q-0069 — answered).
- **Boundary:** its own session; not combined with AI expansion. A06/A07/A08
  discoverability copy rides only if still accurate at cutover.
- **Owed operational step (anytime):** the **first real dispatch** of the #633
  refresh workflow from the Actions tab (maintainer-driven).

### Batch 9 — Observability & lifecycle hardening (RS05 · RS08 · RS10) — contract-first

- **RS08 (ready):** extract the diagnostic embed builders' raw SQL
  (`cogs/diagnostic/_platform_embeds.py`, `_helpers.py`) into bounded read-only
  service read models; embeds become render-only; keep the diagnostics read-only
  invariant.
- **RS10 (bounded):** migrate one view family at a time onto
  `views/base.py` ownership/timeout handling (characterize denial copy + timeout
  edit failure first; preserve genuinely multiplayer views).
- **RS05 (contract-first):** decide publish-accepted vs delivered semantics
  (Q-RS03 options in the map; the implementer proposes with the change — metrics
  may land first, renames need cross-service churn budget).
- **Risk:** medium for event API; low for read-model extraction.

### Batch 10 — Next-slice selection/planning (DT09 · DT10 · DT15) — planning-only

- Re-verify `setup-platform/setup_wizard_finalization_plan.md` against shipped
  source and publish **one bounded finalization slice** with acceptance tests
  (DT09); select the next AI typed answer-with-evidence slice from the
  orchestration plan §7 (gated per-exposure — DT10); characterize a game
  terminal-state pin only when a game slice activates (DT15).

## §6 Carried-from-§5 reconciliation (06-09 plan → here)

Every queued ID from the superseded plan, so nothing silently vanishes:

| Old ID | Where now | Gate / note |
|---|---|---|
| SET-1 (Lane 7) | **shipped #640** | — |
| SET-2 Phase 2 | **Batch 4** | Q-0064 rows ride along |
| SET-3 Phase 3 | after Batch 4 | Q-0063 (answered: converge gradually) |
| SET-4 Phase 4 editors/presets | after Phase 3 | Q-0070 (answered: presets everywhere) |
| SET-5 Phase 5 convergence | later | own planning session first |
| SET-6 dual-write seam | constraint, unchanged | canary: "projection failed" diagnostics |
| HLP-1 (Lane 8) | **shipped #642** | — |
| HLP-2 projection seam | **merged #657** (2026-06-10) | — |
| HLP-3 overlay store + seam | **executed #659** (2026-06-10, verify merged) | editor UI (audit Phase 5) + Phase 4 records remain the Help-lane tail |
| ADP-1 (Lane 2) | **shipped #632** | — |
| ADP-2 P1C | **Batch 5** | Q-0032 |
| ADP-3 denial-copy wiring | **gated** | owner's markup of the #632 table (Q-0036) |
| AI-1/AI-2 (Lanes 3/4) | **shipped #634/#639** | model loop awaits maintainer prod check |
| AI-4 §12.1 audit trace + §7 families | later (Batch 10 selects) | per-exposure gates (Q-0048) |
| Answerability Phases 4/5 | **gated** | settings-UI ask · dashboard schema acceptance |
| BTD-1 (Lane 5) | **shipped #633** | first real dispatch still owed |
| BTD-2 pointers | **Batch 4** | Q-0064 (answered) |
| BTD-3 cutover | **Batch 8** | dedicated session |
| GME-1 mining frontier | **Q-0072** → Batch 7-adjacent | structures · game-XP · workshop-boundary |
| GME-2 duels wear | queued (games lane) | Q-0054 (answered) — small slice when games activates |
| GME-3 pets | later | keystones + balance review + promotion |
| GME-4 ease quick-wins | later | light-session candidates |
| SRV-1 PR13 AI layer | **gated** | AI per-exposure; SRV-2 (PR14) **shipped #584** |
| DOC-2 freshness gate | **shipped** (in `check_docs.py`) | — |
| HLT-1 | shipped with #632 | — |
| HLT-2 production live-tests | **owed** (maintainer-only) | no sandbox AI key |

## §7 Blocked / gated scope (unchanged by this plan)

- **AI expansion** — Q-0048 posture: read-only + deterministic + tiered ⇒ standing
  lift; **writes / cost / external calls / new UI ⇒ per-exposure ask**; broad
  expansion gated on stability + provider/provenance + caching/source-health +
  config correctness. Both AI model loops (#634/#639) await the **maintainer's
  production check** (no sandbox provider key).
- **Governance setup section** — deferred (Q-0008/Q-0011); a new scope decision
  reopens it, nothing else.
- **Help overlay (HLP-3)** — gate cleared and **executed 2026-06-10 (#659**,
  after #657 merged + smoked**)**; the remaining gated Help piece is the
  overlay **editor UI** (audit Phase 5 — its slice carries the Q-0059
  embed-builder Home message, whose answer makes preview mandatory).
- **Production-only health verification (HLT-2)** — maintainer live-tests; sandbox
  results must not be reported as live verification (DT14).
- **Owner decisions — all four ANSWERED (structured choices, 2026-06-10; router
  §31):** **Q-0071 = A** (domain workflow service owns one transaction — rule in
  `docs/ownership.md`) · **Q-0072 = C** (workshop-workflow boundary first) ·
  **Q-0073 = B** (`setlogchannel` projected into Settings, no move — rides
  Batch 4/Phase 2-3) · **Q-0074 = A** (Admin placement administrator-visible
  after a source inventory; owner-only checks stay on dangerous actions — Batch 2
  classifies Admin rows accordingly). Held-at-default, nothing blocked:
  Q-A02 · Q-A03 (Batch 2 implements its default) · Q-B02/Q-DT03.

## §8 Next recommended agent

**Sonnet implementation session(s), starting with Batch 1 + Batch 2** (small,
source-verified, test-covered; parallel-safe as two sessions per
`ai-project-workflow.md` §9). No further mapping is needed — the campaign is
complete and verified, and **all four §31 decisions are answered**. **Opus/Fable
planning** is warranted only for Batch 7's transaction design (Q-0071=A decided
the shape; the staged design still deserves a planning pass) and Batch 10's
selections. Codex fits bounded verification prep (e.g. Batch 2's generated
inventory) if used.
