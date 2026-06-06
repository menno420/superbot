# SuperBot — Architecture Priority Map

> **`historical` — 2026-06-05.** For *what is true now*, start at
> **`docs/current-state.md`**. Kept for the RC-n priority / dependency rationale.

> **Status:** planning artifact. Companion to
> `superbot-audit-consolidation-2026-06-05.md` (the verified findings) and
> `superbot-next-session-roadmap-2026-06-05.md` (the PR sequence). This doc
> turns the consolidated root-cause findings (RC-1 … RC-15) into an ordered
> set of architectural priorities — **what to fix first and why**, and just
> as importantly **what to leave alone**.
>
> **Date:** 2026-06-05
>
> Finding IDs (RC-n) are defined in the consolidation doc §7. Read that first.

---

## Architectural principles to preserve

These are the invariants the audits confirmed are *working*. Every priority
below must keep them intact. Breaking one of these to "fix" a finding is a
net loss.

1. **Cogs are thin Discord adapters.** Business rules and DB mutation live in
   services; multi-step orchestration in workflows; UI composition + interaction
   state in views. (Target shape — partially met; RC-8 is the gap, not a
   re-architecture.)
2. **One mutation seam per domain.** Settings → `SettingsMutationPipeline`,
   bindings → `BindingMutationPipeline`, participation → `ParticipationMutationPipeline`,
   provisioning → `ResourceProvisioningPipeline`, governance writes →
   `GovernanceMutationPipeline`. Never add a second path; strengthen the existing one.
3. **Governance is the single policy brain** for command access, visibility,
   capability, execution, cleanup policy, and subsystem availability. Command
   admission is already centralized (`bootstrap_access_cog` +
   `core.runtime.command_access`). Do not scatter policy back into cogs.
4. **Core/runtime owns lifecycle, tasks, locks, events, sessions, panels,
   anchors, state store, routing, interaction mechanics** — and should own them
   *generically*, without knowing feature/domain semantics (RC-7 is where this
   leaks).
5. **Utils are dependency leaves**; `utils/db/*` are persistence helpers, not
   hidden business services.
6. **AI runtime is provider-neutral; AI policy/quota/tools are service-owned and
   governance-aware.** The central `natural_language_stage` choke point + pure
   `ai_natural_language_policy.resolve()` + read-only scope-gated `ai_tools` are
   confirmed-healthy. Preserve them (RC-11).
7. **BTD6 facts are source-backed and service-owned**, with a faithfulness
   guard that refuses rather than improvises. Preserve the guard.
8. **No second system.** Do not introduce a parallel governance, runtime,
   helper, panel, or provenance system. The consolidation found the repo's
   biggest latent risk is *duplication*, not absence.

---

## Priority 0 — Verification blockers (must precede implementation)

Cheap, must be green before trusting the rest. This consolidation already
cleared most of P0; what remains needs a real DB / live environment.

| Item | Why it blocks | Status |
|---|---|---|
| Architecture + lint + targeted tests | Baseline trust | ✅ done this pass (0 arch errors; 1,450 tests green) |
| Full `pytest` + `mypy disbot/` (`check_quality.py --full`) | CI-parity proof before any code PR | ⬜ run in PR 0 |
| BTD6 provider parity (file/cloud/Postgres stats tree) | Gates RC-10 extraction decisions | ⬜ needs live DB/bucket |
| Smoke checklist pass (`docs/smoke-test-checklist.md`) | Runtime-relevant PRs require it | ⬜ before any runtime PR ships |

**Rule:** no implementation PR merges until `check_quality.py --full` is green
on its branch. The 1,450-test subset here is necessary, not sufficient.

---

## Priority 1 — Safety & correctness blockers

The short list of things that are *wrong*, not merely *unfinished*.

1. **RC-2 — Thread visibility cache bleed.** *Correctness.* `governance/cache.py`
   keys on `channel_id`, ignoring `ctx.thread_id` (`resolver.py:291`,
   `ISSUE-016`). Add `thread_id` to the key (or bypass cache for thread
   contexts) + a bleed regression test. Smallest, highest-value fix.
2. **RC-5 — Cleanup scope rejected late.** *Correctness/contract.* Split
   `_VALID_SCOPE_TYPES` into visibility-scopes (allow `thread`) and
   cleanup-scopes (reject `thread` *before* the DB). Removes a late
   constraint-violation failure mode.
3. **RC-15 — Counting silent save-swallow.** *Data integrity.* Replace the bare
   `except Exception:` swallow with an observable failure path (metric + log).
4. **RC-3 — Fail-open posture (decision-gated).** *Policy.* Decide and then
   enforce: fail-closed for owner-scoped/mutating panels and settings/setup/
   provisioning/admin surfaces; fail-open only for read-only public panels.
   Needs the §"maintainer decisions" call first.

