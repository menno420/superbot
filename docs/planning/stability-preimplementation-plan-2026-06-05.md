# Stability Preimplementation Plan — First Preparation Pass

**Date:** 2026-06-05
**Base reviewed:** `8d47035` (`work`, equivalent to the repository state immediately after merge PR #528)
**Purpose:** repo-grounded audit and first-draft implementation sequence for Claude Opus refinement. This document proposes no implementation and intentionally does not restart BTD6 extraction or expand AI features.

## 1. Executive summary

### Verdict

The repository has a strong automated baseline and the major server-management foundation work through PR7 has shipped. It is **not yet ready for broad new feature expansion** because the live cog audit is mostly incomplete, several ownership/documentation claims are now demonstrably stale, and at least one shipped lifecycle boundary is bypassed by a user-facing view.

- **Do not re-plan:** the audit-remediation wave through #519, server-management PR1–PR7 (#521–#527), or #528's discord.py 2.7 crash and DiagnosticCog fixes.
- **Do fix before expansion:** dependency pinning; the channel delete-panel lifecycle bypass; cleanup ownership/configuration depth; hard-broken-panel discovery through a completed live audit; AI preset/doc correctness; setup recovery/provenance verification; and BTD6 provenance/provider-parity verification.
- **BTD6 data mapping remains deferred.** ADR-006 explicitly pauses extraction until the provenance contract/schema follow-on lands. No `DataProvenance`/`SourceAttribution` implementation exists in source yet, and live file/cloud/Postgres parity has not been demonstrated in this pass.
- **AI feature expansion remains deferred.** The central stage, snapshot, mutation chokepoints, audit guards, and grounding guards are well tested and should be preserved. The operator interface is incomplete at guild scope, and the binding AI ownership doc currently describes guild-preset behavior that source does not implement.
- **Server management remains the near-term product focus.** Cleanup PR8/PR9 is the next deep management track, but a short runtime/boundary stabilization pass should precede it.

### Biggest blockers

1. **P1 confirmed — channel delete panel bypasses `ChannelLifecycleService`.** `views/channels/delete_panel.py::_DeleteConfirmView.confirm_btn` calls `channel.delete()` directly, while binding ownership says channel delete is lifecycle-owned. The invariant checks only `ChannelCog`, so it misses this view path.
2. **P1 confirmed — cleanup is split and too shallow.** Governance owns `cleanup_policies`; `Cleanup` directly owns prohibited-word DB writes and process-local caches; the panel exposes a static startup whitelist; no unified versioned/auditable cleanup policy builder or dry-run exists.
3. **P1 confirmed — verification baseline is not yet complete.** The live tracker still leaves almost every cog `❓`; #528 fixed RoleCog/DiagnosticCog issues but the master table still shows DiagnosticCog as broken and therefore is stale.
4. **P1 confirmed — AI binding doc/source disagreement.** `docs/ai-config-ownership.md` promises preset application at channel/category/guild scope and describes a guild button, but `ai_behavior_profile_service` and its UI support only channel/category.
5. **P1 confirmed — BTD6 provenance gate remains open.** ADR-006 is accepted but explicitly pauses extraction until a follow-on contract/schema PR. Provider unit tests exist, but no cross-backend parity proof or live backend result was established here.
6. **P2 confirmed — dependency/runtime risk.** `requirements.txt` still allows any `discord.py>=2.3.0`, despite #528 proving that upstream internal-name churn can crash panels.

## 2. Verification baseline

### Repository and PR state

- Working tree was clean at session start: `git status --short --branch` returned only `## work`.
- Reviewed commit: `8d47035`, merge PR #528.
- Recent history confirms #520–#528 are present. Specifically: #520 roadmap, #521 moderation convergence, #522 selectors/role feasibility, #523 lifecycle/channel routing, #524 reconciliation, #525 role lifecycle, #526 role-ID selectors, #527 move/reorder, and #528 live-audit/crash/diagnostic fixes.
- `gh pr list --state open` could not run because `gh` is not installed. Open PR state is therefore **unverified** and must be checked before implementation.
- The checkout branch is named `work`, not `main`, but its HEAD is the #528 merge commit. Before implementation, confirm this commit is current remote `main` and that no overlapping PR is open.

### Commands run

| Command | Result |
|---|---|
| `git status --short --branch` | Clean checkout (`## work`). |
| `git log --oneline --decorate -20` and extended history | Confirmed #520–#528 merges and earlier #513–#519 stability wave. |
| `gh pr list --state open` | Not run successfully: `gh` missing. |
| `PYENV_VERSION=3.10.20 python3.10 scripts/check_architecture.py --mode strict` | **Pass:** 0 errors, 87 tracked warnings (17 BaseView, 53 layer-boundary, 17 raw-SQL). |
| `PYENV_VERSION=3.10.20 python3.10 scripts/check_quality.py --full` (first attempt) | Formatting/lint/mypy passed; pytest collection failed because the Python 3.10 environment lacked runtime dependencies. This was an environment setup failure, not a source regression. |
| `PYENV_VERSION=3.10.20 python3.10 -m pip install -r requirements.txt -r requirements-dev.txt` | Pass; installed the CI interpreter dependencies, resolving the collection blocker. |
| `PYENV_VERSION=3.10.20 python3.10 -m pytest tests/unit/views tests/unit/services tests/unit/governance tests/unit/runtime tests/unit/invariants tests/unit/docs tests/unit/cogs` | **Pass:** 5,831 passed, 3 skipped, 21 warnings in 74.33s; includes high-risk AI, BTD6, lifecycle, setup, governance, views, and cogs. Warnings include un-awaited coroutine/resource warnings worth cleaning up. |
| `PYENV_VERSION=3.10.20 python3.10 scripts/check_quality.py --full` (final) | **Pass:** black, isort, ruff, mypy, and 7,461 pytest cases passed; 3 skipped, 20 warnings, 74.36s pytest time. Required again before every implementation PR. |

### Live bot verification

The bot was **not booted**. Although `.session-journal.md` documents a working test-bot/local-Postgres runbook, this container instance has neither the documented token/`DATABASE_URL` environment variables nor the `postgres` user/Postgres binaries. Therefore live command/panel behavior remains unverified in this pass. This is material for the many `❓` cog statuses and must be resolved before a “stable enough” declaration.

### Baseline conclusion

Automated architecture and broad targeted tests are the strongest available evidence. They do **not** replace the unfinished live panel/command audit. Environment-gated AI, YouTube, Paragon, scheduler, and webhook behavior must be classified as degraded/unverified—not broken.

## 3. Source-of-truth map

### Read first in the Opus session

1. Source files for the area being planned.
2. `.claude/CLAUDE.md` and `.session-journal.md`.
3. `docs/AGENT_ORIENTATION.md`.
4. This report.
5. `docs/architecture.md`, `docs/ownership.md`, `docs/runtime_contracts.md`, `docs/helper-policy.md`.
6. `docs/planning/server-management-status-2026-06-05.md` for shipped PR1–PR7.
7. `docs/ai-config-ownership.md` and ADR-006, with the contradictions below in mind.

### Classification

| Classification | Documents | Finding |
|---|---|---|
| **Binding** | `.claude/CLAUDE.md`; `docs/AGENT_ORIENTATION.md`; `docs/architecture.md`; `docs/ownership.md`; `docs/runtime_contracts.md`; `docs/helper-policy.md`; accepted ADRs | Continue to use. Source wins on conflict. `.session-journal.md` is strong workflow guidance but lower precedence. |
| **Current living ledger** | `.session-journal.md`; `docs/planning/server-management-status-2026-06-05.md`; `docs/planning/cog-functionality-audit-2026-06-05.md`; `docs/btd6-gamedata-decode-status.md` | Useful, but the cog tracker and journal need reconciliation after #528; server-management status correctly records PR1–PR7 and remaining PR8+. |
| **Current plan / target architecture** | `server-management-implementation-plan`; `server-management-roadmap`; `settings-customization-roadmap`; `operator-settings-presets`; `resource-provisioning-overview`; AI readiness/provider plans | Use for target intent only. Re-plan the next 2–3 PRs against source; do not execute old sequence blindly. |
| **Historical / superseded** | raw 2026-06-05 audit docs; `repo-cartography`; old setup roadmaps; `games-actionability-roadmap`; broad building roadmaps | Context only. Many claims were already closed by #513–#527. |
| **Stale / needs cleanup** | `superbot-source-of-truth-index`; `superbot-next-session-roadmap`; `superbot-architecture-priority-map`; `cog-functionality-audit`; parts of `direct-db-exception-ledger`; `resource_provisioning.py` docstring | The source-of-truth index stops its server-management summary at #523; roadmap/priority documents still foreground already-shipped RC work; cog tracker still shows DiagnosticCog broken; direct-DB ledger says cleanup has reads only while cleanup commands/modals write prohibited words directly. |
| **Contradicted by source** | `docs/ai-config-ownership.md` guild-preset/UI claims; `docs/ownership.md` claim that channel delete is lifecycle-owned on all user paths | AI source supports only channel/category preset application. Channel delete panel directly calls Discord despite ownership contract. These are actionable reconciliation items, not reasons to invent new seams. |

## 4. Shipped work not to duplicate

| Shipped work | Verified source/history | Follow-up only |
|---|---|---|
| #520 roadmap / phase 0 | Roadmap exists. | Treat sequencing as historical; current queue comes from status/source. |
| #521 moderation convergence / PR1 | Manual commands and modals route through `moderation_service`; invariant exists. | Add configuration depth (roles, destinations, escalation, DMs); cases/evidence/appeals remain later product decisions. |
| #522 role feasibility + `MultiRoleSelector` / PR2 | Shared selector and feasibility utilities exist. | Adopt consistently; paging/search and selector parity should be verified at high cardinality. |
| #523 lifecycle contracts + channel service / PR3+4 | Lifecycle contract and channel rename/move/delete/reorder service exist. | Route the delete view bypass; create/clone/lock/overwrites/category lifecycle/arbitrary positioning remain outside owner. |
| #524 docs reconciliation | Reconciled #521–#523. | Reconcile again for #525–#528 and newly found source contradictions. |
| #525 role lifecycle + safe threshold clearing / PR5 | Manual create/edit/delete route through `RoleLifecycleService`; time/XP clearing is field-specific. | Member assignment, reaction-role routing, reorder/templates remain deferred. |
| #526 dynamic time/XP role config / PR6 | Selector-driven, ID-first dual-read and stale diagnostics shipped. | Add bulk “Clear missing”; selector-driven Edit Role; decide long-term legacy name fallback retirement only after safe migration evidence. |
| #527 channel move/reorder / PR7 | Move/reorder panel and top/bottom primitive shipped. | Arbitrary before/after, revert-safe changes, category UI, and comprehensive multiselect/live checks remain. |
| #528 runtime/live-audit fixes | Role panel discord.py 2.7 collisions fixed; Diagnostic recent-errors/schema/clamp fixes shipped; journal added. | Pin dependency; paginate dense diagnostics; update stale tracker; continue live audit. |

## 5. Stability findings by root cause

### 5.1 Dependency and runtime risks

#### F1 — Pin discord.py to the verified compatibility band
- **Severity/status:** P1, confirmed.
- **Evidence/root cause:** `requirements.txt` has `discord.py>=2.3.0`; #528 fixed collisions caused by 2.7.1 internal changes. Fresh CI installs can silently resolve a later incompatible release.
- **Direction/tests:** pin `discord.py>=2.7,<2.8`; add/import an invariant or compatibility smoke covering overridden/private-ish `discord.ui` names; run the full quality suite and live panel boot.
- **Blocks:** new feature work **yes** until pinned; BTD6 mapping indirectly; AI expansion indirectly.

#### F2 — Live-test capability documented but unavailable here
- **Severity/status:** P1, confirmed environment limitation.
- **Root cause:** session journal describes injected credentials/Postgres that this container lacks.
- **Direction/tests:** restore the documented environment or explicitly revise the journal to distinguish environment variants. Complete the live audit while watching one boot-id-scoped log stream.
- **Blocks:** declaring bot-wide stability **yes**; BTD6/AI live expansion gates **yes**; does not block docs-only planning.

### 5.2 Interaction and persistent-view risks

#### F3 — The live cog audit is incomplete and stale after #528
- **Severity/status:** P1, confirmed.
- **Evidence:** most entries in `cog-functionality-audit` remain `❓`; DiagnosticCog master status remains broken despite #528 fixing its recorded hard failures; RoleCog is inconsistently shown as `🔴→✅` and later `🟡`.
- **Root cause:** tracker was seeded during a live pass, then fixes landed without a final reconciliation/completion pass.
- **Direction/tests:** finish command/panel walk cog-by-cog; record exact command, panel path, environment gate, log outcome, and bug root cause. Update status immediately with each fix.
- **Blocks:** broad new feature work, BTD6 mapping, and AI expansion **yes**.

#### F4 — Interaction safety is not comprehensively self-maintaining
- **Severity/status:** P2, likely / needs live verification.
- **Evidence:** many cogs/views still use raw `interaction.response`/`followup` calls; raw use is not automatically wrong, but #528 demonstrated response timing and post-redeploy panel failures are real regression classes. The interaction router emits benign unhandled-prefix noise for most in-memory views.
- **Direction/tests:** do not mass-rewrite blindly. During the live audit, fix only confirmed double-response/expired-anchor/timeout failures, then add focused invariants/helpers for the proven class. Consider safety-net router registration only if it provides graceful expired-panel behavior without changing authority posture.
- **Blocks:** feature expansion only if hard failures are found.

#### F5 — Dense DiagnosticCog views need usability pagination
- **Severity/status:** P2, confirmed UX gap.
- **Evidence:** #528 clamps total embeds, preventing failure, but the journal records dense `platform_*` subviews as a follow-up.
- **Direction/tests:** paginate only dense subviews using existing paginator/navigation primitives; preserve the global clamp as the final safety net.
- **Blocks:** no, unless live audit finds inaccessible data.

### 5.3 Server-management and service-boundary gaps

#### F6 — Channel delete panel bypasses lifecycle ownership
- **Severity/status:** P1, confirmed.
- **Evidence:** `views/channels/delete_panel.py::_DeleteConfirmView.confirm_btn` calls `channel.delete()`; `docs/ownership.md` assigns delete to `ChannelLifecycleService`; `test_no_direct_channel_mutations.py` checks only `ChannelCog`.
- **Root cause:** PR3/4 routed cog commands but did not widen the invariant and route all view surfaces.
- **Direction/tests:** route the confirmation view through the existing service; preserve batch partial-failure rendering; widen invariant coverage to `views/channels/**` while excluding message edits.
- **Blocks:** new server-management work **yes**; BTD6/AI no direct block.

#### F7 — Channel management remains intentionally incomplete
- **Severity/status:** P2, confirmed unfinished.
- **Evidence:** create/clone/lock/unlock/permission overwrites remain on cog/view paths; category CRUD is not first-class; reorder supports top/bottom only; no revert-safe flow.
- **Direction/tests:** after F6, classify ownership per operation. Creation should use provisioning where declarative; lifecycle changes should extend the existing service, not create a new manager. Add multiselect/high-cardinality/stale-selection/permission-race tests.
- **Blocks:** broad server-management expansion; not bot-wide stability unless live broken.

#### F8 — Role UX and ownership follow-ups remain
- **Severity/status:** P2, confirmed unfinished.
- **Evidence:** journal/source tracker records missing bulk stale-row clearing and free-text Edit Role. Member assignments/reaction-role routing, reorder, and templates are explicitly outside `RoleLifecycleService` today.
- **Direction/tests:** first ship bulk “Clear missing” and selector-driven Edit Role through existing owners. Separately decide whether member assignment needs a canonical service; do not fold it into object lifecycle without a contract decision.
- **Blocks:** server-management polish; templates/AI role generation should wait.

#### F9 — Moderation configuration is shallow, while mutation convergence is healthy
- **Severity/status:** P2, confirmed unfinished.
- **Evidence:** manual actions route through `moderation_service`; current plan defers mod roles, log destinations, escalation, and DMs. Cases/evidence/appeals/mod notes have no accepted product model.
- **Direction/tests:** implement only first-class configuration through settings/bindings/server logging, preserving `mod_logs` as authoritative history. Treat case workflow as a separate maintainer decision.
- **Blocks:** setup convergence and server-management hub; not bot-wide feature work.

### 5.4 Cleanup configuration gaps

#### F10 — Cleanup has split ownership and no coherent operator model
- **Severity/status:** P1, confirmed.
- **Evidence:** governance owns inherited `cleanup_policies`; `cleanup_cog` directly reads/writes prohibited words and caches them; `cleanup/panel.py` describes a static config whitelist; history cleanup is a separate plan/service; setup exposes named cleanup levels/profiles, not the full runtime behavior.
- **Root cause:** “cleanup” currently combines command-feedback cleanup, prohibited-word automod, history deletion, and static exemptions without one versioned policy contract.
- **Direction/tests:** PR8 must first write a policy/ownership contract and compatibility migration plan. Keep governance policy writes through governance; introduce or designate a cleanup mutation/orchestration owner for prohibited words/history/exempt scopes only if it resolves the split. Preserve existing behavior by default.
- **Blocks:** server-management setup/hub and broad cleanup feature work **yes**.

#### F11 — No unified cleanup preview/dry-run/version/audit story
- **Severity/status:** P1, confirmed.
- **Evidence:** server-management status still queues cleanup schema/versioning and builder/dry-run; current panel supports word management/history cleanup but not a single explainable preview of policy outcomes.
- **Direction/tests:** after F10's contract, add deterministic preview with matched rule, scope/source, proposed deletion/warning/log route, and zero mutation; version policy changes and emit deterministic events/audit companions.
- **Blocks:** setup cleanup expansion and server-management hub **yes**.

#### F12 — Direct-DB ledger is stale for cleanup
- **Severity/status:** P2, confirmed docs/source drift.
- **Evidence:** ledger says `cleanup_cog` has reads only; source directly calls `add_prohibited_word`/`remove_prohibited_word` in commands and modals. `docs/ownership.md` currently permits direct prohibited-word writes, so this is not an unclassified violation—but the ledger statement is false.
- **Direction/tests:** correct ledger before deciding whether a service migration is required; add a drift check that inventories direct cog/view writes against the ledger.
- **Blocks:** architecture confidence, not runtime.

### 5.5 Setup wizard gaps

#### F13 — Setup is architecturally mature but live behavior remains unverified
- **Severity/status:** P2, needs live verification.
- **Evidence:** setup has session/draft/operations, recovery view, durable anchor rendering, skip/delegate commands, readiness/repair services, and extensive tests. Historical setup roadmaps explicitly say they are directional. Audit consolidation carried launcher recovery and skip-provenance gaps as not runtime-reproduced.
- **Direction/tests:** do not rewrite. Verify fresh launch, resume, stale anchor, section exception recovery, skip/unskip provenance, delegate/undelegate, transient final review, partial apply, and re-run repair. Confirm every apply route uses setup operations/canonical owners.
- **Blocks:** setup expansion and server-management hub; bot-wide work only if hard failures appear.

#### F14 — Setup sections lag the remaining management owners
- **Severity/status:** P2, confirmed by remaining queue.
- **Direction/tests:** add role/moderation/governance sections only after cleanup/mod configuration contracts land; diagnostics/repair must stage operations, never mutate directly. AI advisor remains deterministic/env-gated here and must be described as such.
- **Blocks:** server-management hub; not immediate runtime stability.

### 5.6 AI configuration and preset gaps

#### F15 — Binding AI ownership doc overstates guild preset support
- **Severity/status:** P1, confirmed contradiction.
- **Evidence:** binding doc says preset application at channel/category/guild scope and describes a guild button; `ai_behavior_profile_service._SUPPORTED_SCOPES` is channel/category only and `BehaviorChooserView` has Channel/Category only. Tests explicitly assert unsupported scopes are refused.
- **Root cause:** docs were updated to a desired end-state without the source implementation, or source implementation stopped short of the binding contract.
- **Direction/tests:** maintainer/Opus must choose: implement sentinel-safe guild preset application preserving all unrelated fields, or amend the binding doc to state guild scope is intentionally unsupported. Given maintainer priority, implementation is recommended, but it is a configuration-correctness PR—not AI expansion.
- **Blocks:** AI expansion **yes**; BTD6 mapping indirectly because AI grounding uses these policies.

#### F16 — AI operator interface is powerful but fragmented
- **Severity/status:** P2, confirmed unfinished.
- **Evidence:** snapshot/readiness/why-no-response/support-report/policy preview/routing matrix exist; behavior chooser exposes channel/category presets and sends advanced users to raw policy editors. Guild baseline configuration is not equally understandable.
- **Direction/tests:** build one coherent operator journey over `AIConfigSnapshot`: status/degraded reason → effective precedence → behavior preset → advanced overrides → why-no-response/support report. Preserve mutation chokepoints and unrelated fields.
- **Blocks:** AI feature expansion **yes**.

#### F17 — AI ownership and guardrails are otherwise healthy and must not be refactored
- **Severity/status:** stable enough / confirmed by source and tests.
- **Evidence:** snapshot service is the read model; mutation services own writes; no new direct policy/instruction write path was found; extensive audit, cooldown, readonly-tool, grounding, and BTD6 boundary tests exist.
- **Direction/tests:** add missing operator/preset tests only. Preserve central natural-language stage, resolver precedence, tool whitelist, and audit-row guarantees.
- **Blocks:** no; this is a must-preserve constraint.

### 5.7 BTD6 readiness gaps

#### F18 — Extraction/cutover remains explicitly paused
- **Severity/status:** P1, confirmed gate.
- **Evidence:** ADR-006 says extraction stays paused until the follow-on provenance contract/schema PR. `btd6-gamedata-decode-status` also records cutover gates and unverified live items.
- **Direction/tests:** preserve current data. Do not restart extraction. First implement/verify the accepted provenance object and owner-per-fact matrix without inventing a parallel read facade.
- **Blocks:** BTD6 mapping **yes**.

#### F19 — Provider parity is tested piecemeal, not proven end-to-end
- **Severity/status:** P1, needs verification.
- **Evidence:** file, cloud, and Postgres provider tests exist; docs describe a shared seam; earlier consolidation explicitly left stats/paragon cross-backend parity unverified. This pass did not have live Postgres/cloud infrastructure.
- **Direction/tests:** a small verification PR should compare required/optional names, payload hashes/schema, tower/hero/map/mode/round/bloon/CT/paragon/stats consumers, status/source labels, stale-cache behavior, and unavailable/degraded behavior across all three providers.
- **Blocks:** BTD6 mapping and production backend cutover **yes**.

#### F20 — Provenance/freshness is not yet one user-facing contract
- **Severity/status:** P1, confirmed.
- **Evidence:** no source implementation named `DataProvenance` or `SourceAttribution`; source registry/freshness/cache services exist, but facts and static providers do not uniformly carry the accepted composed object.
- **Direction/tests:** implement ADR-006 as a bounded contract/schema/read-model PR; verify all user/AI renderers can attribute source and freshness. Keep `btd6_view_model_service` as composer.
- **Blocks:** BTD6 mapping **yes**; AI/BTD6 expansion **yes**.

#### F21 — BTD6 commands/views are heavily unit-tested but live-unverified
- **Severity/status:** functional but unfinished / needs live verification.
- **Evidence:** broad cog/service/view/parser/guard suite exists; every BTD6 cog remains `❓` in the live audit; decode status contains explicit unverified answerability items.
- **Direction/tests:** run the smoke checklist against the file backend first, then parity backends. Verify fetched data reaches every renderer and answer path; classify unavailable live sources as degraded.
- **Blocks:** BTD6 expansion **yes**.

### 5.8 Cog/panel stability map

“Stable enough” below means automated evidence is substantial and no current source defect was found; it does **not** override the missing live audit.

| Cog/surface | First-pass classification | Root-cause note / next verification |
|---|---|---|
| BootstrapAccessCog | stable enough | Central command admission; preserve. |
| AdminCog | unverified / needs live test | Strong command tests; owner-only destructive restart/load/unload should be tested last. |
| DiagnosticCog | functional but unfinished | #528 fixed hard failures; tracker stale; dense subviews need pagination check. |
| SettingsCog | stable enough, needs live test | Strong pipeline/UI tests; verify capability and high-cardinality selectors live. |
| SetupCog | functional but unfinished | Strong architecture/tests; recovery/skip/delegate/anchor workflow needs live pass. |
| LoggingCog | functional but unfinished | Provisioning/routes tested; default-off behavior and destinations need live check. |
| HelpCog | functional but unfinished | Good route/discovery tests; command/hub parity remains a broader cleanup theme. |
| RoleCog | functional but unfinished | Core lifecycle and ID-first automation shipped; two confirmed UX warts; scheduler env-gated. |
| ChannelCog | architecture cleanup needed | Lifecycle service exists, but delete view bypass confirmed; remaining operations incomplete. |
| ModerationCog | functional but unfinished | Manual actions converged; configuration shallow; live logging destination behavior unverified. |
| Cleanup | should block server-management expansion | Split ownership, static whitelist, direct writes, shallow policy/preview. |
| CommunityCog | unverified / needs live test | Only a hub-view test; verify actions and destinations. |
| EconomyCog | unverified / needs live test | Service invariants/tests exist; panel/work/inventory flows need live transaction check. |
| XpCog | functional but unfinished / env-gated | Tests and service owner exist; scheduler off, manual run and cache behavior need live check. |
| InventoryCog | unverified / needs live test | Sparse direct coverage; verify display/navigation and guild scope. |
| MiningCog | functional but unfinished | Good unit coverage but direct view DB mutations are accepted legacy architecture debt; live progression/crafting pass needed. |
| Leaderboard | unverified / needs live test | Empty-state coverage exists; verify each category and pagination. |
| BlackjackCog | unverified / needs live test | Persistence/refund/replay tests exist; verify terminal button disabling and restart contract. |
| Rock Paper Scissors | unverified / needs live test | Persistence/stage tests exist; verify PvP timeout/terminal controls and panels. |
| Deathmatch | unverified / needs live test | Sparse tests; verify challenge lifecycle, timeout, terminal controls. |
| GamesCog | stable enough, needs live test | Hub/navigation covered; child games remain unverified. |
| CountingCog | stable enough, needs live test | RC-15 shipped; persistence/stage coverage good; verify recovery/logging live. |
| ChainCog | unverified / architecture cleanup needed | Direct DB writes accepted by ledger; live panel/stage verification needed. |
| FourTwentyCog | unverified / needs live test | Minimal surface/test; verify command response. |
| ProofChannelCog | likely risk / needs live test | No named tests found; direct exception-swallow patterns merit focused audit. |
| BTD6Cog / Reference / Events / Strategy / Ops | should block BTD6 expansion | Heavy automated coverage, but live tracker all `❓`; provider/provenance gates remain. |
| ParagonCog | blocked by environment / needs live test | Service/view/math tests strong; API fallback behavior needs live outbound check. |
| AICog | blocked by environment + config cleanup needed | Central guards strong; provider disabled is degraded; guild preset/operator journey incomplete. |
| General | unverified / needs live test | No named tests found; audit all commands/panel interactions. |
| UtilityCog | unverified / needs live test | No named tests found; audit polls/timers/tools and terminal interactions. |

### 5.9 Test, observability, docs, and architecture drift

#### F22 — Invariants miss view-owned Discord mutations
- **Severity/status:** P1, confirmed by F6.
- **Direction/tests:** widen lifecycle mutation invariants from named cogs to the full owning surface. Prefer AST checks keyed to actual mutation receivers and explicit exclusions.
- **Blocks:** confidence in server-management expansion **yes**.

#### F23 — Planning docs can cause already-shipped work to be re-planned
- **Severity/status:** P2, confirmed.
- **Evidence:** source-of-truth index stops at #523; next-session roadmap/priority map still foreground earlier waves; server status is newer and correct; cog tracker is stale after #528.
- **Direction/tests:** one docs reconciliation PR after decisions/fixes, with doc-pin tests for shipped/current status where practical.
- **Blocks:** not runtime, but increases repeated-work risk.

#### F24 — Tracked architecture debt remains high but stable
- **Severity/status:** P3, confirmed / non-blocking.
- **Evidence:** strict checker reports 87 known warnings and 0 errors.
- **Direction/tests:** do not launch a broad cleanup. Retire warnings only when touched by coherent owner work, and never add untracked warnings.
- **Blocks:** no, unless a new error appears.

#### F25 — Passing tests still emit asynchronous resource warnings
- **Severity/status:** P2, confirmed test/observability gap.
- **Evidence:** the 5,831-test targeted run passed but emitted un-awaited coroutine warnings involving `AutomationScheduler.run_forever`, RPS reminder tasks, and Blackjack tournament auto-start, plus expected cog-size/aiohttp warnings.
- **Direction/tests:** reproduce each coroutine warning in its smallest test slice; fix fixture/task cleanup or real lifecycle leakage; promote an actionable warning policy rather than ignoring all warnings.
- **Blocks:** not immediately, but unresolved task-lifecycle warnings weaken confidence in live stability and should be folded into PR B.

## 6. First-draft implementation sequence for Opus refinement

The sequence below is deliberately staged. Per session, refine and execute only the next **2–3 PRs**, not the entire list at once.

### PR A — Runtime/dependency and lifecycle guardrails
- **Objective:** remove known fresh-install/runtime risk and close the confirmed channel lifecycle bypass.
- **Scope:** pin discord.py; route delete confirmation view through `ChannelLifecycleService`; widen channel-mutation invariant to views; add compatibility regression checks for the #528 collision class.
- **Out of scope:** new channel features, broad interaction-helper rewrite.
- **Likely files:** `requirements.txt`, `views/channels/delete_panel.py`, channel lifecycle tests/invariants, possibly dependency docs.
- **Dependencies:** none.
- **Tests:** channel lifecycle service/view/invariant tests; views; cogs; full quality; live Role/Channel/Diagnostic panels under pinned install.
- **Rollback risk:** low-medium; delete rendering must preserve partial failures and defer timing.
- **Stop conditions:** service cannot preserve existing batch UX; a newer discord.py is required elsewhere; open overlapping PR.
- **Why first:** closes two proven regressions/risk classes before deeper management work.

### PR B — Complete live cog audit and fix only hard-broken surfaces
- **Objective:** establish a trustworthy bot-wide stability baseline.
- **Scope:** restore live-test environment; execute every tracker row; fix confirmed hard failures in small cog-batched commits; add root-cause regression tests; reconcile statuses.
- **Out of scope:** feature expansion, polish-only redesign, broad thin-cog migration.
- **Likely files:** `cog-functionality-audit`, affected cogs/views/tests, `.session-journal.md` only for durable environment lessons.
- **Dependencies:** PR A.
- **Tests:** relevant slice per fix, full quality at end, boot/log scan scoped to boot ID.
- **Rollback risk:** per-cog; keep fixes independently revertible.
- **Stop conditions:** environment cannot be restored; a baseline failure invalidates assumptions; a fix requires new architecture.
- **Why now:** all later “stable enough” decisions depend on completed runtime evidence.

### PR C — Cleanup ownership/policy schema and compatibility contract
- **Objective:** define the coherent owner and versioned model before adding UI depth.
- **Scope:** reconcile command cleanup, prohibited words, history cleanup, exemptions/ignored scopes, warning/feedback behavior, and log routes; define migration/default compatibility; correct direct-DB ledger.
- **Out of scope:** full builder UI and destructive cleanup execution redesign.
- **Likely files:** cleanup/governance ownership docs, policy models/migrations only if approved, cleanup services/db/tests, direct-DB ledger.
- **Dependencies:** PR A; decisions from Opus/maintainer on policy boundaries.
- **Tests:** governance/cleanup/service/db/invariant tests; migration bootstrap; behavior-preservation cases.
- **Rollback risk:** high if defaults change; require additive migration and exact legacy-default tests.
- **Stop conditions:** no agreed ownership split; migration would be destructive; thread-scope semantics conflict with RC-5.
- **Why before builder/setup:** prevents UI from cementing the current split model.

### PR D — Cleanup builder, dry-run, diagnostics, and server-management UX warts
- **Objective:** make cleanup explainable/configurable and finish bounded role/channel UX loose ends.
- **Scope:** cleanup dry-run/preview/diagnostics over PR C; bulk clear stale role rows; selector-driven Edit Role; selector/multiselect parity checks; optionally dense Diagnostic pagination if live audit confirms need.
- **Out of scope:** role templates/AI generation, arbitrary channel reorder, cases system.
- **Likely files:** cleanup views/services, role panels/management panel, shared selectors, diagnostics views/tests.
- **Dependencies:** PR C and live audit findings.
- **Tests:** cleanup preview no-write invariant; policy source/version/audit tests; role selector/stale clearing; high-cardinality selector tests; full quality/live panels.
- **Rollback risk:** medium; cleanup preview must never mutate.
- **Stop conditions:** dry-run cannot be deterministic; UX change bypasses canonical owner.
- **Why before setup:** setup should consume completed managers, not duplicate incomplete controls.

### PR E — Moderation configuration and setup consistency/recovery
- **Objective:** deepen canonical management configuration, then make setup consume it safely.
- **Scope:** mod roles/destinations/escalation/DM settings through existing pipelines; live-verify and repair setup recovery/skip/delegate/provenance/anchor issues; add role/mod/governance sections only where owners are ready.
- **Out of scope:** numbered cases, appeals/evidence/mod notes, setup rewrite.
- **Likely files:** moderation config services/views/settings/bindings/logging; setup sections/operations/recovery/tests.
- **Dependencies:** PR C/D for cleanup; #521 service convergence.
- **Tests:** moderation service/config/audit/log routing; setup session/draft/operations/recovery/live partial apply; no-direct-write invariants.
- **Rollback risk:** medium-high; staged operations and permissions must preserve existing behavior.
- **Stop conditions:** setup must directly mutate; product decision on escalation/cases is unresolved; live recovery cannot be tested.
- **Why before hub:** hub should aggregate mature managers.

### PR F — AI behavior/configuration correctness and operator clarity
- **Objective:** make presets and effective policy understandable without expanding AI capability.
- **Scope:** resolve guild-preset doc/source decision; implement sentinel-safe guild application if approved; preserve unrelated fields; unify snapshot-driven status/preset/preview/why-no-response/support journey; clearly render disabled/env-gated provider state as degraded.
- **Out of scope:** new tools/providers/features, central-stage refactor.
- **Likely files:** AI binding doc, behavior profile service/views, projection/readiness/why/support renderers, AI tests.
- **Dependencies:** PR A/B baseline; maintainer decision on guild presets (recommended: support them).
- **Tests:** snapshot non-mutation; mutation chokepoint; field preservation at all supported scopes; precedence; audit/cooldown/tool whitelist/grounding guard suites; disabled-provider UX.
- **Rollback risk:** medium; holistic guild policy writes can erase unrelated fields if sentinel preservation is wrong.
- **Stop conditions:** any direct DB write; central stage/tool whitelist changes; unrelated field loss.
- **Why before AI expansion/BTD6 mapping:** configuration and guard observability are prerequisites.

### PR G — BTD6 readiness verification and ADR-006 provenance contract
- **Objective:** satisfy the gate without adding data.
- **Scope:** implement/verify the accepted provenance object and owner matrix; cross-backend provider parity; source health/freshness/cache reporting; file-backend live smoke; Postgres/cloud parity when infrastructure is available; stale/partial command/button audit.
- **Out of scope:** extraction, new mapped fields, broad strategy/AI features.
- **Likely files:** ADR/schema docs, existing BTD6 data/provider/view-model/source-health services, parity tests, smoke checklist.
- **Dependencies:** PR B and PR F; backend infrastructure.
- **Tests:** all BTD6 provider/service/view/parser/AI-boundary/grounding guards; cross-backend fixtures/hashes/consumer outputs; live smoke.
- **Rollback risk:** medium-high if read models change; make provenance additive and preserve current renderers until parity is proved.
- **Stop conditions:** provider outputs differ without an accepted reason; provenance cannot reach AI/user renderers; extraction work enters scope.
- **Why before mapping:** ADR-006 explicitly requires it.

### PR H — Source-of-truth and remaining-queue reconciliation
- **Objective:** leave future agents one accurate current path.
- **Scope:** update source index through #528 and PR A–G; reconcile cog tracker, server-management remaining queue, AI binding decision, BTD6 gate status, stale historical banners/comments, direct-DB ledger.
- **Out of scope:** source behavior changes.
- **Likely files:** planning/status/ownership docs and doc-pin tests.
- **Dependencies:** after decisions and major stabilization results; small doc corrections may land alongside owning PRs.
- **Tests:** docs tests, link/reference checks, targeted doc-pin tests, full quality.
- **Rollback risk:** low.
- **Stop conditions:** docs claim a result that was not source/live verified.
- **Why last:** records the verified final state, while urgent false claims should still be corrected in their owning PRs.

### Gates after the sequence

- **New general features:** allowed only after PR A/B produce a clean automated + live baseline and no P0/P1 hard-broken surfaces remain.
- **AI expansion:** allowed only after PR F and the full AI guard suite pass, with no direct-write or field-preservation regression.
- **BTD6 data mapping/extraction:** allowed only after PR G proves ADR-006 provenance, provider parity, freshness/source health, AI grounding guards, and live answerability. Maintainer must explicitly lift the pause.
- **Server Management Hub / AI role templates:** remain after the specialized managers/configuration are stable; do not pull them forward.

## 7. Opus handoff — copy/paste ready

> You are refining the first stability-preimplementation pass against source at commit `8d47035` (merge #528). I verified that server-management PR1–PR7 and #528 shipped and must not be re-planned. The strongest confirmed new issue is that `views/channels/delete_panel.py::_DeleteConfirmView.confirm_btn` still calls `channel.delete()` directly, bypassing the shipped `ChannelLifecycleService`; the invariant only checks `ChannelCog`. `requirements.txt` also still leaves discord.py unbounded above. Cleanup remains split across governance policies, direct prohibited-word writes/process caches, static whitelist config, and history cleanup, with no unified versioned/dry-run operator model. The direct-DB ledger is stale because it calls cleanup reads-only. The AI binding doc says presets work at guild scope and describes a guild button, but source/tests support only channel/category; choose whether to implement sentinel-safe guild presets (recommended) or correct the binding doc. ADR-006 explicitly keeps BTD6 extraction paused; no `DataProvenance`/`SourceAttribution` implementation was found, and file/cloud/Postgres consumer parity remains unproved. The central AI snapshot/mutation/audit/grounding architecture otherwise appears healthy and must be preserved.
>
> Automated checks: strict architecture passed with 0 errors/87 tracked warnings. The initial full-quality run had formatting/lint/mypy green but pytest collection failed only because Python 3.10 dependencies were absent; dependencies were installed and broad targeted tests were run. The final full-quality rerun passed (7,461 passed, 3 skipped); rerun `PYENV_VERSION=3.10.20 python3.10 scripts/check_quality.py --full` before any implementation. `gh` is unavailable, so open PRs were not verified. The journal's live-bot runbook could not be used because this container lacks its documented token, DB URL, postgres user, and binaries. Therefore most cog surfaces and all BTD6 live behavior remain live-unverified.
>
> Recommended PR order: **A runtime/dependency + channel boundary guardrails → B complete live cog audit/hard failures → C cleanup ownership/schema contract → D cleanup builder + bounded role/channel UX → E moderation config + setup consistency → F AI config/preset correctness → G BTD6 provenance/provider-parity verification → H docs reconciliation.** Refine only the next 2–3 PRs for execution.
>
> Read first: `.claude/CLAUDE.md`, `.session-journal.md`, `docs/AGENT_ORIENTATION.md`, `docs/planning/stability-preimplementation-plan-2026-06-05.md`, `docs/ownership.md`, `docs/runtime_contracts.md`, `docs/planning/server-management-status-2026-06-05.md`, `docs/planning/cog-functionality-audit-2026-06-05.md`, `docs/ai-config-ownership.md`, `docs/decisions/006-btd6-data-provenance-ownership.md`, then the exact source/tests for PR A.
>
> Decisions needed from maintainer: (1) restore/clarify live-test environment; (2) support guild-scope AI presets versus amend the binding doc; (3) exact cleanup ownership/policy boundary and whether prohibited-word/history writes gain a canonical service; (4) how much remaining channel/member-assignment lifecycle convergence belongs before the hub; (5) explicit criteria to lift the BTD6 extraction pause.
>
> Stop if: remote `main`/open PR state differs; full quality is red after dependencies are present; live-test capability is required but unavailable; a proposed fix creates a new owner instead of using an existing one; AI policy/instruction writes bypass mutation chokepoints; BTD6 extraction enters scope; provenance/provider parity fails; setup must mutate directly; or a binding contract/source contradiction is not resolved before implementation.
