# 2026-06-22 — Mining: fish cooking + sellable fish (energy refill via campfire)

> **Status:** `in-progress` — building the fish↔energy bridge (cook at a campfire + sellable fish).
> Born-red card (Q-0133); flipped to `complete` as the final step.

## Arc (what I'm about to do)

The final piece of the owner's mining-balance directive (after #1284 sim, #1286 rebalance+energy):
energy should also be refillable by **cooking/eating fish**. Owner decisions (AskUserQuestion,
2026-06-22): **(1) cook at a campfire structure** (a build gate before fish-energy), and **(2) fish
are both energy-source AND sellable for coins** (resolving the Q-0175 open "what are fish for?").

This session:
1. **Raw fish become inventory items** — on catch, `fishing_workflow.fish` also grants the species to
   the mining inventory (catch-log retained for the dex). Fish enter the shared catalog as sellable
   `RESOURCE`s (value scales modestly with `size_rank`).
2. **Campfire structure** — a new entry in the generic `mining_structures` registry (no migration; reuses
   the Forge/Home table). `!build campfire` (coin + material sink); gates cooking.
3. **Cook → eat** — `!cook <fish>` (requires a built campfire) converts a raw fish → a generic
   `cooked fish` food item; `!use cooked fish` restores energy (+30, via `energy.RESTORE_VALUES`).
4. Sell works through the existing `!sell` (fish are `RESOURCE`s).

No migration. Balance caveat to flag: fishing is currently unpaced, so fish sell value is kept low
(documented). Tests + arch + docs; the mining-economy doc's "fish refill = follow-up" note → done.
