# 2026-06-27 — Fishing-gear acquisition depth: fish→charm craft path

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What this run is doing (born-red card)

Empty-fire dispatch. Building the S1 `[offline]` ▶ Next successor to #1504 (fishing-specific gear
stats): the three CHARM-slot fishing charms (`fishing charm`/`anglers charm`/`master angler charm`)
are coins-only today. This run gives them a **non-coin earn path** — a fish→charm craft mirroring the
existing bait-craft seam (`fishing_workflow.craft_bait`): consume caught fish (smallest-first) → yield
one charm in the mining inventory, so a dedicated fisher can earn the whole charm ladder by fishing
(coins stay the fast alternative, exactly like starter mining gear is both buyable and craftable).

Plan: pure `CharmRecipe` ladder in `utils/fishing/gear.py` (sim-pinned) → `craft_charm` in
`fishing_workflow` (reuses `_plan_fish_spend`) → `!craftcharm` command + panel surface → tests +
numbers doc. No DB/migration; offline-verifiable; self-mergeable on green.
