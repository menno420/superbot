# 2026-06-27 — Sharpen S1 ▶ Next with an offline-startable item (handoff hygiene)

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What I'm about to do

Second slice of this dispatch run (PR #1499 — gear loadout presets — merged). This run surfaced a real
friction: **S1's ▶ Next-startable items are all `[needs-live-bot]` / `[owner]`**, so an empty-fire
dispatch (no live bot) has no clearly-offline S1 lane and must dig for one. The gear-loadout-presets
ship merged its successor idea (`docs/ideas/fishing-gear-stats-2026-06-27.md`, now on main) — an
`[offline]` self-mergeable slice. I'll add it to S1's ▶ Next-startable list so the next empty-fire
dispatch sees an offline S1 lane immediately.

Docs-only; sharpens the live handoff (the dispatch contract's hand-off mechanism).

(close-out filled at the end.)
