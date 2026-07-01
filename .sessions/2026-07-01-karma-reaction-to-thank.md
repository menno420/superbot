# 2026-07-01 — Karma reaction-to-thank (completion-first deepening)

> **Status:** `in-progress`
<!-- born-red flow (Q-0133): `in-progress` while open; flipped to `complete` as the final close step. -->

**PR:** (opening) — Karma reaction-to-thank.
**Branch:** `claude/funny-franklin-jqv6ne` (from origin/main #1619).
**Run type:** `routine · dispatch`

## What this run is doing

Empty scheduled fire → advancing the next plan slice. Recent runs have been fishing-structure
heavy; diversifying to a **non-fishing** completion-first deepening. Picking the **Karma** unit's
rubric-C **"React-to-thank"** box (cert `units/karma.md` punch-list #2 sub-item) — a named
best-in-class gap (Carl-bot has it), self-contained and offline.

Plan: add an opt-in per-guild **trigger emoji** setting; a `on_raw_reaction_add` listener in
`KarmaCog` grants karma to the reacted message's author through the **existing audited
`karma_service.give(source="reaction")` seam** (the service already documents `"reaction"` as an
anticipated source — no new mutation path; all anti-abuse: self-give guard, cooldown, daily cap
reused for free). Default off ⇒ byte-identical for existing guilds.

## Shipped

(to be filled at close)
