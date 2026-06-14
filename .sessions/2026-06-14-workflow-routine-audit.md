# Session: workflow-routine audit — tools, Hermes, routines, loop health

> **Status:** `in-progress` — born-red merge gate (Q-0133). Flip to `complete` as the final step.

**Branch:** `claude/modest-ptolemy-2xipoh` · **Date:** 2026-06-14 · **Type:** owner-directed review (manual)

## What I'm about to do
Owner-requested workflow-health review session. Verifying:
1. Repo-navigation tools (CodeGraph, Grimp, ≥3 active) work + are correctly documented.
2. Hermes integration state — what's wired vs pending; the "sensitive information" dispatch problem.
3. Autonomous routines — why they fire at the wrong times (timezone? lag? not firing?).
4. My opinion on the loop (20-PR reconciliation cadence — widen or keep?) + any unclear workflow points.

Doc fixes expected: correct verified drift in `docs/operations/autonomous-routines.md` control-plane
state table (evidence-backed live verification), plus a GitHub-Actions-cron-lag note.

(Findings + close-out written here as the final step.)
