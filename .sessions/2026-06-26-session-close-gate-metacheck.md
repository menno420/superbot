# 2026-06-26 — Meta-check: every "run-at-close" checker must be wired into /session-close

> **Status:** `in-progress`
> **Run type:** routine · dispatch
> **Branch:** `claude/funny-franklin-kmsak8`

## What I'm about to do (born-red declaration, Q-0133)
Scheduled dispatch, empty work order → take the next plan slice. Building the previous
run's Q-0089 session idea (PR #1477): a tiny meta-check `scripts/check_session_close_gate.py`
that asserts every checker declared a **session-close gate** is actually referenced in the
`/session-close` SKILL.md Step-4 block — so a guard authored "to be run at close" can't
silently lack an invocation site (the exact drift class #1476/#1477 hit: a checker that
exists but nobody runs). S3 mechanism work, fully offline, self-mergeable on green.

Plan: a distinctive `[session-close-gate]` sentinel marker retrofitted onto the Step-4
checkers + the meta-check enforcing sentinel⟹referenced (and referenced-file-exists) +
unit tests + a `/session-close` Step-4 entry that runs the new gate (self-referential
closure).
