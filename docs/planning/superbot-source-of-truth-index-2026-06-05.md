# SuperBot — Planning Source-of-Truth Index

> **`historical` — superseded as a daily router by `docs/current-state.md`.**
> Start at `docs/current-state.md` for *what is true now*. This file is kept for
> its RC-1…RC-15 audit-reconciliation history (useful for *why* a decision was
> made, not *what is current*). It layered the 2026-06-05 audit-consolidation
> outcome on top of `docs/AGENT_ORIENTATION.md` (the binding orientation).
>
> **Date:** 2026-06-05
>
> **The one rule:** when a doc and a source file disagree, **the source file
> wins** (`.claude/CLAUDE.md`). This index records *which* docs are most likely
> to disagree, and why.

---

## Read first (in this order)

1. `.claude/CLAUDE.md` — session workflow + CI parity + CodeGraph + arch invariants.
2. `docs/AGENT_ORIENTATION.md` — binding "reading order by task".
3. **`docs/planning/superbot-audit-consolidation-2026-06-05.md`** — the verified
   findings (RC-1 … RC-15) with file:line evidence. Trust this over the raw
   audit docs.
4. **`docs/planning/superbot-architecture-priority-map-2026-06-05.md`** — what to
   fix first, dependency graph, must-not-touch list.
5. **`docs/planning/superbot-next-session-roadmap-2026-06-05.md`** — the PR
   sequence + per-session reading list + stop conditions.

---

## Shipped since this index was written (2026-06-05)

RC-2/5/15 shipped in **#513**; the Ideas Lab backlog in **#514**; RC-1
(lazy-import checker report) in **#515**; **RC-7** (feature-cleanup-provider
registry — `session_gc` is now a scheduler, `services.game_state_cleanup` owns
the ADR-002 refund sweep) in **#516**. The post-#516 wave (PR1–PR6: IL-1/2/3
operator explainers, RC-6 migration guard, RC-3 fail-open posture, RC-8A Direct-DB
ledger + RC-13 + RC-14, and the RC-11 AI-guard coverage map) all shipped in
**#517**. RC-3's posture is pinned in **ADR-004** (Accepted).

**ADR-005 / ADR-006 / ADR-007 are now `Accepted`** (ratified this session):
RC-4 → ADR-005 **A1 + F1** (capability-native authority + operator kill-switches,
implemented this session); RC-10 → ADR-006 **Hybrid** provenance storage (schema/
extraction still paused); RC-12 → ADR-007 **M1** (shared media subsystem; ownership
row + registration are a follow-on). The RC-11 cooldown-ordering guard was pinned
this session. See the roadmap's "Addendum 3 (post-#517)" for details.

**Server-management initiative (#520–#523).** #520 landed the roadmap; #521 (PR1)
converged moderation onto `services.moderation_service` (three-signal audit;
`clearwarnings` token); #522 (PR2) added `utils/role_feasibility.py` +
`views/selectors/multi_role.MultiRoleSelector`; #523 (PR3+PR4) added
`services/lifecycle/contracts.py` + `services/channel_lifecycle_service.py` (channel
rename/move/delete) and the `channel.lifecycle_changed` event. The roadmap's PR
ordering is **superseded** by the implementation plan's sequence (which is what
shipped). The live record is the new
**`docs/planning/server-management-status-2026-06-05.md`** tracker — start there for
server-management state and the remaining queue (PR5+).

---

## Current planning docs (trust now)

