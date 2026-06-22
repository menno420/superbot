# 2026-06-22 — Mining rebalance + energy system

> **Status:** `complete` — rebalance + energy core + booster refill shipped & verified.
> Owner-directed → auto-merges on green (Q-0191). PR #1286.

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

## Shipped (PR #1286)

- **Magnitude rebalance** (sim-pinned constants): `rewards.BASE_ROLL_MAX` 3→2; `rewards.mine_multiplier`
  now `1 + power*0.0625` (×1/1.13/1.25/1.38/1.5, was ×1/2/3/4/5); `grid._FEATURE_WEIGHTS` 60/20/15/5 →
  70/10/18/2 + treasure richness ×3→×2. Existing tests updated to the new numbers.
- **Energy system** — pure `utils/mining/energy.py` (settle/spend/restore/seconds_until/bar, all unit
  tested), migration **086** (`energy` + `energy_updated_at` on `mining_player_state`, additive,
  defaults to a full bar), DB accessors `get_energy`/`set_energy` (the latter on the RS02 write-boundary
  ratchet). `mining_workflow.dig` checks/spends energy in the txn; out of energy → blocked with a "rest
  or eat" hint. Grid embed shows an `⚡ Energy` bar.
- **Booster refill** — `ration` (+25) / `energy drink` (+50) consumables (`items.py`) buyable from the
  market (`GEAR_SHOP`, a coin sink); `mining_workflow.use_item` eats them to restore energy (consume +
  raise in one txn; refuses at full).
- **Sim + doc kept honest** — `tools/game_sim/mining_economy_sim.py` gained `PRE_REBALANCE` (the
  diagnosed "before") and an energy-throttle-aware `CURRENT` (mirrors live; verdict now BALANCED);
  parity tests updated; the design doc gained an "Applied" section.

Verified: `check_quality.py --full` green (11,505 passed), arch strict clean (pre-existing WARNs only),
docs strict clean.

## Findings / decisions

- **Fish cooking is the NEXT PR, not this one.** Fishing v1 is built but caught fish live in a
  collection log (`fishing_catch_log`), not the inventory — "cook/eat fish" needs a bridge
  (cook logged catches → an edible item). This PR ships the **booster** refill path (rations/energy
  drinks); the fish↔energy bridge is the follow-up. The owner asked for both; boosters land first.
- **Decisions made alone (owner should sanity-check):** MAX_ENERGY=60, DIG_COST=1, regen +1/10s
  (=360/active-hr, = the sim throttle), ration +25 / energy drink +50, market prices 20/40. All
  pinned in `energy.py` + the design doc; tune freely.
- **Merge = deploy (Q-0193):** migration 086 runs on Railway's auto-redeploy at merge; no manual step.

## ⚑ Self-initiated: none

Owner-directed in-chat ("apply them … no cooldown but … energy … refilled by cooking/eating fish or
consuming boosters"). Runtime change, but owner-chosen → no review gate (Q-0191).

## 💡 Session idea (Q-0089)

**A `mining_player_state` accessor is getting crowded — consider a typed `MiningMeta` read.** The row
now carries depth/max_depth/pos/vault_level/title/energy(+ts), each with its own `get_*`, and `dig()`
fires ~6 sequential single-column reads before its transaction. A single
`get_mining_meta(user, guild) -> MiningMeta` (one row read, typed) would cut the read count, make the
"what's on this row?" answer one place, and remove the per-column default duplication. Low-risk, pure
win for the hottest mining path; worth a small refactor PR.

## ⟲ Previous-session review (Q-0102)

**Previous session:** the mining-economy-sim session (PR #1284, this same chat). **Did well:** it
mirrored live constants into the sim *and shipped a parity test* — which is exactly what made THIS
session safe: the moment I changed `mine_multiplier`/feature weights, the parity test told me precisely
which sim mirrors to update, so the design record couldn't silently drift. That foresight paid off one
session later. **Could have done better:** the sim modeled the frequency brake only as a "cooldown"
knob; when the owner picked *energy*, I had to retrofit an energy-equivalence (regen 360/hr ≈ 10s
interval) into `CURRENT`. **System improvement:** a balance sim should model the *mechanism* the game
will actually use, not just an abstract throttle — but the equivalence held cleanly, so the cost was
small. Captured as the session idea below's sibling: keep design sims one step ahead of the chosen
mechanic.

## Context delta (reflection interview)

- **Needed but not pointed to:** that **caught fish are a collection log, not inventory items**
  (`fishing_catch_log`) — the single fact that reshaped "eat fish" into a two-PR bridge. Not in the
  games folio's mining/fishing prose; found by reading the fishing migration + workflow. Worth a line
  in the games folio's fishing section.
- **Pointed to but didn't need:** CodeGraph again — the change was a known set of pure-domain files;
  `context_map` (auto-shown per edit) + the Explore fan-out covered the wiring.
- **Discovered by hand:** the RS02 write-boundary ratchet (`test_mining_write_boundary.py`) requires
  **every new mining write primitive to be registered by name** — `set_energy` had to be added or the
  invariant test fails. The `.claude/rules/mutation-and-db.md` mentions the audited seam but not the
  *name-registration* step; a one-liner there would save the next agent a red test.
- **Decisions made alone:** the energy tunables + the energy-as-cooldown sim modeling (above).
- **Flagged for maintainer / known limits:** energy numbers are sim-grounded but **unplaytested** —
  confirm the 10s regen / 60 cap *feels* right in a live session (it's a real pace change). The fish
  refill path is **not yet built** (next PR). Harvest/`!chop` still uses the old `randint(1,3)` base —
  intentionally left (separate action), flagged in the doc for a parity sanity-check.
