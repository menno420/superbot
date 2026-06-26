# 2026-06-26 — Sector ▶ Next freshness guard (S3 mechanism)

> **Status:** `in-progress`
> **Run type:** routine · dispatch
> **Branch:** `claude/funny-franklin-867vhz`

## What I'm about to do
Autonomous dispatch fire (no work order). S2's offline anchor tail is exhausted (needs prod
creds); the cleanest offline, self-mergeable slice is S3 self-improving-engine mechanism work.

While orienting I hit a real drift class: `docs/current-state/S3-ai-memory.md` ▶ Next lists
"Consistency-linter AI-nav PR 1" linking a plan that is already **SHIPPED / `historical`**
(#1376). A ▶ Next that points at finished work misdirects the next dispatch run to rebuild it.

Slice (S3):
1. `scripts/check_sector_next_freshness.py` — read-only stdlib guard that flags any
   `▶ Next` item in `docs/current-state/S*.md` linking a `historical`-status plan.
2. Fix the live S3 stale pointer (Q-0166 fix-on-sight).
3. Tests under `tests/unit/scripts/`.

CI mirror + arch strict must be green before flipping this card to `complete`.
