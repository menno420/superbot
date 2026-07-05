# CI-setup redesign — session brief (2026-07-05)

> **Status:** `historical` — **EXECUTED.** This scoping brief primed the dedicated session; the
> deliverable it framed shipped in PR #1737:
> [`ci-setup-redesign-2026-07-05.md`](ci-setup-redesign-2026-07-05.md) (target-state design + phased
> migration + fresh-repo divergence) and [`../operations/ci-what-runs-where.md`](../operations/ci-what-runs-where.md)
> (the authoritative map). **Read the design doc, not this brief, for the answer** — this remains only
> as the framing record. Two of its assumptions were corrected by the session (kept below for the
> record): "cost = Actions minutes" is moot (the repo is **public** → minutes free); and "~8 unfiltered
> workflows per push" is stale (all app-CI is already `paths`-filtered, and there is no push+PR
> double-fire).

## Mission (owner-set)

Find the **best-possible CI setup** for the bot: get the same coverage with **fewer separate checks**
where that helps, and **add what's genuinely needed**. First-principles, not incremental tinkering.

**Owner aiming decisions** (`AskUserQuestion`, 2026-07-05):
- **Scope = everything, end-to-end** — the 17 GitHub Actions workflows **+** the 40 `scripts/check_*.py`
  **+** the Claude Code hooks (`PostToolUse`/`Stop`/`PreToolUse` in `.claude/settings.json`), designed
  as one coherent system.
- **Optimize for = reliability + cost (Actions minutes).** Consolidation is the **means** to those two
  ends, not a goal in itself — merge/drop checks specifically where it kills flakiness or minutes;
  don't consolidate things that are already reliable and cheap just for tidiness.

## Current landscape (inventoried 2026-07-05 — verify against source; workflows/scripts churn)

### A. GitHub Actions workflows (17) — by role

