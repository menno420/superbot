# 2026-07-01 — Fishing Tide Pool structure (coral structure-target sink)

> **Status:** `in-progress`
<!-- born-red flow (Q-0133): `in-progress` while open; flipped to `complete` as the final close step. -->

**Branch:** `claude/funny-franklin-4n38rf` (restarted from origin/main #1597).
**Run type:** routine · dispatch

## What this run is doing

Empty scheduled fire → advance the next plan slice. The S1 sector's explicit `[offline]`
"▶ Next offline successor" for the fishing rare-material arc is *"a second curio tier or a
**structure-target variant** (a deepwater material that builds a fishing structure rather than a
collectible)."* Building the **structure-target variant**: the **Tide Pool** — a coral-built
mining-structure (generic `mining_structures` table, no migration) that gives coral its first
**functional** sink (complementing the cosmetic curios), granting a small passive rarity-pull
bonus folded as the fishing cast's 5th knob (default 1.0 when unbuilt ⇒ byte-identical).

Reuses the Forge/Home/Campfire structure pattern end-to-end (registry entry + audited
`mining_workflow.build_structure` + panel), and the existing `EffectiveStats`-style additive-safety
property already used by fishing gear.
