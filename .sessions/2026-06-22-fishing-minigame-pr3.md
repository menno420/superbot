# 2026-06-22 — Fishing minigame PR3: the rod ladder (the orthogonal progression axis)

> **Status:** `complete` — rod ladder shipped & verified (full CI mirror green, 11,598 tests).
> Owner-directed implementation (Q-0175, continues #1298/#1299). PR #1301 → auto-merges on green (Q-0191).

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

## Shipped (PR #1301)

- **Domain** `utils/fishing/rods.py` — the 5-tier `Rod` ladder (Bare → Bronze → Silver → Gold →
  Diamond) with the sim's 4 knobs + prices (0 / 250 / 750 / 2000 / 5000 🪙). `rod_for_tier` (clamped),
  `next_rod`, `STARTER`, `MAX_TIER`.
- **Persistence** — migration `087_fishing_rod.sql` (`fishing_rod(user_id, guild_id, tier)`) +
  `utils/db/games/fishing_rod.py` (`get_rod_tier`/`set_rod_tier`, conn-aware) + `utils.db` re-export,
  mirroring the catch-log.
- **Purchase** — `fishing_workflow.buy_rod`: audited coin debit (`economy_service.debit_in_txn`,
  reason `fishing:rod_purchase`) + `set_rod_tier` in ONE txn + `EVT_BALANCE_CHANGED` after commit;
  insufficient-funds rolls back; at-max is a no-op. Plus `get_rod` (equipped rod) + `RodPurchaseResult`.
- **Knobs wired** into the minigame: `rewards.roll_catch` gained `rarity_pull` (flattens the
  inverse-size weighting toward the big end, clamped ≥1); `minigame.roll_bite_delay` gained `speed`;
  the cast view applies `window_bonus` (every reaction window = `REACTION_WINDOW + bonus`),
  `bite_speed`, and `escape_resist`. The cog fetches the equipped rod once and threads it through
  `roll_cast` + the view. Starter rod still catches fine (all knobs neutral).
- **UI** — `!rod` (aliases `rodshop`/`buyrod`): a `RodShopView` (`BaseView`) showing the ladder +
  your tier + the next price, with an **Upgrade** button calling `buy_rod` and re-rendering. Help
  hook + dashboard regenerated (commands 370→371).
- **Tests** — rods domain (6), rod db CRUD (3), buy_rod + rarity-pull-threading + get_rod (6),
  rarity-pull bias + clamp (2), bite-speed (1), view window-scaling (1); existing workflow tests
  updated for the new `rarity_pull` kwarg + the now-present economy import. Full CI mirror green.

## Session enders

- **💡 Session idea (Q-0089):** *Rod-aware "what changed" diff on upgrade.* The `!rod` upgrade
  result could show a tiny before/after of the *felt* effects ("reaction window 2.5s → 2.9s · bites
  ~12% faster · escapes 22% → 35% resisted") so the abstract knobs read as concrete improvements —
  upgrades should *feel* earned. Cheap (the `Rod` deltas are pure). Logged here.
- **♻ Grooming (Q-0015):** advanced the fishing minigame down its lifecycle — the design's
  two-axis progression (level + rod) is now real; the rod ladder closes the catch→sell→upgrade loop
  the design doc + #1289 set up. Games folio reflects PR3; remaining slices (energy/sell rebalance,
  boat) named for PR4+.
- **⟲ Previous-session review:** PR2 (#1299) left `escape_resist` as a *defaulted-0 parameter* on the
  escape helpers specifically so this PR could turn it with zero churn — that paid off exactly as
  intended (the rod just passes `escape_resist=rod.escape_resist`). Good forward-seam discipline,
  the very thing PR2's own review flagged it had *missed* on the reel button. **What PR3 had to
  retrofit:** PR1's workflow test asserted `not hasattr(wf, "economy_service")` to pin "fishing is
  free" — a too-broad invariant that broke the moment fishing gained *any* economy touch (rod
  buying). **System note:** pin invariants on *behaviour* (this flow debits no coins), not on
  *module shape* (this module never imports economy) — the latter is brittle to legitimate growth.
- **🧾 Doc audit (Q-0104):** games folio updated; `check_docs --strict` ✓; dashboard/site artifacts
  regenerated (new `!rod` command); migration `087` follows the numbering contract. Ledger
  auto-updates on merge. Nothing left only in chat.

## ⚑ Self-initiated: none — owner-directed implementation ("Continue from where you left off" → the
   next planned slice, PR3 rod ladder). The rod *acquisition model* (buy-with-coins) was my pick from
   a sensible default (flagged in the PR for owner tuning), not an unprompted scope expansion.
