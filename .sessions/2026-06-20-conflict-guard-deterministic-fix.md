# 2026-06-20 — pr-conflict-guard: deterministic merge test (fix the "only occasionally red" flake)

> **Status:** `in-progress`

## Arc

Bugs-first. While shipping #1185 the owner hit a **merge conflict that CI did not turn red on**, and
noted this is recurring: *"there have been a lot of attempts to fix that so CI would turn red on a
dirty PR, but for some reason this only seems to work occasionally."*

## Root cause

`.github/workflows/pr-conflict-guard.yml` detected conflicts by reading GitHub's
**asynchronously-computed** `mergeStateStatus`. Right after a push/merge GitHub reports `UNKNOWN`
(the query is what *triggers* the computation), so the guard polled through that window — but the
poll had a fixed 30s budget with no relation to GitHub's actual compute time. When computation ran
long (PR-open time, load), the poll **gave up, posted nothing, and the PR stayed green** until the
laggy 3-hour cron. That residual race *is* the "only works occasionally."

## Fix (this PR)

Stop asking GitHub's async mergeability entirely — **compute the merge ourselves** with
`git merge-tree --write-tree <base> <head>` (exit 0 = clean, 1 = conflict): deterministic,
synchronous, decided the instant the job runs. No UNKNOWN window, no poll, no race.

- Added an `actions/checkout` (fetch-depth 0) so the merge base is reachable.
- `evaluate()` fetches the base branch + `refs/pull/N/head`, pre-verifies **both commit objects
  exist** (`git cat-file -e` — a missing object *also* exits 1, which would false-flag), then runs
  `merge-tree` and posts the `conflict-guard` commit status (failure/success/skip).
- Kept the design unchanged otherwise: non-required visibility status (Q-0154), same triggers
  (`push:main` · `pull_request` · `schedule` backstop), same token model.

## Verification

- `git merge-tree` exit codes on the runner's git 2.43.0: conflict→1, clean→0 (validated locally).
- Decision logic simulated locally: conflict→DIRTY, clean→CLEAN, missing-object→UNKNOWN (no
  false-flag).
- YAML parses; `bash -n` clean on the embedded run script.

## Shipped

_(filled at close)_
