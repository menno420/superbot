# Session: Trim the no-op `continue`-issue clause from the dispatch prompt

> **Status:** `complete` — born-red card flipped (Q-0133); single-push docs fix.

**Branch:** `claude/dispatch-prompt-continue-trim-2026-06-15` · **Date:** 2026-06-15 · **Type:** docs (S3) · **Trigger:** owner-directed in-session

## What shipped

Follow-up to Q-0145. The dispatch prompt's step 8 still told the routine to "open a `continue`
issue *if a continuation trigger is wired*" — a no-op in the 2-routine world (dispatch is fired by
Hermes' VPS cron, nothing consumes `continue` issues since the night-executor was retired), and a
mild risk (a literal routine could open orphan issues nobody services). Owner asked to remove it for
clarity. Replaced the silent conditional with a positive instruction: the handoff IS sharpening
▶ Next action (the next Hermes-cron dispatch reads it from live state); **do NOT open a `continue`
issue**. Docs only; `check_docs --strict` ✓.

## 💡 Session idea (Q-0089)

Covered by the standing Q-0089 idea from this session's earlier slices (the routine-prompt
consistency guard `check_routine_prompts.py`) — a guard like that would have flagged this stale
no-op clause automatically. No new idea forced (Q-0089 bar).

## ⟲ Previous-run review (Q-0102)

#900 (the Q-0145 merge) correctly consolidated to 2 routines but left this one residual clause from
the old 3-routine self-chaining model — a small reminder that when you retire a mechanism (the
`continue`-issue trigger), you must sweep the *instructions that assumed it*, not just the routine.
This trim closes that residue.
