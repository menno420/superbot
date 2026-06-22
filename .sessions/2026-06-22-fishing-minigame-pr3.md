# 2026-06-22 — Fishing minigame PR3: the rod ladder (the orthogonal progression axis)

> **Status:** `in-progress` — born-red card. Owner-directed implementation (Q-0175 fishing
> minigame, continuing after #1298/#1299). The rod ladder: buy better rods with coins; each tier
> turns the 4 knobs the sim recommended.

## Arc (what I'm about to do)

PR1 shipped the reel; PR2 the trophy reel-fight. The design's progression model is **two
orthogonal axes**: *fishing level* = what you can catch (size bands, via `game_xp`); *rod* = how
well / which-within-band you catch it. This PR3 adds the **rod ladder** as that second axis.

**Acquisition decision (my pick, easily tunable):** rods are **bought with coins**. Fish are already
sellable (#1289), so this gives those coins a finite, healthy sink and the catch→sell→upgrade loop
the design doc called for. A strict 5-tier ladder (`starter → bronze → silver → gold → diamond`);
each tier requires the previous + a coin price. Prices are constants, flagged for owner tuning.

This PR:
1. **Domain** `utils/fishing/rods.py` — the 5-tier `Rod` ladder (the sim's 4 knobs: `window_bonus`,
   `bite_speed`, `rarity_pull`, `escape_resist`) + prices. Pure.
2. **Persistence** — migration `087_fishing_rod.sql` (`fishing_rod` table, per user+guild tier) +
   `utils/db/games/fishing_rod.py` (`get_rod_tier`/`set_rod_tier`) + re-export, mirroring the
   catch-log pattern.
3. **Purchase** — `fishing_workflow.buy_rod` (audited coin debit via `economy_service.debit_in_txn`
   + `set_rod_tier` in one txn + balance event after commit), mirroring `mining_workflow.vault_upgrade`.
4. **Wire the knobs** — `roll_cast` applies `rarity_pull` (new param on `rewards.roll_catch`); the
   cast view applies `window_bonus` (longer reaction window), `bite_speed` (faster bite), and
   `escape_resist` (the already-present fight knob). The cog fetches the equipped rod once and
   threads it through.
5. **UI** — `!rod` shows the ladder + your tier with an **Upgrade** button (`RodShopView`); buys the
   next tier.
6. **Tests** — rods domain, the purchase workflow, rarity-pull weighting, the rod-aware view, the cog.

**Deferred to PR4+:** energy pacing + sell-value rebalance, boat/deepwater venue, the fishing-gear
loadout preset (Q-0175).

## Shipped

_(filled in at close)_
