# Idea — `check_workflow_gh_permissions`: a workflow's `permissions:` must cover the `gh` ops it runs

> **Status:** `ideas` — a mechanizable CI-guard idea surfaced 2026-07-06 building the CodeQL stuck-scan
> watchdog. Distinct from `check_routine_permission_surface.py` (that guards *Claude Code* `.claude/settings.json`
> routine permissions vs. the `ask` brake — a different layer).

## The gap it closes

A GitHub Actions step runs a script that performs `gh` API operations (`gh issue create`, `gh workflow run`,
`gh pr edit`, …). Each needs a matching scope in the job's `permissions:` block **when the fallback
`GITHUB_TOKEN` is used** (a PAT like `ROUTINE_PAT` carries its own scopes and bypasses the block). Nothing
checks that the block actually grants what the script calls, so an escalation/side-effect path can ship that
**silently no-ops** under the `GITHUB_TOKEN` fallback.

**Concrete miss this caught:** PR #1743 added `check_ci_coverage.open_alert_issue` (`gh issue create`) but
`ci-rerun-watchdog.yml` had only `contents: read` / `actions: write` / `pull-requests: read` — **no
`issues: write`**. Under `GITHUB_TOKEN`, that escalation would fail and only log. Fixed 2026-07-06 by adding
`issues: write`; a checker would have flagged it at author time.

## The precise signal (not a naive heuristic)

For each `.github/workflows/*.yml` step whose `run:` invokes a repo script, map the `gh <resource> <verb>`
calls in that script to the required `permissions:` scope, and assert the job's effective `permissions:`
(job-level ∪ workflow-level) grants each. Minimal mapping table:

| `gh` call | Required scope |
|---|---|
| `gh issue create` / `issue comment` / `issue edit` | `issues: write` |
| `gh workflow run` / `run rerun` | `actions: write` |
| `gh pr edit` / `pr comment` / `pr review` | `pull-requests: write` |
| `gh api ... -X POST/PATCH` (contents) | `contents: write` |

**Calibration / FP control (Q-0105):** only flag when the token is (or can fall back to) `GITHUB_TOKEN` —
skip steps that set `GH_TOKEN` to a PAT-only secret with no `|| secrets.GITHUB_TOKEN`. Static `gh`-call
extraction is grep-simple but misses dynamically-built commands; ship **warn-first**, validate over a few
sessions before trusting, and keep an `architecture_rules/`-style allowlist. Delete if it proves noisy.

## Why it's worth having

The whole watchdog fleet (`check_ci_coverage`, `check_codeql_coverage`, future ones) escalates via `gh`; a
missing scope makes the *safety net itself* silently fail — exactly the "waits forever with nothing to
notice" class these watchdogs exist to kill. One cheap author-time check closes that meta-gap.
