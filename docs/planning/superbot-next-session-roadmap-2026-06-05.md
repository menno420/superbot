# SuperBot — Next-Session Roadmap

> **`historical` — 2026-06-05; PR sequence superseded.** For *what is true now*
> and the next candidates, start at **`docs/current-state.md`**.

> **Status:** `historical` — planning artifact. Companion to
> `superbot-audit-consolidation-2026-06-05.md` (verified findings, IDs RC-n)
> and `superbot-architecture-priority-map-2026-06-05.md` (priority + dependency
> graph). This doc converts the consolidated findings into an ordered,
> bounded set of sessions/PRs. **It plans; it does not implement.**
>
> **Date:** 2026-06-05
>
> **Discipline applied:** verify first → safety/correctness before UX → central
> ownership before feature surfaces → fix the arch-checker blind spot before
> relying on it → no BTD6 extraction until provenance is decided → no AI
> expansion until guard tests pass → group cog work by root cause → small,
> testable PRs with explicit rollback + stop conditions.

---

## Recommended next sessions

| # | Session | Root causes | Type | Gate |
|---|---|---|---|---|
| S0 | Verification + this consolidation | — | docs + checks | **this PR** |
| S1 | Governance correctness fixes | RC-2, RC-5, RC-15 | code | none (ready) |
| S2 | Interaction/panel safety policy | RC-3 | decision → code | maintainer decision |
| S3 | Architecture enforcement + migration integrity | RC-1, RC-6 | code (tooling/tests) | after S1 lands |
| S4 | Runtime GC ownership + capability authority | RC-7 (✅ #516), RC-4 | code | after S3 (checker) + RC-4 flag decision |
| S5 | General-feature cleanup | RC-8, RC-14, RC-13 | docs→code | after S1 |
| S6 | BTD6/AI readiness | RC-10, RC-11, RC-12 | decision → docs/tests | maintainer decision; **pause extraction** |

Sessions are independent unless a gate says otherwise. S1 and S5A (the
docs-only Direct-DB ledger) can run in parallel. Per `.claude/CLAUDE.md`,
plans span **2–3 PRs max per session** — the groups below respect that.

---

## Suggested PR sequence

```
PR 0  (this)   docs(planning): consolidation + priority map + roadmap + SoT index   ✅ #512
PR 1  S1       fix(governance): thread cache identity + cleanup scope split + counting swallow   ✅ #513
PR 2  S2       feat(runtime): interaction/persistent-view fail-open policy   [ADR-004 Accepted → ready]
PR 3  S3a      tooling(arch): function-local import report mode + allowlist   ✅ #515
PR 4  S3b      test(db): migration integrity invariants + fresh-DB bootstrap   [static invariants ✅; runner guard + bootstrap remain]
PR 5  S4a      refactor(runtime): feature-cleanup-provider registry (session_gc)  [honours ADR-002]   ✅ #516
PR 6  S4b      feat(governance): capability-native settings/bindings authority   [gates settings UI; ADR-005 Proposed]
PR 7  S5a      docs: Direct-DB Exception Ledger + comment/baseline drift fixes
PR 8  S5b      refactor(cogs): move embedded views/modals out of cogs (mechanical)
PR 9  S6a      docs(decision): BTD6 provenance + ownership matrix + YouTube ownership
PR 10 S6b      test(btd6/ai): provider parity + AI guard guarantees (pre-expansion)
```

PRs 1, 3, 4, 7, 9 carry the lowest risk and can be front-loaded. PRs 2, 6, 9
are decision-gated.

---

## PR 0 — Verification-only (this PR)

**Scope:** docs only — the four planning docs. Plus the verification already
run (architecture, lint, 1,450 tests). **Remaining verification to record/run
before any code PR:**

```bash
python3.10 scripts/check_quality.py --full      # full pytest + mypy disbot/
# BTD6 provider parity (needs live DB/bucket) — record result, don't fix env
```

**Deliverable:** this docs set merged; CI green.
**Stop condition:** if `--full` reveals a failing test or mypy error on
`main`/HEAD, **stop** and report — that invalidates the green baseline this
consolidation assumes.

---

## PR 1 — Highest-risk fix group (S1: RC-2 + RC-5 + RC-15)

**Why grouped:** three small, independent, source-confirmed fixes; all in the
governance/feature-correctness lane; each isolated by its own test.

**Scope:**
- **RC-2** — add `thread_id` to `governance/cache.py` `_cache_key` (or bypass
  cache for thread contexts). Touch `resolver.py:291` callsite. Remove/resolve
  `# ISSUE-016`.
- **RC-5** — split `governance/writes.py` `_VALID_SCOPE_TYPES` into
  visibility-scopes (incl. `thread`) and cleanup-scopes (excl. `thread`); reject
  thread cleanup writes in the service before the DB.
- **RC-15** — make `counting_cog.py:_save_guild` failures observable
  (metric/log), not a silent `except Exception:`.

**Required tests:**
- Thread cache isolation: same guild/channel/tier, different `thread_id`, with a
  thread-scoped override → no cross-thread/parent bleed.
- Cleanup scope: `set_cleanup_policy(scope_type="thread")` raises a clean
  `GovernanceError` *before* any DB call.
- Counting: a forced persistence failure increments a metric / emits a log
  (not swallowed).
- Regression: `pytest tests/unit/governance tests/unit/runtime` stay green.

**Rollback:** each fix is independent; revert the offending commit. The thread
cache change is the only behavioral one — if a visibility regression appears,
reverting restores the (buggy but known) channel-keyed behavior.

**Out of scope:** the visibility/execution/exposure unification (GOV-2 — hold);
any panel/fail-open change (that's PR 2).

---

## PR 2 — Interaction/panel safety policy (S2: RC-3) — decision-gated

**Blocked on maintainer decision** (fail-open posture; see priority-map
§"maintainer decisions" #1).

**Scope (after decision):**
- `persistent_views.py interaction_check`: fail-closed for owner-scoped panels
  on missing/`None` anchor; explicit opt-in for public persistent panels.
- Document/decide interaction-router behavior when governance resolution throws
  (fail-closed for mutating surfaces; fail-open only for read-only public).
- Verify (or add) panel-render serialisation around `get_or_render_panel`'s
  delete→send→upsert.

**Required tests:** missing-anchor → denied for owner panels, allowed for
declared public panels; resolver-failure path matches the chosen posture;
panel render under concurrent invocation does not duplicate.

**Rollback:** feature-flag or revert; the change is policy-tightening, so
rollback returns to today's permissive behavior.

**Out of scope:** rewriting the panel/session model (it is two legitimate
patterns per Agent B UI-3 — do not add a third).

---

## PR 3 — Architecture enforcement (S3a: RC-1)

**Scope:** add a function-local-import **report** mode to
`scripts/check_architecture.py` (`_ImportVisitor` currently early-returns when
`_fn_depth > 0`, `:120-128`). Emit lazy cross-layer imports as warnings; seed
`architecture_rules/` with rationale entries for the legitimate cycle-breakers.
**Do not hard-fail** on first run — the count will be high by design.

**Required tests:** checker unit test proving a planted function-local
`cogs → services`-style cross-layer import is now *reported*; existing
`check_architecture` exit stays 0 (report ≠ error initially).

**Rollback:** pure tooling; revert leaves today's behavior.
**Out of scope:** acting on the new report (that's RC-7/RC-4 work).

---

## PR 4 — Migration integrity (S3b: RC-6)

**Scope:** static invariant test over `disbot/migrations/`: no duplicate leading
version, monotonic / explicitly-allowed gaps, optional historical checksum; plus
a fresh-DB bootstrap test (`create_tables()` + full chain applies cleanly).

**Required tests:** the invariant test itself (red on a planted duplicate);
fresh-DB bootstrap passes.

**Rollback:** test-only; revert is free.
**Out of scope:** editing historical migrations (forbidden — forward-only).

---

## PR 5 — Runtime GC ownership (S4a: RC-7)

> **✅ SHIPPED in #516 (2026-06-05).** Retained for archaeology — do **not**
> re-implement. `session_gc` is now a scheduler that calls
> `cleanup_registry.run_all()`; `services.game_state_cleanup` owns the ADR-002
> refund sweep. See `docs/ownership.md` §"Feature stale-state cleanup (RC-7)".

**Scope:** introduce a feature-cleanup-provider registry; `session_gc` becomes
scheduler/orchestrator; feature services register stale-state cleanup and own
refund semantics. Retires part of the `arch-fix-11` cluster.

**Hard constraint:** **honour ADR-002** — refund-on-restart is the contract; the
GC refund path must remain (or move to a feature provider) without changing
user-visible refund behavior.

**Required tests:** GC still refunds staked `bet` rows (via the provider);
`session_gc` no longer imports `economy_service`/`game_state_service` at module
level (verify against the new checker from PR 3).

**Rollback:** revert to the direct `session_gc` import (today's tracked-debt
state). Keep the change behind a small adapter so rollback is a one-commit revert.
**Gate:** after PR 3 (so the checker can confirm the boundary actually improved).

---

## PR 6 — Capability-native authority (S4b: RC-4) — gates settings UI

**Blocked on maintainer flag decision** (priority-map #2).

**Scope:** replace placeholder administrator-tier floor in
`SettingsMutationPipeline` / `BindingMutationPipeline` with typed capability
resolution (`SettingSpec.capability_required`); decide `*_PRIMARY` flag fate.

**Required tests:** mutation authorized/denied by declared capability, not broad
tier; `system`/`backfill` bypass preserved; audit + cache-invalidation still fire.

**Rollback:** revert restores the tier floor (functional, just coarse).
**Out of scope:** broadening any settings surface — that is the *follow-on* this
PR unblocks, not part of it.

---

## PR 7 — Direct-DB ledger + doc drift (S5a: RC-8A + RC-13) — docs only

**Scope:** the **Direct-DB Exception Ledger** (every remaining cog `utils.db`
call classified `accepted-read` / `service-migration-required` / `temporary`,
with owner + target PR). Plus drift fixes: correct
`resource_provisioning.py:59` "zero callers" docstring; verify+fix the identity
strictness / `guild_resources` comments; stamp stale audit baselines.

**Required tests:** none (docs); optionally a lint helper that flags new
unclassified cog DB calls.
**Rollback:** free (docs).
**Out of scope:** moving any code (that's PR 8+).

---

## PR 8+ — Feature cleanup (S5b: RC-8B/C + RC-14)

**Scope (mechanical first):** move embedded view/modal classes out of cogs into
`views/**` (`RoleHubPanelView`, `_AdminPanelView`/`_LogLevelModal`, chain/cleanup
modals, deathmatch views, utility/inventory views) with import/back-compat tests.
Then per-feature service moves grouped by risk; then help/slash parity (RC-14).

**Reconcile first:** check `docs/decisions/003-…md` §3 (tournament
platformization, command-annotation sweep, config-arbitration audit are already
deferred there) and `docs/loose-ends-audit-roadmap.md` Findings 2/3/5 — do not
re-plan items those own.

**Required tests:** import/back-compat after each view move; service-move tests
per feature; help-route actionability + slash/prefix parity for touched hubs.
**Rollback:** per-feature commits; revert the offending feature only.
**Out of scope:** "all cogs at once" — forbidden by the priority map.

---

## PR 9 — BTD6/AI decisions (S6a: RC-10 + RC-12) — decision-gated, docs only

**Blocked on maintainer decision** (provenance model + YouTube ownership).

**Scope:** a Decisions doc pinning the BTD6 owner-per-fact-type matrix + one
`DataProvenance`/`SourceAttribution` object; storage decision
(`btd6_data_blobs` vs source-registry rows vs both); YouTube as a shared
`video_reference`/media subsystem. **Extraction stays paused until this lands.**

**Required tests:** none (docs).
**Out of scope:** any new BTD6 data extraction.

---

## PR 10 — BTD6/AI verification (S6b: RC-11 + provider parity)

**Scope:** execute BTD6 file/cloud/Postgres provider parity for stats/paragon
consumers; lock in AI guard guarantees (one audit row per path after retry/floor,
cooldown ordering, grounding-tool whitelist) as tests **before** any AI feature
expansion.

**Required tests:**
```bash
python3.10 -m pytest tests/unit/runtime/ai \
  tests/unit/services/test_btd6_context_grounding.py \
  tests/unit/services/test_ai_tools.py \
  tests/unit/services/test_paragon_service.py \
  tests/unit/views/btd6/test_paragon_view.py \
  tests/unit/services/test_youtube_context_service.py \
  tests/unit/runtime/test_no_duplicate_passive_listeners.py \
  tests/unit/invariants/test_cog_size.py
```
plus provider-parity execution against a live backend.
**Rollback:** test/verification-only.
**Out of scope:** adding AI features or extracted BTD6 data.

---

## Which agent / model handles each session

| Session | Recommended handler | Rationale |
|---|---|---|
| S1 (RC-2/5/15) | **Claude** (governance-aware) | correctness-critical; needs careful regression tests |
| S2 (RC-3) | Maintainer decision → **Claude** | policy call then tight, well-tested change |
| S3 (RC-1/6) | **Claude or Codex** | tooling/test work; self-contained |
| S4 (RC-7/4) | **Claude** | touches mutation seams + runtime ownership; high-context |
| S5 (RC-8/14/13) | **Claude or Codex**, per-feature | mechanical + repetitive; parallelisable |
| S6 (RC-10/11/12) | **BTD6/AI-focused session** (the `serene-sagan` lineage) | deepest domain context for provenance |

---

## What each session must read first

**Always:** `.claude/CLAUDE.md` → `docs/AGENT_ORIENTATION.md` → this roadmap →
the consolidation doc (for the RC-n evidence) → the priority map (for ordering).

| Session | Then read |
|---|---|
| S1 | `docs/ownership.md`; `governance/{cache,resolver,writes}.py`; `migrations/009`; ADR none |
| S2 | `docs/runtime_contracts.md` §3/§6; `persistent_views.py`, `interaction_router.py`, `panel_manager.py`; Agent B UI-1/2/3 |
| S3 | `scripts/check_architecture.py`; `architecture_rules/layers.yaml`; `utils/db/migrations.py` |
| S4 | `docs/ownership.md`; ADR-002; `session_gc.py`; `settings_mutation.py`/`binding_mutation.py`; `platform-consistency-ledger.md` §1 |
| S5 | `docs/helper-policy.md`; `docs/decisions/003-…md` §3; `docs/loose-ends-audit-roadmap.md`; `docs/ui-view-adoption-audit.md` |
| S6 | `docs/ai-config-ownership.md`; `docs/btd6-data-backends.md`/`btd6-data-pipeline.md`; `docs/btd6-derived-value-groundedness-finding.md`; Agent D audit §6/§12/§13 |

---

## Out-of-scope warnings (every session)

- Do **not** refactor the AI central stage / policy resolver / tool registry
  (RC-11 — preserve).
- Do **not** resume BTD6 data extraction before PR 9 lands (RC-10).
- Do **not** build universal game-state checkpointing (ADR-002).
- Do **not** add a second governance / runtime / panel / provenance / helper
  system. Strengthen the existing seam.
- Do **not** touch runtime lifecycle / tasks / runtime-lock except behind their
  contracts; they are confirmed strong.
- Do **not** edit historical migrations (forward-only).
- Do **not** treat provisioning as "unadopted" (RC-9 — it has real callers).
- Do **not** re-fix items already closed in
  `docs/audits/repo-wide-audit-2026-05-29.md`'s remediation table.

---

## Stop conditions (every session)

Stop and report (do not push) if:

- the working tree is dirty before the session starts, or the branch is not
  based on current `main`;
- `check_quality.py --full` is red on the **starting** commit (the baseline is
  broken — escalate, don't build on it);
- a planned fix would require touching a "must-not-touch" system above;
- a decision-gated PR (2, 6, 9) is reached without the maintainer decision;
- source verification contradicts this plan badly enough that following it
  would mislead (re-open the consolidation doc and amend).

---

## Required tests per session (summary)

| Session | Minimum green before push |
|---|---|
| S1 | `pytest tests/unit/governance tests/unit/runtime` + new cache/scope/counting tests |
| S2 | runtime interaction/persistent-view tests + new fail-open tests |
| S3 | `pytest tests/unit/db` + checker unit test; `check_architecture` exit 0 |
| S4 | governance + runtime suites + new provider-registry/capability tests; ADR-002 refund test green |
| S5 | import/back-compat + per-feature service tests + help/parity tests |
| S6 | the BTD6/AI block in PR 10 above + provider parity |
| **all** | `python3.10 scripts/check_quality.py --full` green (CI mirror) |

---

## Rollback notes (global)

- Every PR is single-purpose and individually revertible; the sequence is
  designed so no PR hard-depends on an *unmerged* later PR.
- Behavioral changes (RC-2 cache, RC-3 fail-open, RC-7 GC, RC-4 authority)
  should land behind a revert-friendly seam (small adapter / flag) so a
  regression is a one-commit revert, not a forensic untangle.
- Decision-gated PRs (2, 6, 9) must not merge ahead of their decision; reverting
  one should never strand a dependent merged PR (hence ordering).
- Docs/tooling/test PRs (0, 3, 4, 7, 9) are free to revert.

---

## Addendum (2026-06-05): Ideas Lab + committed UX follow-ups

PR 1 (S1 / RC-2 + RC-5 + RC-15) merged as **#513**. A brainstorm backlog now
lives in **`superbot-ideas-lab-2026-06-05.md`** (tiered candidate work; §2 and
§6 there are binding). It does not change the RC-driven PR sequence above.

**Committed post-PR-1 UX follow-ups** (promoted from the Ideas Lab; each is
read-only / observability-only, rides an existing read seam, gate cleared):

- **IL-1** — thread/channel-aware access explainer (validates RC-2; built on
  `governance.snapshot` / `SubsystemEffectiveState`).
- **IL-2** — cleanup policy dry-run (pairs with RC-5; reuses the
  `_VALID_CLEANUP_SCOPE_TYPES` split + the setup-wizard preflight render path).
- **IL-3** — counting persistence-health line (surfaces the RC-15
  `task_outcome_total` + ERROR signal via `!platform`; **not** a new monitor).

Everything else from the scan stays a gated suggestion in the Ideas Lab; the
decision/test gates (RC-3, RC-4, RC-10, PR 10 guard tests, ADRs) still hold.

### Shipped progress (as of 2026-06-05)

| Session / PR | RC(s) | PR | State |
|---|---|---|---|
| S1 — governance correctness | RC-2, RC-5, RC-15 | #513 | ✅ merged |
| (planning) Ideas Lab backlog | — | #514 | ✅ merged |
| S3a — arch checker report mode + arch-warning summary (§4.4) | RC-1 | #515 | ✅ merged |
| S4a — feature-cleanup-provider registry | RC-7 | #516 | ✅ merged |

**RC-6 (migration integrity, S3b):** already satisfied — its static invariants
(no-gaps, no-duplicates, filename format, non-empty, runner-dir) live and pass in
`tests/unit/db/test_migrations_structure.py`. Remaining: the *optional* historical
checksum guard (permanent per-migration friction — maintainer's call) and a live
fresh-DB bootstrap (needs Postgres in CI). Not re-implemented.

**Next, still gated:** S4b / **RC-4** (capability-native authority) needs the
maintainer flag-semantics decision (drafted as **ADR-005 Proposed**); S6a /
**RC-10 + RC-12** drafted as **ADR-006 / ADR-007 Proposed**. **RC-3** (fail-open
posture) is **no longer gated** — ratified per-surface in **ADR-004 (Accepted)**;
its implementation is in the revised wave below. The committed UX trio (IL-1/2/3)
is ready to build.

---

## Addendum 2 (2026-06-05, post-#516): revised remaining wave

After #515 (RC-1) and #516 (RC-7) shipped, the remaining roadmap was re-cut into
one larger session. Full plan with per-PR scope / tests / rollback / stop
conditions lives in `.claude/plans/use-this-revised-prompt-dazzling-cloud.md`.
**RC-7 is complete — the "PR 5 — Runtime GC ownership" section above is
historical; do not re-implement it.** New base = `main` @ `312bcfd`.

| Wave PR | Title | Maps to | State |
|---|---|---|---|
| PR1 | Decision pinning + post-#516 doc reconciliation (ADR-004 Accepted; 005/006/007 Proposed) | S2 decision + this refresh | **shipped (#517)** |
| PR2 | Operator explainers & previews (IL-1/2/3, read-only) | Ideas-Lab trio | **shipped (#517)** |
| PR3 | Migration runner guard (RC-6 remainder) | S3b remainder | **shipped (#517)** |
| PR4 | Interaction/panel safety impl (RC-3) — depends on ADR-004 | S2 impl | **shipped (#517)** |
| PR5 | Boundary & consistency foundation (RC-8A ledger + RC-13 + RC-14) | S5a (PR 7) | **shipped (#517)** |
| PR6 (optional) | AI choke-point guard tests (RC-11, tests only) | PR 10 (pulled forward, tests only) | **shipped (#517)** — coverage map only; cooldown-ordering guard added this session (Addendum 3) |

Hard dependency was PR1 → PR4 (both shipped). RC-4 code, the RC-8 view-move sweep
(PR 8), and RC-10 / RC-12 ratification were deferred/gated here — **now addressed in
Addendum 3 below.**

---

## Addendum 3 (2026-06-05, post-#517): decisions ratified + ADR-005 implemented

Wave PR1–PR6 above all landed in **#517** (verified against the commit log). This
session:

- **Ratified ADR-005 (A1 + F1), ADR-006 (Hybrid storage), ADR-007 (M1)** — all now
  `Accepted`. ADR-005's F1 was *amended*: kill-switches wire at the mutation-pipeline
  entry points, not the read-only `config_arbitration.py`.
- **Implemented ADR-005** (RC-4 closeout): a governance capability resolver +
  two operator kill-switches across the settings / binding / provisioning pipelines.
- **Pinned the RC-11 cooldown-ordering guard** — the one gap PR6's coverage map left
  open. RC-11's pre-AI-expansion guard set is now complete. *AI feature/tool
  expansion itself remains gated (Ideas-Lab §6).*
- Shipped three no-gate Ideas-Lab §4.1 UX items (Help discovery labels, RPS-matchup
  + Chain-clear-limit panel buttons, panel-class drift test).

Still deferred/gated: BTD6 provenance **schema/extraction** (RC-10, paused until a
follow-on docs/schema PR), ADR-007 media-subsystem **registration** + `ownership.md`
row (follow-on), capability-native **settings UI** (follow-on after RC-4 code), and
the broad RC-8 view-move sweep (PR 8).

---

## Addendum 4 (post-#518): documentation + next-session candidates

PR #518 merged ADR-005 (A1 + F1) and the safe Ideas-Lab §4.1 UX. A follow-up docs PR
added [`docs/capability-authority.md`](../capability-authority.md) (the binding
reference for the implemented authority system) and reconciled the now-stale
references (resource-provisioning overview, `ownership.md`, this roadmap, Ideas-Lab
§4.5/§6).

**Candidate next sessions** — each independently shippable; pick one per session:

| Candidate | What | Gate / readiness | First read |
|---|---|---|---|
| **A. Capability-native settings UI** | Ideas-Lab §4.5 (settings capability preview, "why can't I edit this?", provenance cards, capability audit mini-report) | **Unblocked** — RC-4 shipped; build read-only over the authority result first | `docs/capability-authority.md`, Ideas-Lab §4.5 |
| **B. Per-capability tier matrix** | Replace the v1 single administrator floor with a declared capability → required-tier map | Design decision; extend `_DEFAULT_REQUIRED_TIER`. No security regression (floors only relax with an explicit declaration); add per-tier tests | `docs/capability-authority.md` §5, ADR-005 re-eval criteria |
| **C. Broaden the panel-authority guard** | Audit other mutating panels reachable without an admin-gated entry (Help `build_help_menu_view`, hub routes) and apply `interaction_is_admin` | Small, mechanical, per-panel; add a non-admin-blocked test each | `docs/capability-authority.md` §4 |
| **D. ADR-006 BTD6 provenance** | Implement the single `DataProvenance` object + owner matrix; resume extraction against it | **Gated** — ADR-006 Accepted but extraction stays paused until the schema PR lands | ADR-006, `docs/btd6-data-backends.md` |
| **E. ADR-007 media subsystem** | Add the `docs/ownership.md` media-subsystem row + register `youtube_context_service` / `video_reference_cache_service` under it | **Follow-on** of ADR-007 (Accepted); ownership-doc PR | ADR-007, `docs/ownership.md` |
| **F. RC-8 staged cleanup** | A *tiny* mechanical view/cog slice (Direct-DB ledger → view moves → service moves), per-feature | Staged; never all-at-once; don't touch capability/BTD6/media in the same slice | priority-map §RC-8, `docs/direct-db-exception-ledger.md` |

**Suggested order:** A or C first (lowest risk, immediate operator value, both build
directly on what #518 shipped), then B, then the gated D/E when you want to open
those lanes. F can ride alongside any of them as a small slice.

Out of scope unchanged: no second governance / provenance / media system; no AI
write/action tools (Ideas-Lab §6); no broad all-cogs thin-cog sweep.
