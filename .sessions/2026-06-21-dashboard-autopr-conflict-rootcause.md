# Session — dashboard auto-PR conflict root cause (2026-06-21, autonomous)

> **Status:** `in-progress`

Owner-directed autonomous investigation (owner away until tomorrow): *why does the automated,
data-only `bot/dashboard-refresh` PR (#1261) end up with a real merge conflict, when no other
session is editing it?* Plus the earlier-parked steps (pr-auto-update header fix, merge-queue
write-up) and a thorough findings doc for review.

## Root cause (confirmed with git, not GitHub)
`#1261` is a **genuine** conflict (`git merge-tree` exit 1, `CONFLICT in dashboard/data/dashboard.json`)
— the conflict-guard correctly flagged it. The mechanism is layered:
1. **`dashboard.json` embeds volatile, run-specific metadata** — a **wall-clock `generated_at`** and a
   self-referential **`build` block** (HEAD commit/subject/committed_at + the working **`branch`**
   name). Any two independent regenerations therefore edit the *same lines* with different values →
   a *structural* conflict whenever two branches both regenerate the file.
2. The bot branch went **stale** (built on an old main at 21:41); main then moved far ahead (the
   reconciliation pass regenerated `dashboard.json`, +170/-97 lines) and nothing rebuilt the bot
   branch on current main in time.
3. The generic `pr-auto-update.yml` only heals `claude/*` branches — **`bot/*` is never touched**.
4. The refresh workflow only rebuilds its branch when it sees a *fresh diff*; it has **no
   "close the stale PR" path**, so a stranded conflicting PR can persist.

This is **distinct** from the earlier false-`dirty` / CI-not-firing issues — this one is a *real*
conflict with a real, fixable cause.

## Fixes this session
1. **`export_dashboard_data.py`: `generated_at` → deterministic (latest-commit time), not wall-clock.**
   Kills the every-run churn + the guaranteed-conflict line; makes the file a pure function of source.
2. **`dashboard-data-refresh.yml`: self-heal** — always rebuild on current main; **close the stale bot
   PR when a run finds nothing to refresh** (the missing path).
3. **`pr-auto-update.yml`: correct the stale header** (the repo does *not* require up-to-date — owner
   confirmed via screenshot) and note `bot/*` is handled by its own workflow.
4. **Findings doc** (`docs/audits/`): full analysis, options considered + why, merge-queue write-up,
   CI-firing forensics plan — for owner review.

Recommended-but-not-shipped-unsupervised (documented): dropping the `branch` field (touches the
`/status` UI on two sites + the redaction contract + tests).

No runtime `disbot/` code.
