# 2026-06-22 — Mining rebalance + energy system

> **Status:** `in-progress` — applying the sim-pinned rebalance + building the energy mechanic.
> Born-red card (Q-0133); flipped to `complete` as the deliberate final step.

## Arc (what I'm about to do)

Owner-directed follow-up to the mining balance sim (PR #1284, merged). The owner approved applying
the recommended numbers and chose the **energy** frequency brake (NOT a cooldown), refillable by
**cooking/eating fish or consuming boosters**.

This session:
1. **Apply the sim-pinned magnitude rebalance** (pure constants):
   base roll `1-3 → 1-2`, tool curve `×1/2/3/4/5 → ×1/1.2/1.3/1.4/1.5`, cell features
   `60/20/15/5 → 70/10/18/2` (bonanza 25% → 12%), treasure richness `×3 → ×2`.
2. **Build a mining energy system** — a `mining_energy` store (current/max + last-refill clock),
   passive time-based regen, a per-dig energy cost; digging blocks (with a helpful message) at 0.
   Sized to the sim's ~360-digs/active-hour throttle (burst-then-regen feel, not a per-dig wait).
3. **Refill via food/boosters** — eat cooked fish / consume a booster to restore energy, tied into
   the fishing system's catch.

Update the sim's `CURRENT` config + parity test to the new numbers (the design record stays honest).
PR split (A: rebalance + energy core · B: food refill) decided after the fishing/food investigation.
