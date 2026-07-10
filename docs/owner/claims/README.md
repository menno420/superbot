# Active-work claims — one file per claim

> **Status:** `living-ledger` — the parallel-agent claim mechanism. Not a roadmap, not a
> tracker of merged work (that's `docs/current-state.md`). Source + merged PRs win.
> Owner decisions Q-0126 (claim-before-start) · **Q-0195 (one-file-per-claim, 2026-06-22)**.

## What this is

A lightweight **claim ledger** so parallel agent sessions don't duplicate each other's work.
The maintainer runs several Claude Code sessions at once; two of them picking up the same task
is pure waste. This directory makes "what is someone already on?" answerable **before** a PR exists.

## Why a directory of files (not one shared file) — Q-0195

The old single `active-work.md` had every session **append** its claim to one shared list and
**remove** it from the same list at close. A real-`git merge` simulation
(`tools/sim/claim_layout_sim.py`) measured that shared-append pattern at a **~98% merge-conflict
rate** under concurrent sessions. Splitting by *sector* only halved it (and got worse the more
sessions ran in parallel, because most work clusters in one sector). **One file per claim is
structurally conflict-free** — two sessions never touch the same file — and the simulation
confirmed **0% conflicts at every concurrency level**.

**The one rule that preserves that 0%:** there is **no hand-edited shared index**. Discover claims
with `ls docs/owner/claims/` (this README does not list them). A shared index would re-introduce
the exact append point the split removed.

## How to use it (per CLAUDE.md § Session & plan workflow)

1. **Before starting**, scan this directory (`ls docs/owner/claims/`) *and* the open /
   recently-closed PRs (`list_pull_requests`). If your task is already claimed or in flight,
   coordinate or pick something else — don't duplicate it. The mechanical scan is
   `python3.10 scripts/check_lane_overlap.py <scope> ...` (it reads this directory).
   **In a known-parallel wave, add `--remote`** — it also reads claim files pushed on
   un-merged sibling branches (`origin/claude/*` / `origin/bot/*`), so a sibling's born-red
   first push is visible *before its PR exists*; and re-run the scan **once more right after
   your own claim push** (if both lanes do this, the second pusher always sees the first —
   the cheap mitigation for the simultaneous-start race).
2. **Create one claim file** named for your branch — `<branch-with-slashes-as-__>.md` — containing
   a single bullet line in the format:
   `` - `branch` · **scope** — detail · `path` `path` · date · PR/status ``
   (One claim per file. The branch backtick + path backticks are what `check_lane_overlap.py`
   parses, so keep them.)
3. **At session close**, **delete your own claim file**. The durable record is the PR + the living
   ledger (`docs/current-state.md`) — there is no "recently cleared" list to maintain.

A claim is a soft signal, not a lock — stale files are fine to prune when you see them
(Q-0166 drift-on-sight). The docs-reconciliation pass GC-sweeps any orphan whose branch/PR already
merged (`scripts/check_stale_claims.py`), so the directory never accumulates.

Keep each file short. This is a whiteboard, not an audit trail.
