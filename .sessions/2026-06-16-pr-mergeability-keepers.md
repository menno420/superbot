# 2026-06-16 — PR mergeability keepers: auto-update behind + red-on-conflict

> **Status:** `in-progress` — born-red session card (Q-0133). Flip to `complete` as the last step.

## Intent (what this run is about to do)

Follow-up to PR #959 (same session). The #959 stall surfaced a real gap the owner flagged: a
behind/conflicted PR sits **green-and-stuck**, not red-and-actionable — the "forgotten PR" rot the
loop was meant to kill. GitHub doesn't turn a conflict/behind state into a failed check, and native
auto-merge won't auto-update a behind branch (no merge queue). Owner greenlit **both** halves
(Q-0154):

- **`.github/workflows/pr-auto-update.yml`** — on `push: main`, bring open `claude/*` PRs that are
  `BEHIND` up to date (`update-branch`) so they re-test and auto-merge; a true conflict fails the
  update and is left for the guard. (Would have prevented the #959 stall.)
- **`.github/workflows/pr-conflict-guard.yml`** — on `push: main` + `pull_request` + schedule, post
  a **red `conflict-guard` commit status** on any `DIRTY` PR (clear to green when resolved). A
  conflict now goes visibly RED for an agent / the owner to act on. Non-required (visibility, not an
  extra gate → no branch-protection change needed).

Supporting: Q-0154 in the router; a "PR mergeability keepers" section in `autonomous-routines.md`.
