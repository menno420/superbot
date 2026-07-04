# 2026-07-04 — Open-PR review + merge sweep

> **Status:** `in-progress`
> **Branch:** `claude/review-open-prs-1k48kg` · **PR:** (opens with this commit)

## Intent

Owner-directed: review **all 13 open PRs** and drive each to a terminal state (merged or
closed), improving contents where necessary:

- **#1509** — Codex unfinished-work audit doc (2026-06-27; a week stale — verify against
  shipped source per Q-0120 before merging).
- **#1555–#1560** — six dependabot dependency bumps (fastapi/dashboard, python-minor-patch
  group, openai, pillow major, asyncpg, prometheus-client). Check CI + runtime-pin policy,
  merge what's green and safe.
- **#1695–#1699** — five Codex rebuild-planning review docs (2026-07-03). Verify claims
  against source, fix drift, merge.

Close-out (idea · previous-session review · docs audit) lands in this file before the badge
flips to complete.