These are independent of each other and can land as small, separately-tested PRs.

---

## Priority 2 — Architecture-boundary cleanup

Fix the *enforcement* and the *ownership leaks* — but only after P1, and
RC-1 before the others so the checker can police them.

1. **RC-1 — Architecture checker blind spot (do this first in P2).** Add a
   function-local-import **report** mode to `scripts/check_architecture.py`;
   seed an allowlist with rationale for the legitimate lazy imports. Start in
   report mode (the initial count will be high — the repo uses lazy imports to
   break cycles deliberately). Only after this can RC-4/RC-7 boundary moves be
   trusted not to reintroduce drift via a body import.
2. **RC-6 — Migration integrity.** Static invariant test: duplicate leading
   version, monotonic / explicit-gap, optional historical checksum; plus a
   fresh-DB bootstrap test that runs `create_tables()` + full migration chain.
3. **RC-7 — Runtime GC owns domain cleanup.** Introduce a feature-cleanup-provider
   registry; `session_gc` stays the scheduler/orchestrator, feature services
   register stale-state cleanup + own refund semantics. **Must honour ADR-002**
   (refund is the contract; do not regress it). This also retires part of the
   `arch-fix-11` cluster cleanly.
4. **RC-4 — Capability-native authority.** Replace the placeholder
   administrator-tier floor in `SettingsMutationPipeline` /
   `BindingMutationPipeline` with typed capability resolution
   (`SettingSpec.capability_required`). Decide the
   `SETTINGS_MUTATION_PRIMARY` / `RESOURCE_PROVISIONING_PRIMARY` flag semantics
   at the same time. **Gates settings/bindings UI expansion.**

---

## Priority 3 — Feature consistency & UX cleanup

Real, but non-blocking. Group by root cause; reconcile with existing roadmaps
(`docs/decisions/003-…` §3, `docs/loose-ends-audit-roadmap.md`) before treating
anything as net-new.

1. **RC-8 — Thin-cog migration.** Step A (docs only): the **Direct-DB Exception
   Ledger** — classify every remaining `utils.db` call in cogs as
   `accepted-read` / `service-migration-required` / `temporary`. Step B
   (mechanical): move embedded view/modal classes out of cogs into `views/**`.
   Step C: move business/DB mutations behind services. Stage per-feature, never
   "all cogs at once".
2. **RC-14 — Help/settings/slash parity.** `rpshelp`/`dm_help`/`rpssettings`
   drift; slash Help hardcodes `prefix="!"`. Reconcile with loose-ends
   Findings 2/3/5.
3. **RC-5 (naming half) + cleanup prefix normalisation.** Disambiguate "command
   cleanup policy" vs "prohibited-word cleanup"; replace `["?", "!"]` with shared
   prefix extraction.
4. **RC-13 — Doc/comment drift.** One small docs PR: correct the provisioning
   "zero callers" docstring, the identity-strictness and `guild_resources`
   comments (verify first), and stamp the stale audit baselines.
