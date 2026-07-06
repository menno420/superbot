# CI redesign — follow-ups handoff (for the next agent)

> **Status:** `plan` — the turn-key backlog left after the CI-setup redesign arc (PRs #1737, #1739, and
> this one). Ranked, with exact steps. The design of record is
> [`ci-setup-redesign-2026-07-05.md`](ci-setup-redesign-2026-07-05.md); the live ground-truth map is
> [`../operations/ci-what-runs-where.md`](../operations/ci-what-runs-where.md); owner decisions live in
> router **Q-0238 (C)** + **Q-0239**.

## Where things stand (done)

- ✅ **CodeQL merge-race CLOSED** — the owner enabled the **`codeql-merge-protection` ruleset** on `main`
  (Require code scanning results · CodeQL · High-or-higher · Active, 2026-07-05). Auto-merge now waits for
  CodeQL and blocks on a High+ alert. Prereq shipped: `codeql.yml` → `cancel-in-progress: false` (#1739).
- ✅ **Merge gate tightened** (#1739) — `check_architecture --mode strict`, `check_tool_pins`,
  `check_workflow_concurrency` are now **hard steps in the required `code-quality` context**.
- ✅ **Dropped-`synchronize` watchdog de-self-silenced** (#1743) — `check_ci_coverage.py` now classifies
  by triggering event (only a `pull_request`/`push` run counts as covered; a completed `workflow_dispatch`
  re-kick that produced no PR-event run escalates to an owner-alert issue). Pure logic unit-tested.
- ✅ **CodeQL stuck-scan watchdog — SHIPPED alerting-only** (2026-07-06, item #2 below) —
  `check_codeql_coverage.py` bounds the residual the ruleset leaves open (a scan that *starts then
  errors/hangs*, keyed on `run_started_at` to tell a hung scan from a normal one), wired as an
  alerting-only leg on `ci-rerun-watchdog.yml`. It + `check_ci_coverage` now escalate through one shared
  idempotent **`scripts/lib/owner_alert.py`** helper (the #1743 Q-0089 idea; also fixed the workflow's
  missing `issues: write` so escalation works under the `GITHUB_TOKEN` fallback).
- ✅ **Ruff replaced black + isort — SHIPPED** (2026-07-06, item #3 below) — the python merge gate is now
  **3 tools** (ruff, mypy, pytest). `ruff format` owns formatting + `ruff check` (with `I`) owns import
  sorting; the two-thirds of the pin-drift surface (black + isort) is gone. Whole-tree reformat (~95 files),
  magic-trailing-comma parity verified (black agreed on all but the 14 known ruff-vs-black files).
- ✅ **Both AST guards — SHIPPED advisory** (item #5) — `check_audit_seam` (#1747, 2026-07-06) +
  `check_deferred_recovery` (#1748, 2026-07-06), both `continue-on-error` in `code-quality.yml`, each with
  an `architecture_rules/` allowlist + unit tests (incl. gate-bites + real-tree-clean). G4 hard-gate
  promotion stays owner-gated.
- ✅ **CI tail** (item #6, #1748, 2026-07-06) — `check_doc_freshness` deleted (**G7**); `check_session_slug_unique`
  wired advisory + self-verifying (the origin/main-in-CI check); **G8** resolved accept-advisory (owner-delegated).
  `settings.json` Stop-hook rewires (**G5**) + the branch-protection cutover (**G2/G3**, item #4) stay owner-gated.

## Ranked follow-ups

### 1. Live-verify the two things offline testing couldn't (do this FIRST — cheap, high-confidence)
- **CodeQL ruleset holds-then-releases:** open a trivial PR; confirm it does **not** auto-merge until the
  CodeQL check reports, then merges on green. (One real PR proves the owner's setting works end-to-end.)
- **`check_ci_coverage` escalation:** the `workflow_dispatch`-satisfies-required-check question is still
  unverified. To confirm: on a test PR, `gh workflow run code-quality.yml --ref <branch>` and check whether
  that dispatched run flips the PR's required `code-quality` status to satisfied. If **yes**, the watchdog's
  REKICK path alone recovers a dropped event (escalation rarely fires). If **no**, the ESCALATE→issue path
  is load-bearing and the *real* recovery is close+reopen with `ROUTINE_PAT` — wire that as the re-kick
  action ([FIX-7] in the design §C.3) and add a per-PR reopen cap ([FIX-8]).

### 2. CodeQL stuck-scan watchdog — ✅ SHIPPED alerting-only (2026-07-06); remaining = live-confirm → enable `--rerun`
The alerting half is built: `check_codeql_coverage.py` (`classify_codeql_head` → HEALTHY/RERUN/ESCALATE/WAIT)
+ the alerting-only leg on `ci-rerun-watchdog.yml` + the shared `lib.owner_alert` (item #2 of the "done" list
above). **What's left (pairs with the live-verify in item #1):** confirm the codeql `workflow_runs` shape
against a real errored/dropped scan — specifically (a) that a `pull_request` codeql run's `.path` is
`.github/workflows/codeql.yml` (adjust `CODEQL_WORKFLOW_PATH` if GitHub reports a managed path), and (b)
whether a re-run surfaces as a fresh `workflow_runs` row (so the retry-count logic sees it). Once confirmed,
flip the leg from alerting-only to `check_codeql_coverage.py --rerun` (re-dispatch RERUN heads, escalate only
after K failed retries). Design §C.2 `[FIX-1]`.

### 3. Ruff replaces black + isort — ✅ SHIPPED (2026-07-06). 5 python-gate tools → 3.
Done as one atomic PR. What it took, for the record (a couple of surfaces beyond the design's "five"):
1. `pyproject.toml`: enabled the `I` rule + `[tool.ruff.lint.isort]` (`known-first-party = ["disbot"]`);
   removed `[tool.black]` / `[tool.isort]`; **ignored `COM812`/`COM819`/`ISC001`** (the formatter now owns
   trailing commas + string layout — ruff warns if these lint rules stay on); per-file-ignored `I001` on
   `disbot/core/runtime/__init__.py` (ruff's combine garbles its per-line `# noqa: F401 — re-exported`).
2. `ruff format` the tree (~95 files) + `ruff check --fix --select I` (8 import-sort normalizations).
3. Magic-trailing-comma parity: black agreed on all but the 14 known ruff-vs-black files (expected).
4. Swapped black/isort → ruff in the five **plus** `scripts/claude_stop_check.py` (Stop hook),
   `scripts/check_routine_permission_surface.py`, `scripts/setup_dev_env.sh`, and the two guard tests
   (`test_check_quality_ci_parity`, `test_check_tool_pins`); `check_tool_pins._TOOLS` → `("ruff","mypy")`.

### 4. The aggregate `ci-gate` + reusable-workflow restructure — `[owner]` to cut over — DELIBERATELY NOT built speculatively (2026-07-06, PR #1748)
Build `ci.yml` (the `detect` + fan-in `ci-gate` job, design §C.1 — use the **proven shell git-diff detector**,
`fetch-depth:0`, the `needs.detect.result` assertion), `web-ci.yml` (reusable matrix over {dashboard,botsite}),
and `pr-freshness.yml` (fold `pr-auto-update` + `pr-conflict-guard`) **non-required, alongside** the current
workflows. Observe green/red parity across a band of PRs (code-only + docs-only). **Then** the owner ratifies
the atomic required-context swap (Q-0239 **G2**) and the six workflow deletions (**G3**). Note the atomic-swap
deadlock warning in the design §E (B2) — the swap must be one change.

> **Judgment call (owner-delegated "finish everything you can" session, PR #1748): staged, NOT built.**
> Reasons: (a) it **cannot reach done without the owner** — the whole payoff is the branch-protection
> cutover making `ci-gate` the required context (G2) + the 6 workflow deletions (G3), a GitHub
> ruleset/admin change that can't be done from code; (b) "build alongside" would run a duplicate CI
> pipeline on **every** PR open-endedly (double Actions cost) while delivering **zero** value until that
> cutover; (c) it touches the single most load-bearing part of the workflow (the merge gate) — refactoring
> `code-quality.yml` → the reusable `_python-quality.yml` risks the *current* required context. That is the
> "cross-cutting / affects how PRs merge" class the autonomy boundary reserves for the owner. **The design
> is frozen and copy-paste-ready in §C.1** — this is a build-ready artifact awaiting the owner's cutover
> decision, not unfinished analysis. When the owner wants it: build the three workflows non-required in one
> PR, observe a parity band, then do the atomic G2 swap + G3 deletions.

### 5. The two AST guards — `[offline]`, calibrated specs ready
Build from the calibrated specs in the idea docs (naive heuristics are too FP-prone — do NOT ship those):
- ✅ **`check_audit_seam.py` — SHIPPED advisory (2026-07-06).** Repo-wide per-function reachability: a
  function with a **direct write signal** (raw SQL outside `utils/db` · Discord state mutation on a
  non-message receiver · an **auditable-domain** `utils.db` write) whose success path never reaches
  `emit_audit_action` (transitively). Wired `continue-on-error` in `code-quality.yml` (deps block,
  code-gated); `architecture_rules/audit_seam_exceptions.yml` allowlist; 19 unit tests incl. the
  Q-0120 gate-bites meta-test + a real-tree-clean ground-truth test. **Two calibration refinements the
  build required, for the record** (naive per-function was still too noisy — the calibration was right):
  (1) **import-qualified db-call detection** — `db.set_x()` where `db` is a `utils.db` alias, NOT a bare
  name match, so `self.add_item` (the `discord.ui.View` method colliding with the `inventory` helper) is
  never a false db write; (2) **auditable-domain scoping via DIRECT audit co-occurrence** — a db helper
  is "auditable-class" only if some function writes it *and* emits in the same body (the audited-wrapper
  shape), which is collision-proof (the name-merged call graph marks generic verbs like `credit`/`award`
  audit-reachable off one namesake and would otherwise mark whole game domains auditable → the ~42% FP
  class). Result: the db-write dimension fires **only** on an unaudited write to a domain that IS audited
  elsewhere (bug #6), never on economy/games/sessions writes. Baseline: 6 findings, all triaged legit and
  allowlisted with source-verified reasons (automated/self-service role application · mechanical overwrite
  steps of audited operations). Would-have-caught bug #5 + bug #6. **Owner-gate for G4 promotion:** confirm
  it stays quiet across a band; the automation role-apply allowlist entry is the one spot to revisit if you
  want automation role-changes surfaced in the audit log.
- ✅ **`check_deferred_recovery.py` — SHIPPED advisory (2026-07-06, PR #1748).** Keys on the **spawn-target**
  (`tasks.spawn`/`create_task`/`ensure_future`), resolves the callee, flags a spawn-target whose body does
  `asyncio.sleep` **then** a Discord state mutation (raw attr OR a name-based lifecycle-routed verb like
  `_lift_lockdown`/`slowmode`) in a module with **no persisted-deadline write + no boot reconcile** — the
  restart-recovery-gap class the Stage-2 walk found twice. Calibration held: raw `asyncio.sleep` (23 files)
  narrowed to **1** finding via the spawn + persistent-Discord-state-mutation filter (infra loops / game
  re-renders / inline non-spawned sleeps all correctly excluded). Wired `continue-on-error` in
  `code-quality.yml`; `architecture_rules/deferred_recovery_exceptions.yml` allowlist; 10 unit tests incl.
  the gate-bites meta-test + real-tree-clean ground-truth. Baseline: 1 finding
  (`security_service._hold_then_lift`) triaged + allowlisted as intentionally process-local (ADR-002,
  fails open on restart). **⚑ Owner note:** the raid-lockdown *slowmode* it applies is a real Discord-side
  change that does NOT auto-reset on restart (a mild residual gap recorded in the allowlist reason) — revisit
  if you want it restart-safe.
Both guards wired advisory (`continue-on-error`); promote after a clean band (Q-0239 **G4**).

### 6. Smaller / owner-gated tail
- 🟡 **`check_session_slug_unique` — WIRED ADVISORY (2026-07-06, PR #1748).** The gate-blocker concern was
  a false-block risk, but the guard **fails open by design** (a `git cat-file` failure → no finding → never
  blocks), so it's wired `continue-on-error` PR-only — which *also performs* the CI-context verification the
  gate needs: this PR's CI run confirms whether `origin/main` resolves in the `fetch-depth:0` checkout.
  **Promotion to a hard gate is now a one-line follow-up** once a PR shows it resolving + producing sane
  output (flip `continue-on-error` off / drop the advisory framing).
- **App-CI legs gating** (dashboard/botsite/design-system `mypy`+`pytest`) — folds into #4's `web-ci.yml`.
- **`settings.json` Stop-hook rewires** (Q-0239 **G5**, owner-gated — NOT taken): a `check_consistency` Stop
  mirror; an optional changed-module fast-pytest subset. Executable config that affects every session → stays
  for explicit owner sign-off (autonomy boundary Q-0106).
- ✅ **Deleted `check_doc_freshness`** (dormant/unwired, Q-0239 **G7**, 2026-07-06); **kept `check_plan_staleness`**.
- ✅ **#794-class content-completeness race** (Q-0239 **G8**): **RESOLVED accept-advisory** (2026-07-06,
  owner-delegated) — stays advisory, no presence gate, revisit if #794 recurs. Router Q-0239 G8 annotated.

## The "does the gate actually block?" meta-test (worth doing alongside any new gate)
Every gate added should have a known-bad fixture proving it *fails* when it should, not just passes when clean
(the Q-0120 false-green class). See the session idea in `.sessions/2026-07-05-ci-phase-a-gating.md`.
