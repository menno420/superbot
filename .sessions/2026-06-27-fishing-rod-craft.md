# 2026-06-27 — Fishing fish→rod craft path

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What this run is about to do
Empty-fire dispatch (no work order). Taking the explicit S1 `▶ Next offline successor` named in
`docs/current-state/S1-bot.md` after the fishing-charm craft (#1508): **extend the fish→item craft
pattern to the rod ladder** — a `craft_rod` path so a dedicated fisher can earn rod upgrades by
fishing (consume caught fish, smallest-first) instead of only buying them with coins, exactly
mirroring `craft_charm`/`craft_bait`. Coins stay the fast alternative; crafting is the slower,
gameplay-native path (no arbitrage — the fish consumed sell for far less than the rod's coin price).

Deepens an existing feature (fits the Q-0209 completion-first posture). Pure + sim-pinnable +
offline self-mergeable.

Planned changes:
- `utils/fishing/rods.py` — `RodRecipe` + `ROD_RECIPES` (keyed by the tier it crafts into) +
  `rod_recipe`/`rod_recipe_text` (pure).
- `services/fishing_workflow.py` — `RodCraftResult` + `craft_rod` (inventory-only conversion, one
  transaction, no coins/audit — matches `craft_charm` and `set_rod_tier` being plain CRUD).
- `cogs/fishing_cog.py` — `!craftrod` (aliases `rodcraft`).
- `views/fishing/rod_shop.py` — a "🎣 Craft from fish" button + the craft cost in the embed.
- Tests + `docs/planning/fishing-rod-craft-numbers-2026-06-27.md`.
