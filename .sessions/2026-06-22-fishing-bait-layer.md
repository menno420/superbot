# 2026-06-22 — Fishing Bait economy layer

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What I'm about to do

Empty-fire dispatch run. Building the **Bait** layer for the fishing minigame — the
design doc's named "second economy knob" follow-up
([fishing-minigame-design](../docs/planning/fishing-minigame-design-2026-06-22.md) §4 +
the open-world expansion plan). Bait is an optional, coin-bought consumable that biases
the catch toward rarer/bigger fish for N casts — a coin sink (fish are now sellable/cookable
since #1289, so coins need somewhere to go) and a pre-cast decision beside the rod.

Mirrors the existing fishing seams house-style: a pure catalog (`utils/fishing/bait.py`,
like `rods.py`), DB state (`utils/db/games/fishing_bait.py` + migration 090, like
`fishing_rod`/`fishing_energy`), an audited coin-sink workflow op (`fishing_workflow.buy_bait`,
mirroring `buy_rod`) + per-cast consumption applied to `roll_catch`'s `rarity_pull`, a
🪱 Bait shop/panel view (mirroring `RodShopView`) + menu button, and a `!bait` command.

Slice is contained, reversible, test-covered; ships on green CI.
