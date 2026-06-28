# 2026-06-28 — Fishing: the "pearl" rare-material drop + a premium-bait pearl craft

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What I'm about to do

Empty-fire dispatch. S1's first ▶ Next-startable item names the offline successor explicitly:

> ▶ **Next offline successor:** extend the same caught-fish craft pattern to … a **fish-loot
> rare-material drop** (a dedicated craft material, not just a double fish). Pure + sim-pinnable,
> self-mergeable.

(The rod-ladder craft path the same bullet offers as the alternative already shipped in #1515.)

**The slice — the "pearl" 🦪, a rare fishing material with a real, repeatable sink:**

1. **Drop** — a successful reel can also yield a **pearl** (a dedicated inventory item, *not* a
   fish / dex row), at a chance that scales with the caught fish's `size_rank` (bigger fish → better
   odds). Pure roll in `utils/fishing/rewards.py`, sim-pinned, byte-identical when it doesn't fire.
2. **Sink (repeatable, no dead-item)** — a **pearl-only recipe** crafts the premium **Royal Feast**
   bait, the one bait deliberately left with *no* fish-craft path (a pure coin sink today). Pearls
   give it a gameplay-native, repeatable earn path (bait is consumed, so pearls never go dead);
   coins stay the fast alternative. Mirrors `craft_bait` exactly.
3. **Surface** — the catch message announces a pearl, the bait shop shows the pearl recipe + your
   pearl count, and `!craftpearl` / a bait-shop select crafts the feast.

No DB migration (pearls reuse the generic `mining_inventory` item store). Offline + sim-pinned;
self-mergeable on green.

## What shipped

_(filled at close)_
