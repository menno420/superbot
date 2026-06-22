# 2026-06-22 — Mining: fish cooking + sellable fish (energy refill via campfire)

> **Status:** `complete` — fish cooking + sellable fish shipped & verified. Owner-directed →
> auto-merges on green (Q-0191). PR #1289.

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

## Shipped (PR #1289)

- **Fish are tangible items now** — `fishing_workflow.fish` grants the caught species to the mining
  inventory in its existing atomic catch txn (catch-log retained for the dex). Fish bulk-added to
  `utils/mining/items.py` as sellable `RESOURCE`s, value `max(1, round(size_rank/3))` (1–7) — kept low
  on purpose. Sell works through the existing `!sell`/market.
- **Campfire** — a new single-level structure in `utils/mining/structures.py` (generic
  `mining_structures` table, **no migration**), `!build campfire` (500🪙 + 20 wood + 10 stone),
  `structures.cooking_unlocked(level)` gate.
- **Cook → eat** — `mining_workflow.cook` (campfire-gated; consume raw fish → grant generic
  `cooked fish`, one txn) + `!cook [n] <fish>`; `cooked fish` (+30 energy) added to
  `energy.RESTORE_VALUES`; eaten via the existing `!use`.
- Docs: Q-0196 (owner decision recorded), games folio fishing pointer, balance-doc Applied section.
  Regenerated the dashboard/site artifacts (commands 369→370 from `!cook`).

Verified: `check_quality --full` green (11,518 passed after the artifact regen), arch 0 errors, docs
strict clean. **No migration; merge auto-deploys (Q-0193).**

## Findings / decisions

- **Owner decisions (Q-0196, via AskUserQuestion):** cook-at-a-campfire (not eat-raw / not free) +
  fish are both energy-source AND sellable. Resolves the *fish-value* half of Q-0175 (the
  leveling-ladder/minigame tail stays open).
- **Decisions made alone:** campfire cost (500🪙+wood+stone), fish sell formula (size_rank/3, low),
  cooked-fish flat +30 energy (so you sell big fish for coins, cook any fish for a standard meal — a
  real player choice). Tunable; pinned in the modules + Q-0196.
- **Balance caveat (flagged for maintainer):** fishing has no energy/cooldown, so sellable fish is an
  *unpaced* coin trickle. Kept deliberately low; a future **fishing-pacing pass** should revisit before
  fish become a meaningful faucet (don't re-open the mining-faucet fix via fishing).

## ⚑ Self-initiated: none

Owner-directed in-chat ("refilled by cooking/eating fish") + the Q-0196 AskUserQuestion answers.

## 💡 Session idea (Q-0089)

**A `!cook all` / cook-from-a-panel affordance + a Campfire panel.** Cooking is currently `!cook <fish>`
one species at a time; a player with a full net of mixed fish will want "cook everything small" or a
button. A small `cook_all_small` (cook every fish below a size threshold, keep the big ones to sell) +
a 🔥 Campfire hub panel (mirroring the Forge panel) would make the cook loop as smooth as the
sell-all/market loop. Low-risk, reuses the structures-panel pattern.

## ⟲ Previous-session review (Q-0102)

**Previous session:** the rebalance+energy session (#1286). **Did well:** it shipped the *generic*
`use_item` food path + `energy.RESTORE_VALUES` table — which is exactly why THIS session's fish work was
small: cooked fish was one table entry + one item, no new eat-mechanic. The "boosters first, fish later"
split paid off. **Could have done better:** #1286 left fish-use as a vague "follow-up" without surfacing
that fish weren't even inventory items — I only discovered the catch-log-vs-inventory gap via an Explore
pass this session. **System improvement:** when a PR defers a named follow-up, its session log should
record the *one blocking unknown* the follow-up must resolve (here: "fish are a catch-log, not items") —
so the next session starts from the constraint, not a fresh investigation. (This session's log does that
for the fishing-pacing caveat.)

## Context delta (reflection interview)

- **Needed but not pointed to:** that the generic `!build <structure>` command + `build_structure`
  workflow are fully registry-driven — adding the campfire needed **zero** new build command/cog wiring,
  just a `structures._DEFS` entry + a `_STRUCTURE_BUILD_REASON` map row. The structures module docstring
  says "adding one is its registry entry below" but the *cog-side is free too* isn't stated; worth a line.
- **Pointed to but didn't need:** the migration runbook — this feature reuses existing tables
  (`mining_structures`, `mining_inventory`), so no migration despite being a sizable feature.
- **Discovered by hand:** the RS02 write-boundary AST scan only covers `disbot/{views,cogs}` — so
  `fishing_workflow` (a service) writing `update_mining_item` directly is allowed and is the correct
  conn-composed RS02 pattern; a cross-service `mining_workflow` call would have been worse (nested txn).
- **Decisions made alone:** the numbers above (campfire cost, fish value, cooked-fish energy).
- **Flagged for maintainer / known limits:** the **fishing-pacing** caveat (sellable fish is unpaced);
  cooked fish is a flat +30 regardless of fish size (intentional — big fish are for selling); `!cook`
  is one-species-at-a-time (the session idea above proposes cook-all).
