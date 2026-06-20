# 2026-06-20 — SessionStart branch-freshness warning (stop the stale-branch foot-gun at restart)

> **Status:** `in-progress`

## Arc

Owner-directed in-session. The owner *"often has to restart a session multiple times in one chat"*
(long reply gaps), so PRs merge between restarts and the branch silently goes behind/divergent —
which then trips the post-squash-merge rebase foot-gun (it bit this very chat three times across the
#1185/#1187/#1188 work). The reactive guards (#1187 conflict-guard, #1188 auto-update) catch this
*after* a PR exists; the missing piece is a **proactive** warning at the moment a session restarts.

The existing `scripts/check_branch_freshness.py` already warns on Stop + pre-push, but **not at
SessionStart** — exactly the restart moment. This wires it there.

## What this PR adds

- **`scripts/check_branch_freshness.py`** — new `--event sessionstart` mode: a concise
  `N behind / M ahead of origin/main` verdict (time-boxed `git fetch`, exit 1 when behind, exit 0
  otherwise / on main / detached). The `ahead` count lets the agent tell a purely-behind branch
  (safe to reset) from a divergent one (already-squash-merged old commits, or real unpushed work).
- **`scripts/claude_session_summary.py`** — the SessionStart banner now calls it and prints a loud
  `⚠ STALE BRANCH` block with the safe sync command when behind, or a quiet `Fresh : up to date ✓`
  line on a current feature branch. Fail-silent.
- **Router Q-0188** — provenance for the in-session executable-config edit (the live-owner exception).

## Why a warning, not auto-sync

Auto-`reset --hard` in a hook would discard uncommitted work — the exact data-loss foot-gun seen
earlier this chat. The banner surfaces the state + the `ahead` count so the agent judges and acts.

## Verification

- Dogfooded: on this branch *while it was 1-behind/2-ahead* (post-#1191 merge), the banner printed
  the `⚠ STALE BRANCH` block correctly; after syncing to main it reads `up to date ✓` (exit 0).
- `check_quality.py --check-only` → all green.

## Shipped

_(filled at close)_