5. **Channel visibility large-guild pagination** (C#6) — product gap, not a bug.

---

## Priority 4 — BTD6 / AI expansion readiness

Gated behind a **decision**, not effort. Agent D was explicit: pause and verify.

1. **RC-10 — BTD6 provenance + ownership matrix.** Decisions doc that pins:
   which layer owns raw facts vs derived values vs source/freshness metadata vs
   prompt facts vs view-model facts vs AI-tool results vs response formatting;
   plus one `DataProvenance`/`SourceAttribution` object rendered everywhere.
   **Blocks further extraction (BX).**
2. **Provider parity verification** (P0 item, BTD6-specific) before any
   cloud/Postgres extraction migration.
3. **RC-11 — Preserve AI orchestration.** Before adding any AI feature, locally
   test the audit-row guarantee (one row per path after retry/floor), cooldown
   ordering, and grounding-tool whitelist. Expansion is gated on these passing.
4. **RC-12 — YouTube/media ownership** maintainer decision → then it can grow as
   a named `video_reference`/media subsystem, never folded into BTD6.

---

## Dependency graph

```
P0 verification (full pytest+mypy, provider parity)
   │
   ├── independent ──► RC-2 (thread cache)        [P1]
   ├── independent ──► RC-5 (cleanup scope)       [P1]
   ├── independent ──► RC-15 (counting swallow)   [P1]
   │
   └── RC-3 decision (fail-open posture) ─► RC-3 implementation [P1]
                                                   │
RC-1 (checker report mode) ──────────────────────┤ enables trustworthy
   │                                               │ boundary enforcement
   ├──► RC-7 (GC provider registry, honours ADR-002)  [P2]
   ├──► RC-4 (capability authority) ─► settings/bindings UI expansion [P2→gate]
   └──► RC-6 (migration integrity) ─► next DB-affecting PR            [P2]

RC-8A (Direct-DB ledger, docs) ─► RC-8B (move views) ─► RC-8C (service moves) ─► RC-14 (parity) [P3]

RC-10 (provenance decision) ─► provider parity ─► BTD6 extraction resumes [P4]
RC-11 (AI guard tests) ─► AI feature expansion                            [P4]
RC-12 (YouTube ownership decision) ─► media subsystem work                [P4]
```

Key edges: **RC-1 precedes RC-4/RC-6/RC-7** (police the moves). **RC-4 gates
settings UI.** **RC-10 gates BTD6 extraction.** **RC-3 needs a decision before
code.** RC-2/RC-5/RC-15 are leaf fixes with no upstream dependency.

---

## Systems that must NOT be touched yet

- **The AI central stage + policy resolver + read-only tool registry** (RC-11).
  Confirmed-healthy choke point; refactoring it risks the grounding guarantees.
  Add tests, don't restructure.
- **BTD6 data extraction** (RC-10). Pause until the provenance/ownership
  decision lands. More extracted fields now = more inconsistent provenance to
  retrofit later.
- **Runtime lifecycle / task supervision / runtime lock / health-readiness.**
  Confirmed strong with real tests. Keep stable while boundary cleanup happens
  around them.
- **Game-state restart behavior** (ADR-002). Do **not** build universal
  checkpointing; ADR-002's re-evaluation criteria are not met. Refund-on-restart
  is the contract.
- **Command admission** (`bootstrap_access_cog` + `command_access`). Centralized
  and working; do not add per-cog channel guards.
- **The `governance` GOV-2 unification** (visibility/execution/exposure). Agent B
  says hold until a concrete need appears. Do not split speculatively.

---

## Risks if implemented in the wrong order

- **Doing RC-4/RC-7 before RC-1:** boundary fixes that *look* clean but quietly
  reintroduce a function-local cross-layer import the checker can't see. Fix the
  checker's eyes first.
- **Expanding settings UI before RC-4:** bakes the placeholder administrator-tier
  semantics into more surfaces, multiplying the eventual capability migration.
- **Resuming BTD6 extraction before RC-10:** every new field inherits the
  non-uniform freshness model; the provenance retrofit cost scales with field count.
- **A broad "thin-cog" sweep before the Direct-DB ledger (RC-8A):** risks
  deleting useful compatibility behavior that wasn't classified. Ledger first.
- **Treating RC-9/A#5 as adoption work:** wasted effort — provisioning is
  already adopted; only the docstring + flag need attention.
- **Re-fixing items already closed in `repo-wide-audit-2026-05-29.md`'s
  remediation table:** duplicated work. Check that table first.
- **"Fixing" game recovery (C#4) as a bug:** violates ADR-002 and burns weeks
  on a rare-restart UX edge case.

---

## Rejected alternatives

- **Rip out the `arch-fix-11` lazy/tracked imports wholesale.** Rejected: they
  exist to break import cycles deliberately; the right move is report-mode
  visibility (RC-1) + incremental retirement (RC-7), not a big-bang.
- **Build a Redis/external store for sessions or game state.** Rejected by
  `docs/decisions/001-no-redis-backed-state.md`; single-process assumption holds.
- **New BTD6 read facade to "unify" the composition owners.** Rejected per
  Agent D §21: strengthen `btd6_view_model_service` as the UI read facade;
  do not invent a parallel facade.
- **Global fail-closed for all interactions (RC-3).** Rejected as a blanket:
  read-only public panels legitimately favor availability. The decision must be
  per-surface, not global.
- **One mega "fix everything" PR.** Rejected: the consolidation's whole point is
  root-cause grouping + small testable PRs with rollback notes.

---

## Ownership decisions needed from the maintainer

These are not code tasks — they are calls only the maintainer should make.
The next-session roadmap blocks the relevant PRs on them.

1. **RC-3 fail-open posture.** Confirm: fail-closed for owner-scoped/mutating
   panels + settings/setup/provisioning/admin; fail-open only for read-only
   public panels. (Recommended.)
2. **RC-4 flag semantics.** Should `SETTINGS_MUTATION_PRIMARY` /
   `RESOURCE_PROVISIONING_PRIMARY` become real kill switches, or be removed as
   dead declarations?
3. **RC-10 BTD6 provenance model.** Approve a single `DataProvenance` object +
   the owner-per-fact-type matrix before extraction resumes. Also: do extracted
   statics migrate into `btd6_data_blobs`, source-registry rows, or both?
4. **RC-12 YouTube/media ownership.** Confirm it is a shared `video_reference`/
   media subsystem (platform + external-API concerns), explicitly **not** BTD6.
5. **RC-8 cog-migration appetite.** How aggressive a thin-cog migration is wanted
   this quarter vs. just landing the Direct-DB ledger and stopping? (Affects PR 5+.)
