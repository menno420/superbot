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
- ✅ **Dropped-`synchronize` watchdog de-self-silenced** (this PR) — `check_ci_coverage.py` now classifies
  by triggering event (only a `pull_request`/`push` run counts as covered; a completed `workflow_dispatch`
  re-kick that produced no PR-event run escalates to an owner-alert issue). Pure logic unit-tested.

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

### 2. CodeQL stuck-scan watchdog (bounds the one residual the ruleset leaves open) — `[offline]` build, needs live confirm
The ruleset holds on *in-progress* and blocks on *unconfigured*, but does **not** bound a CodeQL run that
*starts then errors/hangs* — that can hold a PR indefinitely. Add a leg to `ci-rerun-watchdog.yml`: on the
`*/12` cadence, find head SHAs with a code-scanning analysis pending/errored past a grace window → re-run
CodeQL → after K retries, open an owner-alert issue (reuse `check_ci_coverage.open_alert_issue`'s idempotent
pattern). Design §C.2 `[FIX-1]`.

### 3. Ruff replaces black + isort (the biggest "fewer checks" win) — `[offline]`, its own focused PR
5 gate tools → 3. Turn-key (all in one atomic commit, per design §C.4):
1. `ruff format .` over the tree (Black-compatible).
2. Port `[tool.ruff.lint.isort]` into `pyproject.toml`/`ruff.toml` (`known-first-party = ["disbot", ...]`,
   black-profile equivalents) and enable the `I` rule — or you get a *second* import-reorder churn diff.
3. Verify magic-trailing-comma parity vs `black 26.5.1` on the reformat.
4. Swap black/isort → ruff in **all five**: `code-quality.yml`, `requirements-dev.txt`,
   `.pre-commit-config.yaml`, `scripts/check_quality.py`, **and `scripts/claude_post_edit.py`** (the
   PostToolUse auto-fixer) — same commit, or local hooks reformat with black and fight CI every edit.
5. `check_tool_pins.py` tracks black/isort/ruff — update its `_TOOLS`/pins accordingly.

### 4. The aggregate `ci-gate` + reusable-workflow restructure — `[offline]` build alongside, `[owner]` to cut over
Build `ci.yml` (the `detect` + fan-in `ci-gate` job, design §C.1 — use the **proven shell git-diff detector**,
`fetch-depth:0`, the `needs.detect.result` assertion), `web-ci.yml` (reusable matrix over {dashboard,botsite}),
and `pr-freshness.yml` (fold `pr-auto-update` + `pr-conflict-guard`) **non-required, alongside** the current
workflows. Observe green/red parity across a band of PRs (code-only + docs-only). **Then** the owner ratifies
the atomic required-context swap (Q-0239 **G2**) and the six workflow deletions (**G3**). Note the atomic-swap
deadlock warning in the design §E (B2) — the swap must be one change.

### 5. The two AST guards — `[offline]`, calibrated specs ready
Build from the calibrated specs in the idea docs (naive heuristics are too FP-prone — do NOT ship those):
- **`check_audit_seam.py`** — repo-wide per-function reachability (write signal with no reachable
  `emit_audit_action`), warn-first + `architecture_rules/` allowlist.
  [spec](../ideas/audit-seam-coverage-checker-2026-07-05.md).
- **`check_deferred_recovery.py`** — key on the `tasks.spawn`-target (sleep + Discord state mutation lacking
  a persisted-deadline + boot sweep), NOT raw `asyncio.sleep`.
  [spec](../ideas/deferred-action-restart-recovery-checker-2026-07-05.md).
Wire as advisory (`continue-on-error`) first; promote after a clean band (Q-0239 **G4**).

### 6. Smaller / owner-gated tail
- **`check_session_slug_unique` as a gate** — needs CI-context verification that it can resolve `origin/main`
  in the `code-quality` checkout before it can hard-block (else it false-blocks every PR). Verify, then add.
- **App-CI legs gating** (dashboard/botsite/design-system `mypy`+`pytest`) — folds into #4's `web-ci.yml`.
- **`settings.json` Stop-hook rewires** (Q-0239 **G5**, owner-gated): a `check_consistency` Stop mirror; an
  optional changed-module fast-pytest subset.
- **Delete `check_doc_freshness`** (dormant/unwired, Q-0239 **G7**); **keep `check_plan_staleness`**.
- **#794-class content-completeness race** (Q-0239 **G8**): recommended default is accept-advisory + document.

## The "does the gate actually block?" meta-test (worth doing alongside any new gate)
Every gate added should have a known-bad fixture proving it *fails* when it should, not just passes when clean
(the Q-0120 false-green class). See the session idea in `.sessions/2026-07-05-ci-phase-a-gating.md`.