**Merge-gating (runs on `pull_request`):**
| Workflow | Triggers | Role |
|---|---|---|
| `code-quality.yml` | pull_request, push | **The dominant check + cost.** Bundles: `check_quality.py` (black/isort/ruff/mypy/pytest) + `check_docs.py` + `check_consistency.py` + `check_session_gate.py` (born-red gate) + `check_stale_claims.py`. The one required context. |
| `pr-conflict-guard.yml` | pull_request, push | The `conflict-guard` status (separate required-ish context). |
| `codeql.yml` | pull_request, push, schedule | Security scan — **advisory, not required** → the merge-race (auto-merge fires on `code-quality` green before CodeQL reports; #1728→#1730). |
| `codex-final-review.yml` | pull_request | Codex review trigger. |
| `auto-merge-enabler.yml` | pull_request | Arms native auto-merge on non-draft `claude/*` PRs. |

**Push-triggered app CI (fire on every push, mostly unfiltered — the cost story):**
`botsite-ci.yml`, `dashboard-ci.yml`, `design-system-ci.yml`, `tool-pins.yml`, `pr-auto-update.yml`
— **8 workflows fire per push** once you add code-quality/codeql/conflict-guard. Path-filtering (run
botsite-ci only when `botsite/**` changes, etc.) is an obvious cost lever to evaluate.

**Scheduled / dispatch routines (not merge-gating):**
`backup-db.yml` (schedule), `ci-rerun-watchdog.yml` (schedule+dispatch), `reconciliation-trigger.yml`
(issues+push), `dashboard-data-refresh.yml`, `btd6-data-refresh.yml`, `ai-evals.yml`,
`parity-replay.yml` (dispatch).

### B. Local checkers (40 `scripts/check_*.py`) — by run-context

Only **5** run inside `code-quality` (the merge-gating bundle above). The other ~35 run via **hooks**
(`check_branch_freshness`, `check_quality` on the Stop hook), **routines** (`check_reconciliation_due`,
`check_reconcile_marker`, `check_ledger_hygiene`, `check_current_state_ledger`, `check_loop_health`,
`check_routine_permission_surface`, …), or **ad-hoc / session-close** (`check_session_close_gate`,
`check_docs`, `check_startability_tags`, `check_sector_map`, …). The session's first job is to build
the **authoritative what-runs-where matrix** (script → CI / hook / routine / ad-hoc / dev-only →
required or advisory). `scripts/check_ci_coverage.py` already exists but *only* to detect a CI plumbing
failure (below) — a tell that the plumbing needs fixing, not more compensators.

### C. Claude Code hooks (`.claude/settings.json`) — `PostToolUse` (auto-fix black/isort/ruff),
`Stop` (`claude_stop_check.py` → prints the pre-PR command), `PreToolUse` (`check_branch_freshness`,
`claude_pre_edit`). These are the *local* half of the same coverage — part of "end-to-end."

## The reliability pain points to design out (owner priority #1)

1. **The CodeQL merge-race** — CodeQL is advisory, so auto-merge fires on `code-quality` green before
   it reports; a real alert then lands in merged `main` and needs a follow-up PR (#1728→#1730). Fix
   options in **router Q-0238** (make code-scanning a required check, OR have `check_session_gate`
   refuse green while an alert is open).
2. **Dropped-`synchronize` stalls** — GitHub sometimes drops the `pull_request: synchronize` event, so
   a head gets **no** `code-quality` run → no failure webhook → auto-merge waits forever
   (`check_ci_coverage.py` + `ci-rerun-watchdog.yml` exist only to paper over this; #1283, #1594). A
   more reliable trigger topology (or a required-check that can't be silently skipped) would retire the
   compensators.
3. **Cancellation / born-red edge cases** — the born-red session gate lives *inside* `code-quality`;
   `conflict-guard` is a separate context; cancellation races were patched (`cancel-in-progress:
   false`, #1275). Evaluate whether fewer required contexts = fewer stuck states.
4. **Auto-merge timing** — the "flip the card releases the merge" hazard (journal Rule, 2026-07-05):
   the gate can't currently hold for async scans. Q-0238 is the enforce-side.

## The cost pain points to design out (owner priority #2)

- **~8 workflows per push**, most unfiltered — `code-quality` is the repo's dominant Actions cost
  (already has a docs-only fast path; the app-CI workflows mostly don't path-filter).
- **Duplicated work** across `code-quality` (push+PR both fire) and the app-CI workflows.
- Levers to evaluate: path-filtering the app-CI workflows; `concurrency` groups to cancel superseded
  runs (code-quality already cancels superseded PR runs, Q-0126 — extend the pattern); collapsing
  push+PR duplication; skipping the heavy suite on non-code changes (already partial).

## Genuine gaps to ADD (need-driven, not more-jobs-driven)

- **Q-0238** — code-scanning into the merge hold (the CodeQL race).
- **audit-seam-coverage checker** ([idea](../ideas/audit-seam-coverage-checker-2026-07-05.md)) — would
  have caught 3 of the 8 save-fixes bugs; verified as a real gap in current bot + rebuild.
- **deferred-action restart-recovery checker**
  ([idea](../ideas/deferred-action-restart-recovery-checker-2026-07-05.md)) — small; a 3rd instance is
  already known (`utility_cog.py:61`).
- Whatever the what-runs-where matrix surfaces as **coverage the merge gate doesn't actually enforce**
  (a checker that only runs on a hook or a routine isn't a merge gate — decide which *should* be).

## Method for the CI-setup session

1. **Inventory → the what-runs-where matrix** (every workflow + every `check_*.py` + every hook →
   trigger, run-context, required/advisory, cost, reliability history). This is the ground truth the
   redesign reasons over.
2. **Classify each check** by its true job: **merge-gating** (must be green to merge) · **advisory**
   (informational; must NOT silently gate — the CodeQL lesson) · **routine** (scheduled/dispatch, not
   per-PR) · **dev-only** (hook/local, never CI). Mis-classification is the root of both the race and
   the cost.
3. **Consolidate where it serves reliability/cost:** the ideal is **one required merge context** that
   deterministically reflects "is this mergeable" (fewer stuck states, no dropped-context race);
   path-filter the app-CI workflows; collapse push/PR duplication; retire compensators
   (`check_ci_coverage`/`ci-rerun-watchdog`) if the trigger topology is fixed at the root.
4. **Add the genuine gaps** (above) into the *right* class — a new checker joins the merge gate only if
   it should block a merge; else it's advisory/routine.
5. **Produce the deliverable:** a **target-state CI design** (the workflow set + the required-check
   contract + the check→class matrix + the hook split) **and a phased, reversible migration plan**.

## Guardrail — this is owner-gated executable config; propose before ripping out

Workflows, `.claude/settings.json` hooks, and branch-protection required checks are **executable
config** (autonomy boundary): the session **proposes the target design and gets owner sign-off before
destructive changes** (removing a required context, deleting a workflow, changing what gates a merge).
Migrate **incrementally, reversibly, warn-first** — never drop a check without proving the new setup
covers it. The reconciliation/routine plumbing (S5) must keep working throughout.

Home: **S5 Operations** ([`../current-state/S5-ops.md`](../current-state/S5-ops.md)) — this is an ops
lane. Provenance: `.sessions/2026-07-05-ci-setup-brief.md`; the aiming decisions are that session's
`AskUserQuestion` record.
