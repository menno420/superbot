# Session — make the settings.json hooks cwd-robust (Q-0150)

> **Status:** `in-progress`

## What this is

Owner-directed in-session (the maintainer asked for an explanation of the cwd-deadlock, then said
"yes go ahead"). Third PR of this dispatch run (after #945 permission allow-list, #946 §7.5
cost-comparison floor). Applies the durable fix the journal's cwd-deadlock entry had been pointing
at, under the Q-0106 in-session exception. Provenance: **Q-0150**.

## The trap (why)

Hook commands in `.claude/settings.json` used **relative** `scripts/<hook>.py` paths. The Bash tool's
cwd persists across calls, so a stray `cd <subdir> &&` leaves cwd in the subdir; the PreToolUse hooks
(Bash + Edit|Write) then resolve `<subdir>/scripts/<hook>.py`, FileNotFound, exit non-zero → the
harness blocks the tool. All three mutating tools share the hooks → full session deadlock (hit live
this run; the worktree-agent symlink rescue got me out).

## Fix (applied)

Prefix every hook command with `cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}" &&` —
prefers the documented hook env var, falls back to `git rev-parse --show-toplevel` (load-bearing:
`$CLAUDE_PROJECT_DIR` was observed **empty** in-shell here). Resolves the repo root even from a stuck
subdir; runs in the hook's own subshell so it never affects the tool cwd. All 7 hook commands updated.

## Plan

- `.claude/settings.json` — 7 hook commands wrapped (done).
- Router **Q-0150** provenance + `.session-journal.md` entry marked "durable fix applied" (done).
- Verify: JSON valid · each wrapped script exits 0 from a stuck `disbot/` cwd · `check_docs --strict`.
