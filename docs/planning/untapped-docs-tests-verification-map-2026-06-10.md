# Untapped Docs / Tests / Verification Map — 2026-06-10

> **Status:** `audit`
>
> **Merged as #647 (2026-06-10) and reconciled the same day.** §2's "zero open PRs"
> is a mapping-time fact — the open set at mapping time was this PR and its sibling
> **#646** themselves. The drift findings were verified (FIND-DT01 split verdict:
> the tracker's *header* was stale, its *body* already recorded PR14 shipped) and
> the queue-truth fixes landed 2026-06-10; per-finding dispositions, the Batch→phase
> mapping, and the Q-DT01–Q-DT04 routing live in
> [`consolidated-implementation-plan-2026-06-10.md`](consolidated-implementation-plan-2026-06-10.md).

**Mapped at:** `ed6269767c5614894fb3cdce2985d6487dc981b4`  
**Scope:** Documentation, tests, plans, verification debt, and implementation-readiness after platform mapping.  
**Source precedence:** source + merged PRs > binding docs > current-state > plans > old notes.

## 1. Executive summary

### Top findings by severity

1. **Critical blocker — no critical runtime blocker was found, but queue truth is split.** The server-management status tracker/current-state/roadmap still queue PR14 even though merged PR #584 shipped the unified hub. A future session following the advertised authority can redo shipped work or sequence governance incorrectly (FIND-DT01).
2. **Important — the just-merged mapping reports contain intentionally historical live-PR claims.** FIND-B02 and FIND-B08 say #640/#642 are live owners, while both are merged at this mapped HEAD; the reports also hand consolidation to a future merge session without assigning a durable queue home (FIND-DT02, FIND-DT03).
3. **Important — mapping found a classification-quality problem but no completeness invariant pins it.** Existing ledger tests pin accepted values and Help filtering, not that panel actions/hidden shortcuts are explicitly classified. FIND-A01/A05 and FIND-B04/B07 can recur silently (FIND-DT04).
4. **Important — Help characterization exists, but the projection seam does not.** `test_help_render_paths.py` accurately pins today's inconsistent render paths; implementation must preserve that net while adding effective-access assertions before overlay work (FIND-DT05).
5. **Important — active-lane sequencing conflicts remain.** Adaptive is “Later” in the Settings area while P1C is “Now/Next” at the roadmap top; setup-wizard finalization is also “Next” without a bounded next slice. Mining names two alternative next slices without a decision or characterization entry criterion (FIND-DT08, FIND-DT09, FIND-DT13).
6. **Important — the platform consistency ledger labels itself stale and still carries status-shaped rows.** It is useful as a contract inventory, but should not be selected as a queue without source verification (FIND-DT12).

### Biggest stale-doc risks

