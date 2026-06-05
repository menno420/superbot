# SuperBot — Next-Session Roadmap

> **Status:** planning artifact. Companion to
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
| S4 | Runtime GC ownership + capability authority | RC-7, RC-4 | code | after S3 (checker) + RC-4 flag decision |
| S5 | General-feature cleanup | RC-8, RC-14, RC-13 | docs→code | after S1 |
| S6 | BTD6/AI readiness | RC-10, RC-11, RC-12 | decision → docs/tests | maintainer decision; **pause extraction** |

Sessions are independent unless a gate says otherwise. S1 and S5A (the
docs-only Direct-DB ledger) can run in parallel. Per `.claude/CLAUDE.md`,
plans span **2–3 PRs max per session** — the groups below respect that.

---

## Suggested PR sequence

```
PR 0  (this)   docs(planning): consolidation + priority map + roadmap + SoT index
PR 1  S1       fix(governance): thread cache identity + cleanup scope split + counting swallow
PR 2  S2       feat(runtime): interaction/persistent-view fail-open policy   [needs decision]
PR 3  S3a      tooling(arch): function-local import report mode + allowlist
PR 4  S3b      test(db): migration integrity invariants + fresh-DB bootstrap
PR 5  S4a      refactor(runtime): feature-cleanup-provider registry (session_gc)  [honours ADR-002]
PR 6  S4b      feat(governance): capability-native settings/bindings authority   [gates settings UI]
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
