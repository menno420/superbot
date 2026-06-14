# Session: routine_fire.py — robust Claude Code dispatch helper

> **Status:** `in-progress`

**Branch:** `claude/hermes-routine-fire` · **PR:** TBD · **Date:** 2026-06-14 · **Type:** ops/dispatch bugfix (manual)

## What I'm about to do
Live-testing Hermes' new operating prompt, Hermes diagnosed a REAL bug: the dispatch skill's inline
`curl -d "$(python3 -c ... "$WORK_ORDER")"` is shell-quoting-fragile for multi-line work orders, and
tried to fix it by writing `scripts/hermes/routine_fire.py` itself — which crosses its docs-only
write boundary (Q-0140: code → dispatch to Claude Code). Correct resolution, wrong hands. Build the
helper properly here (the canonical version): `scripts/hermes/routine_fire.py`, stdlib-only, reads the
work order from **stdin** (zero shell quoting), loads `CLAUDE_ROUTINE_*` from env or
`~/.hermes/routine.env`, POSTs `{"text": …}`, prints the session URL, never prints the token,
`--dry-run` to preview. Point `dispatch.md` STEP 4 at it + regen SKILL.md + test. Route the
"may Hermes author its own small tooling scripts?" boundary question to a DISCUSS Q-block.
