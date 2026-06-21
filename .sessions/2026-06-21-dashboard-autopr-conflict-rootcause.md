# Session — dashboard auto-PR conflict root cause (2026-06-21, autonomous)

> **Status:** `complete`

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

## Verification
- `git merge-tree` confirmed #1261 is a **real** conflict (not GitHub false-dirty).
- Generator determinism proven: two runs 2s apart → identical sha1 (`f7d7cd64…`); pre-fix differed.
- `pytest test_export_dashboard_data.py` (34) · `test_check_dashboard_data.py` · `tests/unit/dashboard/`
  (99) · `test_check_generated_artifacts_fresh.py` · `tests/unit/botsite` (38) — all green.
- `check_dashboard_data` OK · `check_generated_artifacts_fresh` OK (4 fresh, structural) ·
  `check_docs --strict` green · `check_quality --check-only` green.
- Findings doc: `docs/audits/dashboard-autopr-conflict-rootcause-2026-06-21.md` (+ new audits index).

## ⚑ Self-initiated
Owner gave a broad autonomous mandate ("figure out the problem… fixes, ideas, anything of value")
while away. The generator-determinism + `branch`-removal + workflow self-heal fixes are promoted
under Q-0172; the pr-auto-update header fix was a parked owner-agreed step. Flagged for review.

## 💡 Session idea
**A CI guard that fails when a *committed generated artifact* embeds a wall-clock timestamp or host
branch name.** The whole #1261 class came from volatile metadata baked into a tracked file. A tiny
check (extend `check_generated_artifacts_fresh`) could scan registered artifacts for an ISO timestamp
that equals "now ± a few seconds" or a `branch`-like field, and warn "generated artifacts must be a
pure function of committed source." It turns "someone committed wall-clock into VCS" from a
rediscovered-the-hard-way bug into a named signal. (Dedup-checked `docs/ideas/` — not present.)

## ⟲ Previous-session review
The previous chain (the #1260 PR-mergeability work) correctly built the *git-truth* tooling but
framed the dashboard PRs as part of the same "false-dirty" story. This session's value was
**separating the two**: #1261 is a *genuine* conflict with a concrete root cause (volatile generated
metadata), and conflating it with the GitHub-flakiness issue would have led to the wrong fix. Lesson:
when two symptoms look alike ("a PR is dirty"), verify each against git ground truth *before*
assuming a shared cause — the conflict-guard + `check_pr_mergeable.py` are exactly the tools for that,
and they paid off here. System improvement filed above (the volatile-artifact guard).
