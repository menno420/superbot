# Session — `check_loop_health.py` gh-absent REST fallback

> **Status:** `in-progress`
> **Branch:** `claude/funny-franklin-3m7tvn`
> **Run type:** `routine · dispatch`

## What I'm about to do

Scheduled dispatch fire, no work order → advance the next ungated plan slice. Executing
[`planning/loop-health-gh-fallback-plan-2026-06-20.md`](../docs/planning/loop-health-gh-fallback-plan-2026-06-20.md)
(promoted from an idea by the band-#1170 reconciliation pass, Q-0172): give
`scripts/check_loop_health.py` a stdlib-`urllib` GitHub-REST fallback so the control-plane
ROUTINE_PAT row is verifiable **by the script** in the routine container (where `gh` is absent),
not only by a manual MCP read. Ungated, disposable tooling (Q-0105), self-merge on green.

Born-red card (Q-0133) — flipped to `complete` as the deliberate last step.
