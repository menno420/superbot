# Idea — Bait crafting from caught fish (close the fishing economy loop)

> **Status:** `ideas` · **Subsystem:** games (fishing) · **Captured:** 2026-06-22
> (the bait-layer dispatch run, PR #1329). Builds directly on the now-shipped
> bait layer + the cook/campfire loop (#1289).

## The idea

Let the existing cook/campfire loop (#1289) also turn **small / common caught
fish into bait**, so the fishing economy loops back on itself instead of bait
being a pure coin sink:

```
catch small fish ──▶ craft into bait ──▶ load bait ──▶ catch bigger fish ──▶ …
```

Today (PR #1329) bait is bought **only** with coins. Crafting adds a second,
gameplay-native source: your throwaway minnows become the lure that lands the
trophy. It gives the low-size-rank fish — which otherwise just sell cheap — a
second use, and rewards *fishing* (not just spending) with better fishing.

## Why it's worth having

- **Closes the loop:** catch → cook/craft → bait → bigger catch is a self-feeding
  cycle, the texture good idle/collection games have.
- **Reuses shipped seams:** the campfire/cook surface (#1289), the bait catalog +
  `fishing_workflow.buy_bait` / `set_active_bait` (#1329), the inventory grant
  already used for caught fish. A `craft_bait` workflow op mirrors `buy_bait` but
  debits fish items instead of coins.
- **Gives small fish a purpose** beyond a low sell price (the #1289 values were
  kept deliberately cheap).

## Sketch (not a plan yet)

- A recipe map (`utils/fishing/bait.py` or a sibling): e.g. *3 × any size-rank-1–3
  fish → 1 Worm Bait pack*, scaling up to rarer baits needing bigger/more fish.
- `fishing_workflow.craft_bait(user, guild, bait_key)` — debit the fish items via
  the inventory seam + load the bait, one transaction (audited like the purchase).
- A "Craft" affordance on the 🪱 Bait shop panel (or the campfire), beside Buy.

## Related

- [fishing-minigame-design](../planning/fishing-minigame-design-2026-06-22.md) §4
  (bait layer, shipped #1329) · [fishing-open-world-expansion-plan](../planning/fishing-open-world-expansion-plan-2026-06-18.md)
  (Q-0175 vision) · the cook/campfire loop (#1289).
