# 2026-06-24 — Route `!syncslash global` through the diff-gated auto-sync helper

> **Status:** `in-progress`

## Goal (dispatch run, self-initiated idea→ship promotion, Q-0172)

Empty scheduled fire → advance a real plan slice. Promoting the **previous
session's Q-0089 session idea** (`.sessions/2026-06-24-command-tree-auto-sync.md`),
which survives the sniff test: **route the manual `!syncslash global` through the
new diff-gated `command_tree_sync.auto_sync_if_changed`** instead of an
unconditional `tree.sync()`.

Why it's worth shipping:
- Retires the **last unconditional global `tree.sync()`** in the codebase — one
  implementation, one place to reason about the global-sync rate limit.
- Gives operators a **live-vs-local diff preview** ("+N added / -M removed")
  before/instead of burning a sync, and a clean "already in sync — skipped"
  outcome.
- Adds an explicit **`force`** escape (`!syncslash global force`) for "sync
  anyway" (param/description-only changes the path-diff deliberately misses).

Contained, reversible, test-covered. The guild/clear scopes are unrelated
(guild-local `copy_global_to` / `clear`) and stay as-is.

## Plan
- [ ] Route `!syncslash global` through `auto_sync_if_changed`; report the
      SyncOutcome (synced / unchanged / fetch_failed / sync_failed) with the diff.
- [ ] Add a `force` modifier → unconditional `tree.sync()` (the old behaviour,
      explicit) for cosmetic-only changes.
- [ ] Tests for both branches + the unchanged/failed outcomes.
- [ ] `check_quality --full` green + arch strict.

## ⚑ Self-initiated (Q-0172)
Promoted the previous run's Q-0089 idea (manual-sync unification) to a build with
no dispatch/owner ask. Reversible; flagged here for owner review.