| Doc | Trust | Note |
|---|---|---|
| `docs/planning/superbot-audit-consolidation-2026-06-05.md` | ✅ current | Supersedes the five raw audit docs' confidence claims where source disagreed. |
| `docs/planning/superbot-architecture-priority-map-2026-06-05.md` | ✅ current | Priority + dependency ordering. |
| `docs/planning/superbot-next-session-roadmap-2026-06-05.md` | ✅ current | PR/session plan. |
| `docs/planning/superbot-source-of-truth-index-2026-06-05.md` | ✅ current | This file. |
| `docs/planning/superbot-ideas-lab-2026-06-05.md` | ✅ current (advisory) | Brainstorm backlog. §2 (operating decisions) + §6 (rejection ledger) are binding; the rest is gated suggestions — re-verify against source before building. |
| `docs/planning/server-management-status-2026-06-05.md` | ✅ current | **Live status tracker** for the server-management initiative — what shipped (#520–#523) and the remaining queue (PR5+). Authoritative on *what is done*. |
| `docs/planning/server-management-implementation-plan-2026-06-05.md` | ✅ current (scope) | Per-PR scope/tests/risks for PR1→PR14. PR1–PR4 shipped; see Rev 3 note for the `clearwarnings` correction. Use with the status tracker. |
| `docs/planning/server-management-roadmap-2026-06-05.md` | ✅ current (target arch) | Target architecture + maintainer decisions. **PR ordering superseded after #523** — use the implementation plan / status tracker for sequence. |

---

## Current architecture / binding docs (unchanged authority)

These remain the binding contracts (per `AGENT_ORIENTATION.md`). The audit
consolidation **did not** contradict them; it cited several as the reconciling
authority.

| Doc | Role | Reconciliation note |
|---|---|---|
| `docs/architecture.md` | binding — layering/invariants | Confirmed; the `arch-fix-11` cluster is tracked debt against it, not a contradiction. |
| `docs/ownership.md` | binding — mutation authority + dep direction | Authority for RC-4/RC-7/RC-8 ownership questions. |
| `docs/runtime_contracts.md` | binding — lifecycle guarantees | §3 (PersistentView), §6 (interaction), §8 (game state) directly govern RC-3/RC-7. |
| `docs/platform-consistency-ledger.md` | binding — status ledger | Authority for RC-4 (settings/binding phase state) + binding-cache-no-op safety. |
| `docs/architecture/service_ownership.md` | reference — at-a-glance ownership | `ownership.md` wins on conflict. |
| `docs/helper-policy.md` | binding — helper placement | Read before RC-8 view/util moves. |
| `docs/decisions/001-no-redis-backed-state.md` | ADR (immutable) | Rejects external session/state store. |
| `docs/decisions/002-game-state-not-restart-safe.md` | ADR (immutable) | **Reclassifies Agent C#4**: game restart behavior is accepted design, not a bug. |
| `docs/decisions/003-deferred-followups-after-refactor-program.md` | ADR | §3 already owns several Agent C "new" items — reconcile before re-planning. |
| `docs/decisions/004-interaction-fail-open-posture.md` | **ADR (Accepted 2026-06-05)** | Per-surface fail-open/closed posture (RC-3); the contract the RC-3 impl PR fulfils. |
| `docs/decisions/005-capability-native-authority-and-flag-semantics.md` | **ADR (Accepted 2026-06-05)** | RC-4 authority + `*_PRIMARY` flag semantics; A1+F1 implemented. Capability-native settings UI is still a follow-up. |
| `docs/decisions/006-btd6-data-provenance-ownership.md` | **ADR (Accepted 2026-06-05)** | RC-10 provenance/owner-matrix; **Hybrid** storage chosen. BTD6 extraction stays paused until the provenance schema/docs PR. |
| `docs/decisions/007-media-youtube-ownership.md` | **ADR (Accepted 2026-06-05)** | RC-12 media/YouTube ownership; **M1** chosen. Ownership row + service registration are a follow-on. |
| `docs/resource-provisioning-overview.md` | reference (RPM lane) | Pair with the RC-9 correction: pipeline **is** adopted. |
| `docs/help-command-surface-map.md` | binding (doc-test pinned) | Authority for RC-14 help parity. |
| `docs/ai-config-ownership.md` | binding (doc-test pinned) | Read before any AI-cog change (RC-11). |
| `docs/smoke-test-checklist.md` | binding (doc-test pinned) | Required before any runtime PR ships. |
| `architecture_rules/*.yaml` | enforced policy | `layers.yaml` = the `arch-fix-11` tracked-violation source of truth. |

---

## Current subsystem docs (trust, with the noted caveat)

| Doc(s) | Trust | Caveat from this consolidation |
|---|---|---|
| `docs/btd6-data-backends.md`, `docs/btd6-data-pipeline.md`, `docs/btd6-cloud-data.md` | ✅ current | Pair with RC-10: provider-parity is **unverified** (needs live backend); provenance model is a pending decision. |
| `docs/btd6-derived-value-groundedness-finding.md`, `docs/btd6-absence-claim-guard-design.md` | ✅ current | The faithfulness/groundedness guard is confirmed-healthy (RC-11) — preserve. |
| `docs/btd6-smoke-test-checklist.md` | ✅ current | Run before BTD6 runtime PRs. |
| `docs/ai-config-ownership.md`, `docs/ai-service-integration-map.md` | ✅ current (ownership doc is binding) | AI orchestration is healthy; do not refactor the choke point. |
| `disbot/core/runtime/ai/README.md` | ✅ current | Package intent. |
| `docs/server-logging.md` | ✅ current (shipped reference) | — |

> BTD6 has **many** subsystem docs (`docs/btd6-*` — 15+ files). They are
> domain-accurate but verbose; Agent D recommends a single BTD6 data-inventory
> index (a future opportunity, not yet built). Until then, prefer source +
> `btd6_data_service` over any single doc for current field state.

---

## Historical / context-only docs (do NOT implement against as specs)

These are accurate as *history* but describe planned end-states or older bases.
`AGENT_ORIENTATION.md` already classifies most as "plans/roadmaps — read for
context only". The audit consolidation adds the reconciliation column.

| Doc | Why historical | Reconciliation |
|---|---|---|
| `docs/audits/platform-runtime-data-layer-audit-2026-06-05.md` (Agent A) | source-read audit, base `d583dcb`, no local exec | Superseded by consolidation §3/§5. A#5 (provisioning) is **stale**; A#1/#2 are tracked debt. |
| `docs/audits/agent-b-governance-control-audit-2026-06-05.md` (Agent B) | source-read audit, no local exec | Findings confirmed in consolidation §3; trust the consolidation's status flags. |
| `docs/audits/general-feature-layer-analysis-2026-06-05.md` (Agent C) | source-read audit, no local exec | C#4 reclassified (ADR-002); several items overlap ADR-003 §3. |
| `docs/audits/agent-d-btd6-ai-subsystem-audit-2026-06-05.md` (Agent D) | source-read audit, no local exec | Confirmed; drives RC-10/11/12. |
| `docs/repo-cartography-2026-06-04.md` (Codex) | neutral inventory, branch `work`, no `main`/remote | Map is sound; its "unknowns" (YouTube, runtime-AI, cleanup ownership) became RC-12/RC-11/RC-5. |
| `docs/audits/repo-wide-audit-2026-05-29.md` | **older** audit (base `5609fe8`), has a remediation table updated post-#414 | **Check its remediation table before re-fixing** — some boundary items are already closed. The A/B/C/D audits did not cross-reference it. |
| `docs/audits/mutation_boundary_audit.md` | snapshot (2026-05-24) | Companion to `ownership.md`; consult for mutation-boundary history. |
| `docs/loose-ends-audit-roadmap.md` | plan (read for context) | Findings 2/3/5 overlap RC-14; PR L1–L6 predate this plan — reconcile, don't duplicate. |
| `docs/roadmap_setup_platform.md`, `docs/setup_wizard_finalization_plan.md` | plans | Setup is mostly durable-anchor based now (Agent B SETUP-1); some legacy paths drift (B SETUP-2/3/4). |
| `docs/phase_2b_bindings_plan.md`, `docs/phase-2-completion-readiness.md` | phase plans/ledgers | Bindings pipeline shipped; cache invalidation is a safe no-op today (ledger §1). |
| `docs/games-actionability-roadmap.md` | **complete — historical** (per orientation) | Do not treat as active backlog. |
| `docs/ui-view-adoption-audit.md`, `docs/helper-debt-inventory.md` | snapshots | Corroborate RC-8 (views-in-cogs, baseview-inheritance warnings). |
| `docs/cog-hub-coverage-audit.md`, `docs/help-command-surface-map.md` | coverage/surface maps | `help-command-surface-map.md` is doc-test-pinned (current); cog-hub-coverage is a snapshot. |
| `docs/building-roadmap/*`, `docs/settings-customization-*`, `docs/operator-settings-presets.md` | standards + roadmaps | Standards (command-integration, hub-ui, config-input) are current; roadmaps are plans. |
| `docs/ai-readiness-plan.md`, `docs/ai-readiness-pr-notes.md`, `docs/ai-provider-and-grounding-fix-plan.md` | plans | AI is further along than these imply (RC-11 healthy); read for intent only. |

---

## Docs that need later cleanup (tracked, not done this pass)

Per the out-of-scope rule, this pass did **not** rewrite old docs. The following
edits belong to **PR 7 (RC-13)**:

1. `disbot/services/resource_provisioning.py:59` — the "zero production callers"
   docstring is **stale** (real callers exist; consolidation §5). Correct it.
2. Identity-strictness comments in `disbot/bot1.py` and the `guild_resources.py`
   ownership comment — Agent A flagged as stale; **verify line-by-line, then fix**.
3. The five audit docs cite base `d583dcb`; add a one-line "superseded by
   `docs/planning/…consolidation…`" banner so future readers reach the verified
   set first.
4. Consider a single BTD6 data-inventory index (Agent D future opportunity) to
   retire ambiguity across the 15+ `docs/btd6-*` files.

---

## How future agents should verify docs against code

The five 2026-06-05 audits were *source-read only* and one high-impact claim
(provisioning "unadopted") turned out **stale**. Apply this before trusting any
doc claim:

1. **Run the cheap checks first.** `python3.10 scripts/check_architecture.py`
   (0 errors expected, 87 known warnings post-#516) and `check_quality.py --check-only`.
   A doc claiming "X violates layering" is testable in seconds.
2. **Grep for callers before trusting "unadopted"/"zero callers"/"dead".**
   CodeGraph `dead-unresolved` is ~100% false-positive here (`.claude/CLAUDE.md`);
   in-file "zero callers" comments drift. `grep -rn "Symbol" disbot/ --include=*.py`.
3. **Check the tracked-violation allowlist** (`architecture_rules/layers.yaml`)
   before calling a cross-layer import "undetected drift" — it may be `arch-fix-11`.
4. **Check the ADRs** (`docs/decisions/00{1,2,3}`) before calling a behavior a
   bug — it may be an accepted decision (e.g., game restart = ADR-002).
5. **Check the prior audit's remediation table**
   (`docs/audits/repo-wide-audit-2026-05-29.md`) before "discovering" a finding.
6. **Run the relevant test slice.** This pass ran invariants/governance/db/
   runtime/AI-BTD6 (1,450 tests, green). A claim about a subsystem with a test
   directory is one `pytest` away from confirmation.
7. **When a doc and a source file disagree, the source file wins** — re-read the
   file you are about to edit.
