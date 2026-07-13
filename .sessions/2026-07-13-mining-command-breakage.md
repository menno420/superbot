# 2026-07-13 — Fix `!mine` breakage: str user_id passed to a BIGINT-keyed read

> **Status:** `in-progress`
> **Branch:** `claude/mining-command-breakage-ypve0d` · **PR:** pending
> **Venue:** remote container (owner-directed from a Discord screen-recording). **📊 Model:** Opus 4.8 (Claude Opus family).
> **Scope:** one-line runtime bug fix in `build_grid_embed` + a durable regression guard. No schema, no cross-cutting change.

## What I'm about to do

The maintainer's screen-recording shows `!mine` replying **"⚠️ An unexpected error occurred. Please try again."**
while the Mining Hub and all its buttons work. Root-caused it (see Arc); shipping the fix + a test that
would have caught it.

## Arc

_(filled in at close)_