- PR14 remains queued in the server-management tracker, current-state, and roadmap after #584 merged.
- Mapping A/B preserve now-stale live-PR/baseline statements (#638/#640/#641/#642), which are valid audit history but unsafe as current routing.
- Adaptive P1B wording says “remaining” despite #632 completing its remainder; P1C is routed inconsistently.
- The platform-surface campaign is still “Next” after both reports merged.

### Biggest missing-test risks

- No repository-wide assertion requires explicit, correct command-surface classifications for panel actions, hidden shortcuts, slash legacy routes, or compatibility aliases.
- Help tests characterize current divergent filters but do not yet pin an effective-access projection contract across home, advanced, subsystem, and single-command paths.
- Settings Phase 2 has no declaration-coverage invariant proving every actionable domain panel is registered without the temporary `DOMAIN_CONFIG_SUBSYSTEMS` seam.
- Governance/access/routing display-vs-execution separation is service-tested, but P1C needs authority/redaction/live-view characterization before UI implementation.
- No integration directory exists; production-only diagnostics behavior remains an explicit live-test debt.

### Highest-value implementation-ready batches

1. **Queue-truth reconciliation (Codex):** correct stale routing in the authoritative tracker/current-state/roadmap and annotate historical mapping claims without changing audit evidence.
2. **Surface-classification invariant (Sonnet):** create a generated inventory assertion, then classify the bounded FIND-A01/A05/B04/B07 set in reviewable slices.
3. **Help projection seam characterization-first (Sonnet):** add failing/characterizing access-projection cases, then unify the four render paths before overlay work.
4. **Settings declaration coverage (Sonnet):** replace the temporary group seam with registrations and pin exhaustive actionable-group coverage.

### Work that must remain gated/deferred

- Governance setup section (Q-0008/Q-0011), AI-generated role templates, broad AI/BTD6 feature expansion, Help overlay mutation/customization, and AI template-advisor ideas remain gated.
- Health production AI selection and live Discord recurring-finding rendering remain maintainer-only live verification.
- BTD6 `--all` cutover is implementation-ready only as its dedicated, decision-routed session; do not combine it with broad AI expansion.

## 2. Live repo state checked

| Check | Result |
|---|---|
| Current HEAD | `ed6269767c5614894fb3cdce2985d6487dc981b4` (`work`) |
| Open PRs checked | GitHub REST API returned **zero open PRs** on 2026-06-10 UTC. `gh` was unavailable. |
| Recent merged PRs checked | #645, #644, #643, #638, #642, #640, #641, #639 and earlier burst PRs were confirmed merged through GitHub REST and local merge history. |
| Docs/plans read | Required workflow/orientation docs; current-state/roadmap; mapping standard and A/B reports; Settings/Help audits and maps; owner router; all subsystem folios; named server-management/setup/adaptive/AI/BTD6/health plans; active decode/cutover docs. |
| Tests/scripts inventoried | 649 `tests/unit/test_*.py` files; 39 invariant files; no `tests/integration/` test files; architecture/doc/quality scripts and relevant area tests. |
| Limitations | No `gh` executable; PR descriptions were not exhaustively downloaded. No AI provider key or production Discord environment, so owed health live tests were not attempted. |

Current-state claims already stale at HEAD: its header still describes #638 as an open draft and the mapping standard as PR #641; its next-candidate server-management route still says PR14 is next. Roadmap routing is mostly accurate for Settings, Help, AI, BTD6, and mining, but platform mapping and PR14 have shipped, Adaptive appears in conflicting horizons, and setup-wizard finalization lacks a bounded next-session handoff.

## 3. Recent mapping reports consumed

- **Agent A** mapped the user-facing typed/panel surface and identified ownership, classification, alias, and BTD6 split-root discoverability findings. This report consumes FIND-A01–A09 without repeating its command/panel tables.
- **Agent B** mapped admin/platform surfaces and identified Help projection divergence, Settings reachability, Admin placement, classification, governance, channel naming, slash legacy, and baseline-delta findings. This report consumes FIND-B01–B10 without repeating its inventories.
- Consolidation is required where findings need an owner, a characterization test, a durable plan entry, or a gate. Most future opportunities remain deferred; the highest-value shared seam is explicit command-surface classification plus Help projection.
- This report deliberately does **not** redo command counts, panel inventories, service/helper ownership mapping, or implementation ownership seams assigned to parallel Codex Agent 1.

## 4. FIND-A / FIND-B consolidation table

| finding | source report | severity | summary | current owner/gate | needs test? | needs doc update? | needs owner question? | implementation batch candidate | verification notes |
|---|---|---:|---|---|---|---|---|---|---|
| FIND-A01 | Agent A | 2 | Mining hidden typed commands lack ledger `panel_action` classifications | command-surface ledger + mining | yes | yes | no | Surface-classification invariant | Explicit completeness pin absent |
| FIND-A02 | Agent A | 2 | Economy owns binding-shaped `setlogchannel` | Settings/bindings ownership decision | yes | yes | **yes** | Ownership-routing decision, then move | Cross-agent ownership seam; do not move in mapping |
| FIND-A03 | Agent A | 2 | Counting owns mutable/persisted match state locally | games folio/architecture | characterization | yes | possibly | Counting ownership extraction | Agent 1 likely maps implementation seam; avoid duplicate edit |
| FIND-A04 | Agent A | 3 | Leaderboard has nine compatibility aliases | games/Help discoverability | yes | optional | no | Alias cleanup | Preserve compatibility before hiding/removing |
| FIND-A05 | Agent A | 3 | Utility hidden compatibility commands lack ledger classifications | ledger + utility | yes | yes | no | Surface-classification invariant | Same root gap as A01/B04/B07 |
| FIND-A06 | Agent A | 2 | BTD6 panel advertises paths split across root groups | BTD6 folio/Help | yes | yes | no | BTD6 discoverability copy | Verify commands before changing copy |
| FIND-A07 | Agent A | 3 | Split BTD6 cogs rely on aggregate Help hook/routes | BTD6 + Help | characterization | yes | no | BTD6 discoverability copy | May be intentional aggregation; no independent hook required without UX decision |
| FIND-A08 | Agent A | 4 | Explain split roots in BTD6 panel | BTD6 future UX | yes | no | no | Bundle with A06 | Future opportunity only |
| FIND-A09 | Agent A | 4 | Add canonical-alias legend in Leaderboard panel | games future UX | yes | no | no | Bundle with A04 | Future opportunity only |
| FIND-B01 | Agent B | 2 | Help render paths use materially different filters/no effective projection | Help audit + Adaptive P1A | **yes** | yes | no | Help projection seam | #642 adds characterization, not the seam |
| FIND-B02 | Agent B | 2 | Settings reachability gap owned by live #640 | Settings audit | no | **yes** | no | Queue-truth reconciliation | #640 is merged; finding is resolved/stale-as-current |
| FIND-B03 | Agent B | 2 | Admin metadata tier conflicts with administrator-admitted routes | Admin/registry owner | yes | yes | **yes** | Admin placement decision | Must choose metadata or route posture first |
| FIND-B04 | Agent B | 2 | Panel actions/hidden shortcuts default to `primary_entrypoint` | command-surface ledger | **yes** | yes | no | Surface-classification invariant | Root consolidation finding |
| FIND-B05 | Agent B | 2 | Governance has no setup section | Q-0008/Q-0011; deferred | later | yes | no duplicate | **blocked** governance setup | Do not promote |
| FIND-B06 | Agent B | 2 | Channel commands have generic top-level names | channel UX/compatibility | yes | yes | **yes** | Namespace migration plan | Compatibility/deprecation posture unresolved |
| FIND-B07 | Agent B | 3 | `/setup-hub` legacy route lacks slash classification wiring | setup + ledger | **yes** | yes | no | Surface-classification invariant | Requires slash-side classification contract |
| FIND-B08 | Agent B | 3 | Help counts/characterization owned by live #642 | Help audit | no | **yes** | no | Queue-truth reconciliation | #642 merged; resolved/stale-as-current |
| FIND-B09 | Agent B | 3 | AI internals changed after standard baseline | AI roadmap | yes where contracts change | yes | no | Mapping baseline annotation | Standard/report are historical; reverify before implementation |
| FIND-B10 | Agent B | 4 | Generate visible-but-unavailable explanation | Adaptive/Help future UX | later | yes | no | after Help projection seam | Keep deferred until projection/overlay settles |

## 5. Active plan and roadmap consistency map

| area | current-state claim | roadmap route | authoritative plan/tracker | source/PR verification | status | drift finding refs |
|---|---|---|---|---|---|---|
| Settings Phase 2 / 3 | #640 Phases 0+1 shipped; Phase 2 next | Phase 2 then Phase 3 | Settings centralization audit | #640 merged; temporary `DOMAIN_CONFIG_SUBSYSTEMS` remains | correctly routed; needs coverage invariant | DT06 |
| Help projection seam / overlay | #642 characterization shipped; overlay later | projection seam then Q-0055–59 overlay | Help customization audit | #642 merged; render-path tests exist; projection not consumed | correctly ordered, test-first requirement implicit | DT05 |
| Adaptive Setup/Access P1C | P1A/P1B shipped; P1C next | top table Now/Next, Settings section Later | Adaptive plan | #632 merged P1B remainder; P1C absent | route conflict | DT08 |
| Server Management PR13/PR14 / governance | PR13 AI then PR14; governance deferred | same | status tracker | #584 already shipped PR14 hub; AI layer absent; governance deferred | materially stale | DT01 |
| AI orchestration continuation | P4 MVP shipped; continue accepted foundation | AI roadmap authority | orchestration plan + AI roadmap | #634 merged; typed plan→execute→verify tests exist | coherent; next slice must be explicitly selected | DT10 |
| AI answerability Phase 4/5 | P3 shipped; P4 settings UI/P5 generated answers next | next behind per-exposure gates | answerability roadmap | #639 merged; broad UI/generated-answer work remains gated | correctly gated | DT10 |
| BTD6 extraction/cutover | extraction resumed; dedicated `--all` cutover next/later | cutover Later | decode-status + BTD6 folio | #638 merged ABR/income/decode tail; decisions Q-0066–69 routed | coherent but dedicated-session boundary required | DT11 |
| Mining structures / game-XP | either is next | same ambiguous pair | mining character plans/roadmap | #624 shipped workshop/durability/overview; no selection recorded | unclear next-session boundary | DT13 |
| Health/diagnostics live-test debt | production live tests owed | Now verification owed | health folio + implementation plan | deterministic/DB tests exist; production AI/live Discord unavailable | correctly routed, environment-blocked | DT14 |
| Platform-surface mapping follow-up | reports planned/in flight | campaign Next then merge/implementation session | standard + A/B reports | #641/#643/#644 merged; no open PRs | stale route; implementation queue not consolidated | DT02, DT03 |
| Setup wizard finalization | active next candidate | Next | setup wizard finalization plan | extensive setup tests exist; plan is broad and old | needs bounded handoff/reverification | DT09 |

## 6. Test and characterization gap map

| area | existing tests found / behavior pinned | behavior not pinned | likely future test file | block implementation until characterization? | refs |
|---|---|---|---|---|---|
| Help render paths/projection | `tests/unit/cogs/test_help_render_paths.py`, Help navigation/actionability/classification tests pin current four paths and filters | effective-access result is not uniformly consumed/pinned across every path | extend `test_help_render_paths.py`; add projection integration cases | **yes** for seam/overlay | B01, DT05 |
| Settings discovery/declarations | settings cog/navigation/docs tests pin actionable groups and >25 reachability | exhaustive declaration ownership replacing `DOMAIN_CONFIG_SUBSYSTEMS`; BTD6 declaration/guided flow | `tests/unit/cogs/test_settings_cog.py`, settings navigation/doc pins, new invariant | **yes** for Phase 2 refactor | DT06 |
| Command-surface ledger | ledger/import/legacy/Help classification tests pin vocabulary and filtering | explicit classification completeness/correctness for panel actions, hidden shortcuts, slash legacy, aliases | `tests/unit/runtime/test_command_surface_ledger.py` or new invariant | **yes** before bulk reclassification | A01/A05/B04/B07, DT04 |
| Governance/access/routing display vs execution | access projection/service/governance/routing tests pin read models and execution owners | P1C panel authority, redaction, display-only/no-write behavior, Help preview | `tests/unit/services/test_access_projection.py`, new P1C view tests | **yes** for P1C UI | B01/B03/B10, DT08 |
| Setup wizard finalization | large `test_setup_cog.py`, setup draft/session/operation invariants | a bounded “finalization complete” acceptance contract and live flow | setup cog/view tests + smoke checklist | yes for selected mutation slice | DT09 |
| Server-management panels/mutations | hub service/view tests and mutation invariants are broad | tracker assertions that PR14 is shipped; AI template layer remains gated | status-doc test only if a durable machine-readable sequence is adopted | no for docs reconciliation; yes for gated AI | DT01 |
| AI orchestration answer-with-evidence | orchestration wiring/policy/mutation/DB tests; P4 round-cash vertical slice | a generic typed answer-with-evidence contract across future tools; live provider selection | runtime AI orchestration tests + eval/contract fixture | yes before broad expansion | DT10 |
| BTD6 data/cutover values | parse/inventory/service/cog value pins; decode-status enumerates decisions | `--all` cutover acceptance across committed stats and legacy fallback removal | BTD6 service/parser/inventory tests and smoke checklist | **yes** for cutover | A06, DT11 |
| Mining next slice | workshop/durability/reward/world/market tests | selected structures or game-XP contract, terminal/restart/economy boundaries for that slice | mining service/cog/view tests chosen after scope selection | yes | DT13 |
| Games terminal-state views | game panel tests pin Help panels/rules, not a repository-wide terminal-state regression contract | verify every game terminal state disables/settles views and preserves refund semantics | game-specific view/engine tests; possible shared invariant | yes for game-flow changes | DT15 |
| Diagnostics live behavior | health embed/snapshot/redaction/findings and real-Postgres tests | live model tool selection, non-owner denial, recurring-finding Discord render | production smoke record, not sandbox unit test | no code block; release verification remains owed | DT14 |

## 7. Documentation drift findings

### FIND-DT01 [critical blocker] Server-management authorities still queue the already-shipped PR14 hub.
- **evidence:** `docs/current-state.md:116-117` says PR14 is next; `docs/roadmap.md:56-58` says the unified hub is next; `docs/planning/server-management-status-2026-06-05.md:17-19` says PR14 remains queued; local history/current-state recently-shipped records merged #584.
- **verified-by:** docs grep / local git history / PR check / source-and-test presence (`test_server_management_hub*`).
- **impact:** a future session may rebuild the hub or incorrectly place governance after an unshipped prerequisite.
- **recommended disposition:** fix-docs-now.
- **likely files for later update:** `docs/planning/server-management-status-2026-06-05.md`, `docs/current-state.md`, `docs/roadmap.md`, `docs/subsystems/server-management.md`.
- **implementation note:** Codex should reconcile queue truth only; preserve PR13 AI and governance gates.

### FIND-DT02 [important improvement] Platform mapping is still routed as a future campaign after both reports merged.
- **evidence:** `docs/roadmap.md:86-94` says two agents map then a merge/implementation session; PR #643/#644 are merged and the reports exist.
- **verified-by:** PR check / docs read.
- **impact:** next-session routing can rerun mapping instead of consolidating findings.
- **recommended disposition:** fix-docs-now.
- **likely files for later update:** `docs/roadmap.md`, `docs/current-state.md`, mapping standard.
- **implementation note:** route to bounded consolidation/test batches, not a single broad consistency-fix session.

### FIND-DT03 [cleanup] Mapping reports contain stale live-PR ownership/baseline claims that need historical framing.
- **evidence:** Agent B lines 11, 22, 52 name live #638/#640/#641/#642; Agent A lines 3 and 1198 say #641 was live/absent; all are merged at HEAD.
- **verified-by:** PR check / docs grep.
- **impact:** readers may treat resolved B02/B08 or old baselines as active blockers.
- **recommended disposition:** route-to-existing-plan.
- **likely files for later update:** mapping A/B report preambles/findings, mapping standard.
- **implementation note:** retain audit-time facts; add resolved/current disposition annotations rather than rewriting evidence.

### FIND-DT04 [important improvement] Surface classification findings lack an exhaustive invariant.
- **evidence:** A01/A05/B04/B07 identify defaults/hidden/slash gaps; existing ledger and Help tests validate vocabulary/filtering but allow unannotated fallback to `primary_entrypoint`.
- **verified-by:** test check / source read / report consolidation.
- **impact:** audits remain memory/count driven and classification drift can silently recur.
- **recommended disposition:** needs-test.
- **likely files for later update:** `tests/unit/runtime/test_command_surface_ledger.py` or a new invariant; bounded cog declarations; command-surface docs.
- **implementation note:** generate the inventory from loaded/static declarations and require explicit exceptions; do not pin a prose count alone.

### FIND-DT05 [important improvement] Help characterization pins divergence but not the intended projection contract.
- **evidence:** `tests/unit/cogs/test_help_render_paths.py` explicitly characterizes home/advanced/typed/subsystem paths; FIND-B01 records that they do not consume effective access projection.
- **verified-by:** test check / source read / Help audit.
- **impact:** overlay work can preserve or worsen inconsistent visibility while still passing current tests.
- **recommended disposition:** needs-test.
- **likely files for later update:** Help render-path tests, Help cog/projection adapter, Help audit.
- **implementation note:** add projection-result fixtures and expected visibility/locked-copy behavior before changing renderers.

### FIND-DT06 [important improvement] Settings Phase 2 is routed but its declaration-coverage acceptance test is not specified.
- **evidence:** roadmap lines 75-79 and Settings audit Phase 2 call for replacing `DOMAIN_CONFIG_SUBSYSTEMS`; existing tests pin current actionable groups/reachability.
- **verified-by:** docs read / test check / source grep.
- **impact:** registrations can omit a domain or recreate a curated list without CI detecting it.
- **recommended disposition:** needs-test.
- **likely files for later update:** Settings audit, settings cog/navigation tests, new declaration invariant, settings command map.
- **implementation note:** define an exhaustive registration/coverage contract before replacing the temporary seam.

### FIND-DT07 [important improvement] FIND-A02 and FIND-B03/B06 need owner decisions before implementation.
- **evidence:** mapping reports identify a binding-shaped Economy command, Admin tier/route mismatch, and generic channel roots; router has no dedicated decisions for these exact dispositions.
- **verified-by:** router grep / report consolidation.
- **impact:** implementation could move commands, change access, or break compatibility based on an audit inference.
- **recommended disposition:** needs-owner-decision.
- **likely files for later update:** owner router, relevant folios/plans after answers.
- **implementation note:** route Q-DT01–Q-DT03; safe default is no behavior change.

### FIND-DT08 [important improvement] Adaptive P1C has conflicting roadmap horizons and the plan's P1B status is stale.
- **evidence:** roadmap at-a-glance says P1C next, Settings section labels Adaptive Later; Adaptive plan line 3 says P1B/P1C next while #632 completed P1B remainder.
- **verified-by:** docs read / PR check / test check.
- **impact:** agents may defer an active lane or repeat P1B work.
- **recommended disposition:** fix-docs-now.
- **likely files for later update:** Adaptive plan, roadmap, current-state.
- **implementation note:** reconcile status before a P1C session; retain display-only/read-only boundary.

### FIND-DT09 [important improvement] Setup-wizard finalization is “Next” without a bounded current slice or fresh acceptance boundary.
- **evidence:** roadmap lines 67-69 names the broad plan as active; the plan predates many shipped setup/server-management slices and extensive tests.
- **verified-by:** docs read / test enumeration / PR history.
- **impact:** a session can overreach across mutations, UX, and already-shipped sections.
- **recommended disposition:** route-to-existing-plan.
- **likely files for later update:** setup-wizard finalization plan, settings folio, roadmap.
- **implementation note:** first run a source/test re-verification and publish one bounded finalization slice.

### FIND-DT10 [important improvement] AI “next” work needs a selected contract, not generic continuation.
- **evidence:** roadmap records orchestration P4 and answerability P3 shipped, while answerability Phase 4/5 remain per-exposure gated and the orchestration plan contains multiple later phases.
- **verified-by:** plans / PR #634/#639 / test inventory.
- **impact:** a future session may infer broad AI UI/generated-answer approval.
- **recommended disposition:** blocked-by-gate(per-exposure AI gate).
- **likely files for later update:** AI roadmap and selected phase plan only after activation.
- **implementation note:** Opus/Fable selects one accepted typed answer-with-evidence slice; Sonnet implements only that slice.

### FIND-DT11 [important improvement] BTD6 cutover is ready only as a dedicated decision-routed batch with explicit value pins.
- **evidence:** #638 merged ABR/income/decode-tail work; router Q-0066–Q-0069 and decode-status route `--all` cutover; roadmap keeps it Later.
- **verified-by:** PR check / docs read / parser/inventory test enumeration.
- **impact:** combining cutover with AI expansion or incomplete fallback removal risks data regressions.
- **recommended disposition:** route-to-existing-plan.
- **likely files for later update:** decode status, BTD6 folio, cutover tests/fixtures.
- **implementation note:** use a dedicated Sonnet session; pin representative values and fallback behavior before/through cutover.

### FIND-DT12 [important improvement] Platform consistency ledger is a stale-status-shaped contract inventory, not safe queue truth.
- **evidence:** its header explicitly says “stale status”; rows still contain PR/future status and §8 is an implementation sequence.
- **verified-by:** docs read / docs grep.
- **impact:** agents can select obsolete PR work despite source/current trackers superseding it.
- **recommended disposition:** route-to-existing-plan.
- **likely files for later update:** platform consistency ledger and its folio links.
- **implementation note:** preserve durable contracts; remove/clearly badge queue-shaped stale sections in a docs-only pass.

### FIND-DT13 [important improvement] Mining's next slice is ambiguous between structures and game XP.
- **evidence:** roadmap at-a-glance says “structures or game-XP next”; no selected scope/entry tests are named.
- **verified-by:** roadmap / mining tests / recent PR #624.
- **impact:** two sessions can choose different incompatible next slices or skip prerequisite characterization.
- **recommended disposition:** needs-owner-decision.
- **likely files for later update:** mining active plan/roadmap/current-state after selection.
- **implementation note:** choose one slice and write its state/economy/view characterization before runtime changes.

### FIND-DT14 [important improvement] Health live-test debt is correctly recorded but cannot be closed by sandbox checks.
- **evidence:** health folio says no AI provider key and lists production owner/non-owner plus recurring-finding Discord walks.
- **verified-by:** docs read / test inventory / environment limitation.
- **impact:** deterministic tests can be misreported as live provider/render verification.
- **recommended disposition:** blocked-by-gate(production maintainer live test).
- **likely files for later update:** health folio/current-state only after maintainer evidence.
- **implementation note:** do not add speculative code; record exact live outcomes when performed.

### FIND-DT15 [future opportunity] Games terminal-state view behavior lacks a clear cross-game regression pin.
- **evidence:** game-panel tests focus on Help/actionability; roadmap drafts require cancel/refund and deterministic terminal behavior, but no shared terminal-view invariant was found.
- **verified-by:** test enumeration / docs grep.
- **impact:** future game-flow work can leave stale interactive views or inconsistent settlement UX.
- **recommended disposition:** needs-test.
- **likely files for later update:** game-specific engine/view tests or a bounded shared invariant.
- **implementation note:** characterize only when a selected game slice activates; do not invent a broad abstraction first.

## 8. Missing or weak tests

| behavior/risk | source or doc evidence | current tests found | missing assertion | recommended test type | should implementation wait? | linked refs |
|---|---|---|---|---|---|---|
| Explicit command classifications | A01/A05/B04/B07 | ledger, legacy, Help filter tests | every surfaced/hidden/panel/slash compatibility route has deliberate classification/exception | generated invariant | yes | DT04 |
| Uniform Help access projection | B01 + Help audit | render-path characterization + access projection service tests | same effective result/locked explanation across all render paths | characterization then integration-style unit | yes | DT05 |
| Settings declaration completeness | Settings Phase 2 | settings cog/navigation/docs tests | all actionable registered domains reachable; no curated seam drift | invariant + view test | yes | DT06 |
| P1C display-only authority/redaction | Adaptive plan | access/governance/routing service tests | staff-only, no writes, no sensitive reasons, correct Help preview | service/view tests + live smoke | yes | DT08 |
| Setup finalization acceptance | setup plan | extensive setup cog/draft/operation tests | selected finalization slice end-to-end acceptance and rollback | bounded view/service test + smoke | yes | DT09 |
| AI typed answer-with-evidence | AI plans | orchestration policy/wiring/mutation/DB tests | reusable evidence/result/failure contract for the selected next tool | contract tests + eval fixtures | yes | DT10 |
| BTD6 cutover representative values | decode/cutover docs | parser/inventory/service tests | committed `--all` values, legacy fallback disposition, refresh/cutover parity | fixture/value pins + smoke | yes | DT11 |
| Mining selected-next-slice contract | ambiguous roadmap | workshop/world/reward/market tests | chosen slice state, economy, restart, and view boundaries | characterization/unit/view | yes | DT13 |
| Health production path | health folio | deterministic, DB integration, embed tests | live provider selects owner tool; non-owner denied; recurring render correct | maintainer smoke record | no code; release evidence yes | DT14 |
| Cross-game terminal views | games roadmap | individual engine/view tests; Help panels | terminal state disables interaction and settlement/refund remains idempotent | game-specific regression; shared invariant only if repeated | yes for affected game | DT15 |

## 9. Owner-question routing candidates

### Q-DT01
- **question:** Should `!setlogchannel` move from Economy to the canonical Settings/bindings platform owner, remain as a compatibility alias, or stay Economy-owned?
- **why it matters:** determines mutation ownership, Help placement, migration, and compatibility tests.
- **options A/B/C:** A move + compatibility alias; B keep implementation but project it into Settings; C keep as-is.
- **recommended default:** B until an ownership/migration plan is approved.
- **existing duplicate/related Q:** related to Q-0064 and Settings Phase 2, but not duplicated.
- **blocked work:** FIND-A02 implementation.

### Q-DT02
- **question:** Should Admin metadata become administrator-tier, or should administrator routes become owner-only?
- **why it matters:** display placement and execution admission currently disagree.
- **options A/B/C:** A metadata/admin hub becomes admin-tier; B routes become owner-only; C split owner-only controls from admin tools.
- **recommended default:** C, after source-backed inventory.
- **existing duplicate/related Q:** none found.
- **blocked work:** FIND-B03.

### Q-DT03
- **question:** Should generic channel commands migrate under a grouped namespace?
- **why it matters:** improves clarity but changes compatibility/discoverability.
- **options A/B/C:** A grouped namespace + legacy aliases; B keep roots but improve Help/panel labels; C no change.
- **recommended default:** B until a migration/deprecation plan exists.
- **existing duplicate/related Q:** none found.
- **blocked work:** FIND-B06.

### Q-DT04
- **question:** Which mining slice is next: structures or game XP?
- **why it matters:** both are advertised as next, but need different contracts/tests.
- **options A/B/C:** A structures; B game XP; C pause mining for a characterization/selection plan.
- **recommended default:** C if the owner does not select A/B explicitly.
- **existing duplicate/related Q:** Q-0054 concerns tuning, not this sequencing choice.
- **blocked work:** FIND-DT13 implementation.

## 10. Implementation-readiness batches

### Batch 1 — Queue-truth reconciliation
- **included refs:** FIND-B02, FIND-B08, FIND-DT01–DT03, DT08, DT12.
- **scope:** reconcile shipped/current/queued claims; annotate historical mapping findings; route follow-up batches.
- **out of scope:** runtime/test changes, changing gates, rewriting audit inventories.
- **required files/docs/tests:** server-management tracker, current-state, roadmap, affected plan/folio preambles; doc checks.
- **verification commands:** `python3.10 scripts/check_docs.py --strict`; targeted `rg` for stale PR phrases; full quality/architecture.
- **blocked/gated notes:** none; preserve historical evidence and gates.
- **recommended target agent:** **Codex** for bounded docs verification.

### Batch 2 — Surface-classification characterization and bounded cleanup
- **included refs:** FIND-A01, A05, B04, B07, FIND-DT04.
- **scope:** create exhaustive/exception-driven invariant, then classify one bounded set at a time.
- **out of scope:** command renames/moves, alias removal, broad Help redesign.
- **required files/docs/tests:** command-surface ledger tests/invariant, affected command declarations, surface-map disposition notes.
- **verification commands:** focused ledger/Help tests; `check_quality --full`; strict architecture.
- **blocked/gated notes:** write the characterization/invariant first; slash classification may require a separate seam design.
- **recommended target agent:** **Sonnet** for narrow implementation; **Codex** can prepare the invariant inventory.

### Batch 3 — Help effective-projection seam
- **included refs:** FIND-B01, B10, FIND-DT05.
- **scope:** add effective-access fixtures/assertions across four render paths, then unify projection consumption.
- **out of scope:** guild overlay mutations/customization and unavailable-explanation generation beyond the approved seam.
- **required files/docs/tests:** Help render-path tests, access projection tests/adapter, Help audit status.
- **verification commands:** focused Help/access tests; full quality; strict architecture; live Help smoke.
- **blocked/gated notes:** overlay remains gated until seam lands and Q-0055–59 implementation scope is activated.
- **recommended target agent:** **Sonnet**.

### Batch 4 — Settings Phase 2 declaration coverage
- **included refs:** FIND-DT06, FIND-A02 (decision only), Q-0064.
- **scope:** define/pin registration completeness, replace temporary domain-group seam, add approved BTD6 declaration/guided-flow rows.
- **out of scope:** Economy command move without Q-DT01; Phase 3 convergence; AI UI.
- **required files/docs/tests:** Settings registrations/cog/navigation tests, declaration invariant, command map/audit.
- **verification commands:** focused Settings/docs tests; full quality; strict architecture; live >25/group navigation smoke.
- **blocked/gated notes:** A02 ownership move blocked on Q-DT01; AI exposures remain gated.
- **recommended target agent:** **Sonnet** after **Codex** test-prep if desired.

### Batch 5 — P1C read-only UI characterization and implementation
- **included refs:** FIND-B01, B03, B10, FIND-DT08.
- **scope:** staff-only Access Map + Help Preview panels, authority/redaction/no-write tests, Server Management link.
- **out of scope:** mutation, denial-copy changes, overlay customization, Admin tier change.
- **required files/docs/tests:** P1C views/cogs/tests, access projection tests, Adaptive plan status.
- **verification commands:** focused service/view/authority tests; quality; architecture; live smoke.
- **blocked/gated notes:** reconcile plan status first; B03 requires Q-DT02 if Admin placement changes.
- **recommended target agent:** **Sonnet**.

### Batch 6 — BTD6 dedicated `--all` cutover
- **included refs:** FIND-A06/A07/A08, FIND-DT11.
- **scope:** execute routed cutover, representative value/fallback pins, refresh/smoke verification, discoverability copy if still accurate.
- **out of scope:** broad AI tools, unrelated decode expansion, independent split-cog Help hooks without need.
- **required files/docs/tests:** decode-status named files, fixtures/services/parser/inventory tests, BTD6 smoke docs.
- **verification commands:** focused BTD6 tests/inventory scripts; quality; architecture; smoke checklist.
- **blocked/gated notes:** dedicated session boundary; follow Q-0066–69 exactly.
- **recommended target agent:** **Sonnet**.

### Batch 7 — Next-slice selection/planning
- **included refs:** FIND-DT09, DT10, DT13, DT15; Q-DT04.
- **scope:** choose one bounded setup, AI, or mining next slice and publish acceptance/tests/gates.
- **out of scope:** implementation before selection; broad multi-area burst.
- **required files/docs/tests:** relevant authoritative plan and characterization inventory only.
- **verification commands:** docs/quality/architecture checks plus targeted test enumeration.
- **blocked/gated notes:** AI per-exposure gates and mining owner selection apply.
- **recommended target agent:** **Opus/Fable** for planning/merge strategy; **Codex** for bounded verification.

## 11. Verification log

| command | result |
|---|---|
| `git status --short` | clean before mapping; only the two allowed mapping/session files added afterward |
| `gh pr list ...` | unavailable: `gh: command not found` |
| GitHub REST pull checks via Python `urllib` | passed; zero open PRs; recent merged PRs confirmed |
| `git log --oneline --decorate -25` | passed; confirmed local merge sequence through #645 |
| required-doc `sed`/`rg` reads and `find docs/subsystems ...` | passed; required route and active plans inspected |
| `rg -n '^FIND-A|^FIND-B' ...` and stale-claim searches | passed; all A/B findings and drift claims consolidated |
| `find tests/unit -type f -name 'test_*.py'` | passed; 649 unit test files enumerated |
| `find tests/integration -type f -name 'test_*.py'` | passed with zero files/directory absent |
| `python3.10 scripts/check_docs.py --strict` | could not start under the default pyenv selection (`python3.10: command not found`) |
| `python3.10 scripts/check_quality.py --full` | could not start under the default pyenv selection (`python3.10: command not found`) |
| `python3.10 scripts/check_architecture.py --mode strict` | could not start under the default pyenv selection (`python3.10: command not found`) |
| `PYENV_VERSION=3.10.20 python3.10 scripts/check_docs.py --strict` | badge issue corrected after run; remaining expected orphan failure because the allowed edit scope forbids linking the new audit from a shared read-path doc |
| `PYENV_VERSION=3.10.20 python3.10 scripts/check_quality.py --full` | formatting/lint/mypy passed; failed on the same doc-orphan gate and pytest collection because environment lacks `discord`/`asyncpg` dependencies |
| `PYENV_VERSION=3.10.20 python3.10 scripts/check_architecture.py --mode strict` | environment-limited: missing `yaml` dependency |

---

**Parallel-lane boundary:** Parallel Codex Agent 1 is mapping runtime/services/workflows; this report maps docs/tests/plans/verification readiness only and does not supersede or rewrite that lane's output.
