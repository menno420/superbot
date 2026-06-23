# 2026-06-23 — Fishing bait-crafting (close the catch→cook→bait economy loop)

> **Status:** `in-progress` — born-red card (Q-0133). Routine · dispatch (empty-fire
> schedule; promotes the `fishing-bait-crafting-2026-06-22` idea → build, Q-0172).
> PR auto-merges on green (Q-0123) once flipped `complete`.

## What I'm about to do

Empty-fire dispatch run. Product lanes that need creds/browser/network are gated
(BTD6 live battery · botsite PR 2 cutover · Project Moon ingest), so I'm promoting
the cleanest fully-offline-testable S1 idea — **bait crafting from caught fish**
([idea](../ideas/fishing-bait-crafting-2026-06-22.md)) — to a shipped build. It
builds directly on the just-shipped bait layer (#1329/#1337) and the cook/campfire
loop (#1289): small caught fish become a *gameplay-native* second source of bait
beside the coin shop, closing `catch → craft → bait → bigger catch`.

Scope:
1. `utils/fishing/bait.py` — pure `BaitRecipe` map (small fish → bait pack), helpers.
2. `services/fishing_workflow.py` — `craft_bait` workflow op (debit fish + load bait
   in ONE transaction, mirroring `cook` / `buy_bait`; no coin debit — inventory→bait).
3. `views/fishing/bait_shop.py` — a "Craft from fish" select + recipe field on the panel.
4. `cogs/fishing_cog.py` — `!craftbait [bait]` surface.
5. Tests across utils + workflow.
