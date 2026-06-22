# Audit — why the automated dashboard-refresh PR conflicts (and the wider CI-flake picture)

> **Status:** `audit` — autonomous investigation, 2026-06-21, owner-directed (owner away).
> Records the root cause of PR #1261's conflict, every hunch considered (with verdicts), the
> fixes shipped this session, and the carried-forward analysis of the broader "CI doesn't fire /
> false-dirty" mystery. Written for owner review.

## TL;DR

PR **#1261** (`chore(dashboard): refresh generated data`, branch `bot/dashboard-refresh`) had a
**real** merge conflict — `git merge-tree` confirms `CONFLICT in dashboard/data/dashboard.json`
(exit 1). The conflict-guard was **right** to flag it. The cause is an anti-pattern:
**`dashboard.json` embedded volatile, run-specific metadata** — a **wall-clock `generated_at`** and
the generator-host **`branch`** name — so *any two independent regenerations edit the same lines with
different values* and conflict by construction. This is **separate** from the earlier false-`dirty` /
CI-not-firing issues (those are GitHub async-pipeline flakiness; this is a genuine git conflict).

**Shipped this session** (PR #1267): made `generated_at` deterministic (latest-commit time), removed
the `branch` field, gave the refresh workflow a self-heal/close path, and corrected the stale
`pr-auto-update.yml` header. **Recommended next:** a merge queue (the durable cross-cutting fix).

---

## 1. The #1261 investigation (what, verified with git not GitHub)

| Check | Result |
|---|---|
| `git merge-tree --write-tree origin/main <pr-head>` | **exit 1** → real conflict |
| Conflicting file | `dashboard/data/dashboard.json` (only) |
| PR head vs its base (`afcf2e68`) | 32 ins / 32 del in dashboard.json |
| main's dashboard.json since that base | **170 ins / 97 del** (reconciliation pass regenerated it) |
| Generator determinism (same commit, 2 runs 2s apart) | identical sha1 **after** the fix; **differed** before (wall-clock) |

So both sides edited the *same generated file* divergently from the merge base → a textbook content
conflict. Not a GitHub misreport — git agrees.

## 2. Root cause (layered)

1. **Volatile metadata in a committed generated file (the core).** `dashboard.json` carried
   `meta.generated_at` = **wall-clock** `datetime.now()` and `meta.build.branch` = the **working
   branch** of whoever regenerated it. Two independent regenerations therefore always differ on those
   exact lines. When the reconciliation pass regenerated `dashboard.json` on `main` *and* the
   dashboard bot had its own regeneration on `bot/dashboard-refresh`, the two diverged on
   `generated_at`/`branch` (plus the real feed data) → guaranteed conflict. The wall-clock value also
   meant **every** refresh run saw a diff, so the workflow churned a PR every cadence even with no real
   change.
2. **The bot branch went stale.** #1261 was built on `main@afcf2e68` at 21:41; `main` then advanced a
   lot (the nineteenth reconciliation pass landed, regenerating the file). Nothing rebuilt the bot
   branch on the new `main` before the conflict set in.
3. **The generic auto-updater skips `bot/*`.** `pr-auto-update.yml` only heals `claude/*` branches, so
   it never touched `bot/dashboard-refresh`. (And it *couldn't* cleanly: `update-branch` does a 3-way
   merge, which is the wrong tool for a generated file — it just re-hits the same conflict. Rebuilding
   the branch on current main is the right strategy, which the refresh workflow already does on its
   diff-path.)
4. **No "close the stale PR" path.** When a refresh run found no fresh diff it just `exit 0`'d, leaving
   any already-open, now-stale PR stranded and red indefinitely.

## 3. Hunches considered — and the verdict on each

The owner explicitly asked to record what was considered and why it was/wasn't the answer.

| Hunch | Verdict | Why |
|---|---|---|
| **GitHub falsely marks it `dirty`** (like #1256/#1260) | ❌ Not this time | `git merge-tree` independently says **CONFLICT**. This is a *real* conflict; the guard is correct. |
| **A churning/non-deterministic generator field** | ✅ **Primary cause** | `generated_at` was wall-clock → changed every run; `branch` was host-specific. Both are the same line on every regeneration → structural conflict + constant churn. Confirmed: pre-fix two runs differed; post-fix identical. |
| **Parallel sessions / load colliding on the file** | ⚠️ Contributing, not root | The *collision* was real (reconciliation regenerated on main while the bot PR existed), but it only conflicts *because* of the volatile metadata. Two deterministic regenerations at the same commit are byte-identical and wouldn't conflict. |
| **Actions minutes/runner overload** (owner's earlier hypothesis) | ❌ Ruled out | Public repo = unlimited minutes; and the failure mode here is a git conflict, not a runner failure. (Owner's own counter-evidence — 4 parallel sessions fine, 1 session sometimes fails — already killed the load theory for the *separate* CI-firing issue too.) |
| **The build block is self-referential (file can't contain its own commit)** | ✅ Real, but *expected* | `meta.build.commit` always lags `main` by the merge commit, so a refresh PR after every merge is somewhat inherent. This is *correct* behavior (it records the deployed snapshot's version) and, post-fix, is bounded + non-conflicting. Documented, not "fixed". |
| **`pr-auto-update` should have healed it** | ⚠️ Partly | It would have, *if* it covered `bot/*` — but it doesn't, and `update-branch` (merge) is the wrong tool for a generated file anyway. The refresh workflow's own rebuild-on-main is the right mechanism; it just lacked the stale-PR-close path. |

## 4. Fixes shipped this session (PR #1267)

1. **`scripts/export_dashboard_data.py` — deterministic `generated_at`.** Now anchored to the latest
   commit's `committed_at` (falls back to wall-clock only if git is unavailable). Two regenerations at
   the same commit are byte-identical (verified by `test_generated_at_is_deterministic_not_wall_clock`).
   The refresh workflow now only fires on a *real* source change.
2. **`scripts/export_dashboard_data.py` — removed `meta.build.branch`.** It was transient
   generator-host junk and a needless conflict source; the `/status` template already guarded on its
   absence (`{% if build.branch %}`). Updated the redaction contract (`SITE_META_BUILD_FIELDS`) and the
   test assertion; regenerated both `dashboard.json` and the public `site.json` subset;
   `check_dashboard_data` green.
3. **`.github/workflows/dashboard-data-refresh.yml` — self-heal.** Added the missing path: when a run
   finds the data already fresh **and** a `bot/dashboard-refresh` PR is still open, it **closes that PR
   and deletes the branch** (it can only be a stale/conflicting older regeneration). The diff-path
   already rebuilds the branch on current `main`, so it is never stale-based.
4. **`.github/workflows/pr-auto-update.yml` — corrected the stale header.** It claimed "this repo
   requires branches to be up to date before merging" — **false** (owner confirmed the setting is OFF).
   The header now states the real value (re-test against current main + force a mergeability recompute
   that clears stuck false-`dirty`) and notes `bot/*` is out of scope.

## 5. Recommended follow-ups (NOT shipped unsupervised)

- **Merge queue (the durable cross-cutting fix).** Enable a GitHub merge queue on `main`. Inside a
  queue GitHub serialises merges, auto-updates each PR to the front, re-tests, and merges — which
  removes the false-`dirty` stalls *and* the stale-base conflict class at once (it would have prevented
  both #1260's stall and #1261's conflict). It is an owner admin toggle (Settings → Rules/Branches).
- **Stop committing self-referential deploy metadata, if the churn ever annoys.** The `meta.build`
  block inherently lags `main` by one commit, so a refresh PR after every merge is structural. If that
  cadence is unwanted, have the refresh decide "is a refresh needed?" from the *substantive* data only
  (feeds/counts/catalogue), ignoring `meta`. Left as a judgement call — the current cadence is bounded
  and harmless post-fix.

## 6. The "CI didn't run on my latest commit" strand — RESOLVED (2026-06-22)

> Update: the carried-forward mystery is **solved**. Earlier in this doc it was listed as two
> unconfirmed hypotheses (event-delivery flakiness / app-token anti-recursion). Both are **wrong**;
> the real cause is a recent concurrency change. Keeping the wrong guesses struck through is
> deliberate — it's the record of how the diagnosis converged.

**Root cause: `code-quality.yml` had `concurrency: cancel-in-progress: true` (PR refs), added
2026-06-20 (#1195, Q-0126, to save minutes).** Under the born-red flow's **rapid event burst** (open →
push → push within ~2 min), GitHub's run cancellation **races and drops the run for the *head*
commit**, leaving the PR with no completed required check → auto-merge stalls.

**Smoking-gun evidence (PR #1274, 2026-06-22):** on the **same** `pull_request: synchronize`
event/commit (`64e4f86`), `codex-final-review` (`cancel-in-progress: false`) **ran**, while
`code-quality` (`cancel-in-progress: true`) **did not**. Same trigger, same commit — the *only*
difference was the flag. And it fits the owner's two key observations exactly:
- *"It used to work; fix-pushes always re-ran CI"* → before #1195 (June 20), code-quality had **no**
  cancellation, so every push got its own run. The strand is **as old as the cancel flag**, not older.
- *"Could it be too many checks?"* → yes: the growing check-suite + the born-red open-then-push pattern
  are what create the **rapid event burst** that triggers the cancellation race.

**Hypotheses this disproves:**
- ~~`synchronize` is inherently flaky~~ — the event fired; `codex-final-review` used the *same* one.
- ~~merge-ref unavailable (dirty PR)~~ — #1274 was `blocked`, not `dirty`.
- ~~app-token anti-recursion~~ — irrelevant; both workflows share the same token + event.

**Fix (shipped):** `code-quality.yml` → `cancel-in-progress: false` (matching `codex-final-review`).
The minute-saving rationale is **moot** — this is a public repo with **unlimited** Actions minutes —
so cancelling buys nothing and costs reliability. Redundant older-commit runs are harmless (free).

**Still complementary:** the **merge queue** (above) remains the durable cross-cutting fix (it also
addresses the separate false-`dirty` aggregation under a heavy check-suite), and
`scripts/check_pr_mergeable.py` (#1260) gives git-truth mergeability so agents never trust GitHub's
async signal.

### pytest "why 4 minutes / only run new tests?" (owner question, 2026-06-22)
- It is **already parallelized** — CI runs `pytest tests/ -n auto` (pytest-xdist across the runner's
  cores); ~11.5k tests in ~4 min on a 2-core runner is normal, not pathological.
- **"Only run new/changed tests" is unsafe as a merge gate** — the *point* of the suite is catching
  **regressions** (a change breaking *existing* tests). Running only new tests would let regressions
  merge. Impact-based selection (`pytest-testmon`/coverage) is the safer cousin but is risky as a sole
  gate (stale dep-maps miss things) — fine only as an *advisory* fast lane, never the gate.
- The legitimate lever is the **slow-test long tail** (profiled with `--durations`): a handful of
  tests that spin up real subprocess git repos dominate (e.g. the merge-state / export-data temp-repo
  suites). Optimizing/marking those is the real speedup; cores and "skip regressions" are not.

## 7. Appendix — evidence

- PR #1261 head `407e4d22`, base `afcf2e68`; `git merge-tree origin/main 407e4d22` → exit 1, conflict
  in `dashboard/data/dashboard.json`.
- Pre-fix drift sample on `main`: `generated_at` `22:08:34Z`→`22:30:55Z`; `branch`
  `claude/reconcile-1260`→`claude/modest-gates-0ble76`.
- Post-fix determinism: two runs 2s apart → identical `sha1 f7d7cd64…`.
- All verification green: `test_export_dashboard_data.py` (34), `test_check_dashboard_data.py`,
  `tests/unit/dashboard/` (99 passed), `check_dashboard_data` OK, `check_quality --check-only` clean.
