# 2026-06-20 — pr-conflict-guard: deterministic merge test (fix the "only occasionally red" flake)

> **Status:** `complete`

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

## Shipped (PR #1187)

- `.github/workflows/pr-conflict-guard.yml` — conflict detection rewritten from async
  `mergeStateStatus` polling to a **deterministic `git merge-tree --write-tree`** computation;
  added `actions/checkout`; object-existence guard against false-flags. Reliable red on every
  DIRTY PR, no race.

## Decisions made alone

- Kept the guard **non-required** (Q-0154's documented design) rather than folding it into the
  required `code-quality` gate — the owner's ask was a *reliable red signal*, and GitHub already
  blocks the actual merge of a dirty PR, so hard-blocking adds nothing. Making it required would be
  a branch-protection change (ask-first). Reversible.

## Flagged for maintainer

- This is **UNVERIFIED until the next real DIRTY PR** confirms the red `conflict-guard` status
  appears within seconds (the workflow header carries the same Q-0105 "confirm / delete if it
  flaps" note). The logic is validated locally (merge-tree exit codes + decision cases), but the
  full path (checkout → fetch PR head → post status) only exercises on a live conflicted PR.
- Optional follow-up if you want conflicts to *hard-block* (not just signal): make `conflict-guard`
  a required check in branch protection — say the word and I'll note it (it's a settings change).

## 💡 Session idea (Q-0089)

**A `tools/game_sim/`-style "CI signal smoke test" for the meta-workflow guards.** This guard has now
been fixed ≥3 times and kept regressing because its failure mode (a race) only shows on a *live*
conflicted PR — exactly when it's most costly. A tiny harness that, in a throwaway temp repo,
constructs a known-conflicting branch pair and asserts the *detection logic* returns DIRTY would
make these meta-guards regression-proof the way the balance sim makes game mechanics regression-proof.
The detection here is now pure `git merge-tree`, which *is* unit-testable in a temp repo (no GitHub).
Lane = tooling. (Captured, not built — dedup-checked `scripts/` + `tests/`: no existing
workflow-logic test harness.)

## ⟲ Previous-session review (Q-0102)

The previous step (the #1185 docs PR, same chat) shipped clean — but it **opened born-dirty** (the
branch carried duplicate squashed #1183 commits) and *that* is what exposed today's guard bug. The
prior creature-sim session's own process note had already flagged the post-squash-merge foot-gun and
recommended "branch fresh off main over resetting a dirty tree" — had that been promoted into the
runbook, #1185 likely wouldn't have opened dirty at all. **System improvement:** the recurring
class is *branches not re-based after their predecessor squash-merges*. Two durable guards would
kill it: (1) the now-reliable conflict-guard (this PR) catches it loudly; (2) a session-start check
that warns "your branch base is N commits behind main; rebase before opening a PR" would catch it
*before* the PR. Worth routing the latter as a small guard idea.

## 📤 Run report

- **Did:** root-caused + fixed the flaky conflict-guard (async race → deterministic git merge-tree) ·
  **Outcome:** shipped
- **Shipped:** #1187 — `pr-conflict-guard.yml` deterministic merge test
- **Run type:** `manual · owner-directed bug fix (bugs-first)`
- **⚑ Owner decisions needed:** none (optional: make conflict-guard a required check — offered)
- **⚑ Owner manual steps:** verify the red status on the next real DIRTY PR (UNVERIFIED guard)
- **⚑ Self-initiated:** none (owner reported the bug in-session and directed the fix)
- **↪ Next:** confirm on the next live conflict; optionally promote the "branch-behind-main"
  session-start warning + the workflow-logic smoke-test harness (both captured above).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session-step | 1 (#1187, CI-config fix, auto-merge on green) |
| Runtime (`disbot/`) code changed | 0 |
| Root cause | async `mergeStateStatus` poll race → deterministic `git merge-tree` |
| Files changed | 1 (`.github/workflows/pr-conflict-guard.yml`) |
| Local validation | merge-tree exit codes + 3 decision cases + YAML + `bash -n` all green |
| CI-red rounds | 1 (by-design born-red session gate only) |
| New ideas contributed | 1 (workflow-logic smoke-test harness) |
