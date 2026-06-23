# 2026-06-23 — Fishing trophy follow-ups: soft-fail clue + heaviest-catch leaderboard

> **Status:** `in-progress` — born-red session card (Q-0133). Flip to `complete` last.

> **Run type:** `routine · dispatch`

## What I'm about to do

Second slice of this dispatch run, now unblocked by PR #1351 (trophy records, merged). Both
build directly on the merged weight seam — captured as #1351's 💡 session idea, the fishing
design's §"Other ideas":

1. **Soft-fail clue** ("a big one got away") — when a *trophy* fish escapes the reel, the cast
   view names it (`minigame.escape_clue`) so the loss baits the next cast instead of a flat
   denial. Ordinary fish keep the plain line.
2. **Heaviest-catch leaderboard** — `!trophies` (aliases `bigfish`/`fishtrophy`): the server's
   biggest catches off the `best_weight` column #1351 added (`db.top_trophies`, `ORDER BY
   best_weight DESC`), so trophies compete server-wide.

Additive — no money/safety seam (ADR-002 game-state). Tests across minigame/db/cast-view.

## What shipped

_(filled in at close)_
