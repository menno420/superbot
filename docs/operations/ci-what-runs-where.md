# CI — what runs where (the authoritative map)

> **Status:** `reference` — the single map of every automated check in this repo: which **workflow**
> runs it, on which **trigger**, in which **run-context class**, and whether it **gates a merge**.
> **Verify against source** — `.github/workflows/*.yml`, `scripts/check_*.py`, and `.claude/settings.json`
> churn; when this table and a file disagree, the file wins. Built 2026-07-05 from the CI-setup
> redesign (PR #1737); the target-state columns are the **proposed** design in
> [`../planning/ci-setup-redesign-2026-07-05.md`](../planning/ci-setup-redesign-2026-07-05.md), not yet
> applied.

## Why this doc exists

Nothing else enumerates *trigger → run-context → class → merge-gating* in one place. Before this map,
every session had to re-derive "what actually gates a merge?" from the raw `.github/workflows/` +
`scripts/` listings — and the answer is much narrower than the check count suggests. This is the ground
truth the redesign reasons over, and the CI half of the "gate-state readout" idea.

## Load-bearing facts (verified 2026-07-05 against source)

- **The repo is PUBLIC** (`menno420/superbot`) → **GitHub Actions minutes are free/unlimited.** "Cost"
  here is **not** billed minutes; it is wall-clock latency (the agent/dev feedback loop), PR-checks-UI
  clutter, concurrent-job/runner contention, and merge-race hazards from too many required contexts.
  *(This corrects the redesign brief's "cost = Actions minutes" framing.)*
- **The one required merge context today is `code-quality`** (the job name in `code-quality.yml`;
  `check_ci_coverage.REQUIRED_CHECK = "code-quality"` confirms it). Auto-merge (`auto-merge-enabler.yml`)
  merges a non-draft `claude/*` PR the instant that check is green.
- **CodeQL is advisory, not required** — so auto-merge fires on `code-quality`-green **before** CodeQL
  reports (the #1728→#1730 merge-race; router Q-0238).
- **All app-CI workflows are already `paths`-filtered** (`dashboard-ci`, `botsite-ci`,
  `design-system-ci`, `tool-pins`). *(This corrects the brief's "~8 unfiltered workflows per push"
  cost story — verified stale.)*
- **There is no push+PR "double-fire" to eliminate** — `code-quality.yml` and `codeql.yml` both trigger
  `push` on `branches: [main]` **only**; a `claude/*` push fires the heavy gate solely via
  `pull_request: synchronize`. *(Corrects an assumption in the brief.)*
- **CI runs Python 3.10.** Only **5** of the 40 `check_*.py` run inside the `code-quality` merge gate;
  the other ~35 run via hooks, routines, or ad-hoc/session-close.

**Class legend:** **G** = merge-gating (must be green to merge) · **A** = advisory (CI-visible,
non-blocking / `continue-on-error`) · **R** = routine (schedule/dispatch, not per-PR) · **I** = infra
(auto-merge / conflict / rerun plumbing) · **D** = dev/hook-only (local, never a CI step).

---

## 1. GitHub Actions workflows (17)

| # | Workflow | Trigger (today) | Class | Required? | Concurrency | Role / notes |
|---|---|---|---|---|---|---|
| 1 | `code-quality.yml` | `push:main`, `pull_request:main`, `workflow_dispatch` | **G** | **YES** (`code-quality`) | `code-quality-${ref}`, **cancel:false** | The merge gate. Bundles ruff/black/isort/mypy/pytest + `check_docs` + `check_consistency` + `check_session_gate` (born-red) + `check_stale_claims`. Docs-only fast path skips heavy steps but still reports green. |
| 2 | `codeql.yml` | `push:main`, `pull_request:main`, weekly cron | **G** (via ruleset) | **YES** (ruleset, 2026-07-05) | `codeql-${ref}`, **cancel: false** ✓ (#1739) | SAST. Now a merge gate via the **`codeql-merge-protection` ruleset** (Require code scanning results · CodeQL · High+ · Active) — auto-merge waits for CodeQL and blocks on a High+ alert (closes the Q-0238 race). `cancel:false` so the head run isn't dropped. Residual (a CodeQL run that errors/hangs) is now bounded alerting-only by the `ci-rerun-watchdog` stuck-scan leg (#7). |
| 3 | `auto-merge-enabler.yml` | `pull_request:[opened,reopened,ready_for_review]` | **I** | — | — | Arms native auto-merge on non-draft `claude/*` PRs. Needs `ROUTINE_PAT`. Does **not** fire on MCP-created PRs (arm manually, Q-0127). |
| 4 | `codex-final-review.yml` | `pull_request:[synchronize,ready_for_review]` | **A** | — | — | Posts `@codex review` when the born-red card flips ready, so Codex sees the final head. |
| 5 | `pr-conflict-guard.yml` | `push:main`, `pull_request:[opened,sync,reopened]`, `*/30` cron, dispatch | **I** | — | cancel:true (idempotent status) | Posts a red `conflict-guard` status on a DIRTY PR (main moved). Visibility, not a required gate. |
| 6 | `pr-auto-update.yml` | push / PR / schedule | **I** | — | — | Keeps `claude/*` PR branches updated against main. |
| 7 | `ci-rerun-watchdog.yml` | `schedule */12`, dispatch | **I** | — | — | Two "waits-forever" compensators (needs `ROUTINE_PAT`). **Leg 1:** re-kicks `code-quality` when GitHub **dropped** the `synchronize` event (`check_ci_coverage.py`). **Leg 2 (A10, 2026-07-06):** alerts on a **CodeQL scan that started then errored/hung** — the residual the merge-protection ruleset leaves open (`check_codeql_coverage.py`, alerting-only until the re-dispatch path is live-confirmed). |
| 8 | `dashboard-ci.yml` | `push`/`pull_request` **paths:`dashboard/**`** | **A** | no | — | Dashboard `mypy` + `pytest` (main gate installs only the bot's reqs, so these `importorskip` there). |
| 9 | `botsite-ci.yml` | `push`/`pull_request` **paths:`botsite/**`** | **A** | no | — | Bot-site `mypy` + `pytest`. Twin of dashboard-ci. |
| 10 | `design-system-ci.yml` | **paths:`design-system/**`** | **A** | no | — | React/Tailwind typecheck + test + build. |
| 11 | `tool-pins.yml` | **paths:** pin sources | **A** | no | — | `check_tool_pins.py` — fails when the 3 formatter-pin locations drift (#1315). Not required → shows red but doesn't block. |
| 12 | `reconciliation-trigger.yml` | `push:main`, issues | **R** | — | — | Opens the `reconcile` issue at every 30th-PR boundary (Q-0107). |
| 13 | `dashboard-data-refresh.yml` | `schedule 17 */2`, dispatch | **R** | — | — | Regenerates `dashboard/data/dashboard.json`, opens a PR. |
| 14 | `btd6-data-refresh.yml` | dispatch-only | **R** | — | — | BTD6 data re-seed → reviewable PR (Q-0049). |
| 15 | `backup-db.yml` | daily+monthly cron, dispatch | **R** | — | — | Postgres backup. |
| 16 | `parity-replay.yml` | dispatch-only | **A/R** | — | none ⚠ | Replays the `parity/` golden harness. Add a concurrency group. |
| 17 | `ai-evals.yml` | dispatch-only | **R** | — | none ⚠ | AI eval battery. Add a concurrency group. |

**On a typical `claude/*` PR push:** the heavy gate `code-quality` runs (via `synchronize`); CodeQL
runs (advisory); `codex-final-review` and `pr-conflict-guard` may run; the app-CI workflows run **only
if** their `paths` matched. There is **no redundant push-triggered heavy run** — `push` is `main`-only
on both heavy workflows.

---

## 2. The 43 `scripts/check_*.py` — by run-context

### 2a. Merge-gating today (inside `code-quality.yml`) — the real gate is these 5 + the tool steps

| Checker | Role |
|---|---|
| `check_quality.py` | The local CI-mirror; in CI its constituent tools (black/isort/ruff/mypy/pytest) run as explicit steps. |
| `check_docs.py` `--strict` | Doc-hygiene: Status badges, dead links, read-path refs. Runs on **every** PR incl. docs-only. |
| `check_consistency.py` `--mode strict` | UX/interaction linter (graduated rules only) over `disbot/views/`. |
| `check_session_gate.py` | The born-red merge hold (PR-only). |
| `check_stale_claims.py` `--strict` | **Advisory** (`continue-on-error`) — surfaces orphan claim files. |
| `check_audit_seam.py` `--mode strict` | **Advisory** (`continue-on-error`, deps block, code-gated) — flags a mutation write signal that never reaches `emit_audit_action` (the #1728 bug class). Warn-first; promotion to a hard gate is owner-gated (Q-0239 G4). |
| `check_deferred_recovery.py` `--mode strict` | **Advisory** (`continue-on-error`, deps block, code-gated) — flags a spawned sleep→Discord-state-mutation timer with no persisted deadline + boot reconcile (the restart-recovery-gap class). Warn-first; G4. |
| `check_session_slug_unique.py` `--strict` | **Advisory** (`continue-on-error`, PR-only) — surfaces a reused `.sessions/` slug (BUG-0027). Fails open (git failure → no finding); wired to verify `origin/main` resolves in CI before a gate promotion. |

Plus, **indirectly gating via the pytest ratchet:** `check_command_reachability`,
`check_settings_reachability`, `check_setup_copy`, `check_architecture` (run as invariants tests).

### 2b. Coverage the merge gate does NOT enforce (was the highest-value finding)

Several checks whose job *should* block a merge ran **only** locally or on a routine. **Three of them
are now hard steps inside the required `code-quality` context (PR #1739)** — they gate merges with no
branch-protection change:

| Checker | Was | Now |
|---|---|---|
| `check_architecture.py` `--strict` | Stop hook + SessionStart only (the #1 gap) | **✅ GATING** (`code-quality`, deps block) — a new layer violation now blocks merge |
| `check_tool_pins.py` | own advisory workflow (not required) | **✅ GATING** (`code-quality`, always-run) — a pin desync now blocks (was red-only, #1315) |
| `check_workflow_concurrency.py` | new, advisory (#1737) | **✅ GATING** (`code-quality`, always-run) — a cancelling merge-relevant workflow now blocks (#1275) |

Still local/routine-only (candidates for a verified follow-up, not yet gating):

| Checker | Runs where today | Should it gate? |
|---|---|---|
| `check_session_slug_unique.py` | session-close only | Yes — the slug clobber (BUG-0027) is author-time; deferred (its `origin/main` compare needs CI-context verification before it can be a hard gate). |
| `check_governance_files.py` | **UNUSED** (no operational caller) | Fold into `check_docs`. |
| `check_dashboard_data.py` | routine | Belongs on the dashboard leg (drift shipped to main: #988/#1020/#1023). |
| dashboard / botsite / design-system `mypy`+`pytest` | advisory app-CI | Yes — promote to gating on their (path-filtered) legs. |

**The docs-only fast path skips the live-tree ground-truth tests — verified case, 2026-07-08
(PR #1843 archaeology).** #1843 did not merge red; it merged **green-by-skip**. It was
docs-only, so its required `code-quality` run on head `faaa29f` completed green in **12 s**
(11:06:56→11:07:08Z): the fast path (§1 row 1) skipped ruff/mypy/**pytest**, and the doc-hygiene
gate that *does* run on docs-only PRs (`check_docs --strict` — reachability/badges) does **not**
check plan homing. The PR added `docs/planning/per-repo-settings-state-ledger-2026-07-08.md`
with no routing-doc link, so `test_check_plan_homing.py::test_live_repo_plans_are_all_homed` — a
**live-tree** test that validates the checked-out tree, not the diff — failed on every
subsequent branch containing that merge where pytest actually ran, until parallel sessions homed
the plan by hand (roadmap horizon in #1845 commit `75a495a`; plan-index row on the #1846 lane
`58a2e24`; deduped `0dc13f6`). Root-cause class: **the one PR class that can introduce docs
drift (docs-only) is exactly the class where the live-tree tests guarding it are skipped.**
Follow-up idea (named CI step + push-main culprit issue + stdlib docs guards on the fast path):
[`../ideas/live-tree-test-culprit-attribution-2026-07-08.md`](../ideas/live-tree-test-culprit-attribution-2026-07-08.md).

### 2c. Advisory (correctly non-blocking — a session may legitimately be *fixing* the thing)

`check_current_state_ledger` · `check_migration_collision` · `check_permission_overlap` ·
`check_routine_permission_surface` · `check_session_log` (content enders — the *badge* gates, the
*content* is advisory).

### 2d. Routine (schedule / dispatch / reconciliation set — not per-PR)

`check_reconciliation_due` · `check_reconcile_marker` · `check_ledger_hygiene` ·
`check_completion_ledger_parity` · `check_plan_code_drift` · `check_plan_homing` ·
`check_plan_staleness` · `check_sector_map` · `check_sector_next_freshness` ·
`check_startability_tags` · `check_bug_book_rootfix_backlog` · `check_plan_backlog` ·
`check_loop_health` · `check_ci_coverage` (the dropped-`synchronize` watchdog) ·
`check_codeql_coverage` (the CodeQL stuck-scan watchdog, A10 — shares `lib.owner_alert`).

### 2e. Dev / hook / ad-hoc aids (never a CI step, correctly)

`check_branch_freshness` (Pre/Stop hook) · `check_lane_overlap` · `check_pr_mergeable` ·
`check_phase_gate` (advisory-only per current-state) · `check_generated_artifacts_fresh` ·
`check_session_close_gate` · `check_autospec_fidelity`.

### 2f. Dormant / unwired

*(none)* — `check_doc_freshness.py` was **deleted 2026-07-06** (Q-0239 **G7**): dormant/unwired, no
operational caller (Q-0105 disposability). *`check_plan_staleness` stays live in the reconciliation set
(2d) — it was explicitly kept.*

---

## 3. Claude Code hooks (`.claude/settings.json`) — the local half

> Hooks + `.claude/settings.json` are **owner-gated executable config** (Q-0106): the hook *scripts* are
> free to edit; the *wiring* changes only by owner direction / a router DISCUSS Q.

| Hook event | Script | What it enforces locally | Also in CI? |
|---|---|---|---|
| `PreToolUse` (Edit/Write) | `claude_pre_edit.py` | pre-edit orientation / context checks | — |
| `PreToolUse` (Bash) | `check_branch_freshness.py` | warns on a stale branch | — |
| `PostToolUse` (Edit/Write) | `claude_post_edit.py` | **auto-fixes** black/isort/ruff; loud warning on change | yes → `code-quality` (truth) |
| `PostToolUse` (create_pull_request) | `claude_pr_subscribe_reminder.py` | reminds to subscribe to PR activity | — |
| `Stop` | `claude_stop_check.py` | prints the pre-PR command; runs `check_quality` (black/isort/ruff/mypy/pytest) + `check_architecture --strict` | partial — `check_architecture` is **hook-only** today (the gap in §2b) |
| `Stop` | `check_branch_freshness.py` | branch-freshness advisory | — |
| `SessionStart` | `claude_session_start.sh` | builds the Python env + CodeGraph index; prints the session banner | — |

**The key hook↔CI observation:** `check_architecture --strict` and `check_consistency --strict` run at
`Stop` (local) and, for architecture, **nowhere in CI** — so the merge gate does not enforce the layer
boundaries the whole repo is organised around. Closing that is the single highest-value hook↔CI move
(see the redesign doc §C.5). The CodeGraph cold-start blip (hook silently disables CodeGraph for the
session) should be surfaced prominently in the SessionStart banner.

---

## 4. Where to go next

The **target-state** for every row above — the one aggregate required context (`ci-gate`), the CodeQL
merge-protection ruleset, the ruff consolidation, the reliability fixes, and the phased owner-gated
migration — is in
[`../planning/ci-setup-redesign-2026-07-05.md`](../planning/ci-setup-redesign-2026-07-05.md).
