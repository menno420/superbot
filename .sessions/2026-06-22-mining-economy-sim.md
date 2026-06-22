# 2026-06-22 — Mining economy / balance simulation

> **Status:** `complete` — mining balance sim built + run; recommendation pinned.
> Owner-directed (in-chat), so auto-merges on green (Q-0191; no review gate). PR #1284.

## Arc (what I'm about to do)

Owner-directed in-chat: the mining grid's first real grid Mine is now live (#1281/#1282), and
the owner feels **rewards may be too large and too frequent**. He recalled that a prior session
introduced the idea of *running a simulation to find a balanced configuration*. Task: create and
run a balance simulation for the mining game so it stays **fun and playable for everyone**, and
surface a recommended, balanced configuration of the tunables (reward size / frequency / grid
descent), following the existing `tools/game_sim/` design-sim precedent
(`creature_battle_sim.py` — stdlib, deterministic, PASS/WARN verdict, config-as-data).

Depth (currently capped at 3) is explicitly *not* the priority — the faucet (reward magnitude +
frequency) is.

## Plan

- Map the real mining reward + grid mechanics (rewards, drop rates, depth, costs, XP).
- Build `tools/game_sim/mining_economy_sim.py` — Monte-Carlo a player's session(s): coins/XP
  per dig, per session, over time; sweep candidate configs against fun/balance targets.
- Run it, find the most balanced config, write the numbers into a `docs/planning/` record.
- Light smoke/invariant test mirroring `test_creature_battle_sim.py`.

## Shipped (PR #1284)

- **`tools/game_sim/mining_economy_sim.py`** — stdlib, deterministic Monte-Carlo simulator of the
  mining *faucet*. Models one dig (`randint(1,base) × tool_mult × cell_richness × ore_value`,
  depth-weighted) across four player profiles (newcomer → veteran), measures coins/active-hour against
  the gated economy benchmark (`!daily` ≈ 1,692/24h), and **sweeps 144 candidate configs** (cooldown ×
  base roll × tool curve × feature mix) for the lowest-penalty balanced config. Prints a PASS/WARN
  verdict + the recommended config + a progression curve + concrete deltas vs the live game.
- **`tests/unit/tools/test_mining_economy_sim.py`** — 11 tests: **parity** (the sim's mirrored
  constants match the live `utils/mining/{items,rewards,grid}` + `equipment` source — drift guard),
  diagnosis (current faucet is over-target), sweep finds a balanced config, determinism, main runs.
- **`docs/planning/mining-economy-balance-2026-06-22.md`** — the sim-pinned design record (diagnosis
  table, recommended config, balance targets, the energy-vs-cooldown frequency decision, and the
  when-approved implementation map). Linked from `docs/subsystems/games.md`.

## Findings

- **The owner is right, and the imbalance is large.** Live faucet pays a *fully-geared veteran a full
  `!daily` (~1,700 coins) in ~1 active minute*; even a fresh newcomer earns one every ~9 min — mining
  is **7–55× the gated economy's hourly rate**. There is **no cooldown / energy / rate limit** at all,
  and **25% of cells are lucky strikes** → "too large AND too frequent" quantitatively confirmed.
- **Recommended config** (penalty 0.00, all profiles ~1–2.7 dailies/active-hr, geared/fresh gap 8.2× →
  2.7%): a ~10s-equivalent **frequency brake** + base roll `1-3 → 1-2` + flatter tool curve
  `×1/2/3/4/5 → ×1/1.2/1.3/1.4/1.5` + bonanza `25% → 12%` (treasure richness `×3 → ×2`). Ore values +
  depth weighting held fixed (gear-coupled).
- **One owner decision surfaced:** *how* to brake frequency — a per-dig cooldown (trivial to ship) vs
  an energy/stamina budget (better feel: burst-explore then tap out). The doc recommends energy and
  gives the equivalent throttle. **No runtime change in this PR** — it's design input to approve.

## ⚑ Self-initiated: none

Owner-directed in-chat ("create/run a simulation that finds the most balanced way for the mining
game"). Design-only (`tools/` + docs + a test) — no `disbot/` runtime edit, so no review gate
(Q-0191). The eventual rebalance edit is a separate, owner-approved PR.

## 💡 Session idea (Q-0089)

**A `tools/game_sim/` README + a shared faucet/economy harness.** There are now two design sims
(`creature_battle_sim`, `mining_economy_sim`) that independently re-derive the *same* economy
benchmark (`!daily` ≈ 1,692, `!work` ≈ 60/hr) and the same "dailies-per-active-hour" balance lens.
A small shared `tools/game_sim/economy_benchmark.py` (the gated-faucet constants, with a parity test
to `economy_helpers.py`) + a one-screen README indexing the sims would stop that benchmark drifting
per-sim and make "is game X's faucet in line with the rest of the economy?" a one-import question for
the next game's sim (pets, fishing, idle). Worth it because every future game faces the same
"is the reward balanced against the economy?" question this session just answered ad-hoc.

## ⟲ Previous-session review (Q-0102)

**Previous session:** `2026-06-22-mining-grid-mine.md` (grid Mine, PR #1281/#1282). **Did well:** kept
the *balance* in the pure `utils/mining/world.py`/`grid.py` layer so "z = the existing depth band,
balance carries over unchanged" — which is exactly why this faucet was cleanly simulatable from pure
functions without a DB/Discord harness. **Missed / could improve:** it shipped a brand-new, more
*engaging* mine loop (unlimited directional digging, a bonanza every 4th cell) **without re-checking
the faucet math** — engagement went up but the reward rate (already uncapped) got *easier to farm*,
which is what prompted the owner's "too large & too frequent." **System improvement it surfaces:** a
new or reworked **earning** loop should ship with a one-line faucet sanity-check (coins/active-hour vs
`!daily`) — the same reflex as "new mutation → audit seam." The `mining_economy_sim` + the shared
benchmark idea above is the tooling that makes that reflex cheap; longer-term it could be a
lightweight "economy-impact" note in the games pre-PR skill.

## Context delta (reflection interview)

- **Needed but not pointed to:** the **economy benchmark** for "balanced" — `!daily`/`!work` payout
  tables live in `services/economy_helpers.py` (`_DAILY_TIERS`, `JOBS`), not in the games folio or any
  mining doc. A "what does a coin/hour *mean*?" pointer (the gated-faucet baseline) belongs in the
  games folio's economy section; this session reverse-engineered it. (The session-idea harness fixes
  this durably.)
- **Pointed to but didn't need:** CodeGraph / the symbol tools — the faucet is a handful of pure
  functions; `context_map` + targeted reads + one Explore fan-out was the whole job.
- **Discovered by hand:** the ore **sell** values (stone 1 … diamond 12) are *not* a sell table — they
  are the `RESOURCE` `value` field in `utils/mining/items.py`, surfaced via `market.sell_price` →
  `item_value`. Only documented in a `rewards.py` comment. The parity test now pins it.
- **Decisions made alone:** the four player profiles, the 2.5s active cadence, and the balance-target
  bands (1k–5k coins/hr ≈ 0.6–3 dailies/hr; ratio ≤ 3.5×; bonanza 8–16%). These define "balanced" and
  the owner should sanity-check them against his intent — they're stated in the doc's targets section.
- **Flagged for maintainer / known limits:** the absolute coins/hour depends on the *estimated* 2.5s
  cadence — confirm against a live play session before treating the numbers as final (the *relative*
  7–55× finding is robust). And the **frequency-brake mechanic is an open choice** (energy vs
  cooldown) — the recommendation is a design input, applied in a separate owner-approved PR.
