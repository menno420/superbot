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
