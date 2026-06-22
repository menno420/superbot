# Mining economy balance — sim-pinned numbers (2026-06-22)

> **Status:** `plan` — design record; numbers produced by a simulation, for the owner
> to approve before any runtime change. Not binding; source + merged PRs win.
> Sibling of [`gear-set-numbers-2026-06-11.md`](gear-set-numbers-2026-06-11.md)
> (the "simulation-sane numbers" discipline) and the creature-game sim record.

## Applied (2026-06-22, PR #1286)

The owner approved the recommendation and chose the **energy** frequency brake
over a per-dig cooldown. Shipped:

- **Magnitude rebalance** (live constants): base roll `1-3 → 1-2`
  (`rewards.BASE_ROLL_MAX`), tool curve `×1/2/3/4/5 → ×1/1.13/1.25/1.38/1.5`
  (`rewards.mine_multiplier`, `1 + power*0.0625`), cell features
  `60/20/15/5 → 70/10/18/2` and treasure richness `×3 → ×2` (`grid.py`).
- **Energy system** (`utils/mining/energy.py`, migration 086): each dig spends 1
  energy; energy regenerates **+1 / 10s = 360/active-hour** (the chosen throttle,
  *no per-dig wait*); a full bar (60) is a burst, then you regen. Out of energy →
  digging is blocked with a "rest or eat" hint (`mining_workflow.dig`).
- **Refill via boosters** — `ration` (+25) and `energy drink` (+50) are buyable
  consumables (a coin sink) eaten via `!use` (`mining_workflow.use_item`).
- **Refill via cooking fish** (shipped in #1289, owner-chosen): caught fish are
  now sellable inventory items; `!cook <fish>` at a built **Campfire** structure
  turns one into a `cooked fish` (+30 energy when eaten). Resolves the fish-use
  half of Q-0175 (fish are both an energy source and sellable for coins).

The sim's `CURRENT` config now mirrors this applied state (with the energy
throttle modeled as its equivalent ~10s interval) and verdicts **BALANCED**; the
`PRE_REBALANCE` config preserves the diagnosed "before" (the table below).

## Why this exists

The mining grid's first real grid-`Mine` is live (#1281/#1282). The owner's read:
**rewards are too large and too frequent**, and he asked for *a simulation that
finds a balanced way to configure the game so it stays fun and playable for
everyone.* This record pins the simulator's diagnosis and its recommended
configuration.

Tool: **`tools/game_sim/mining_economy_sim.py`** (stdlib, deterministic,
`--seed`). Run it to reproduce every number here:

```
python3.10 tools/game_sim/mining_economy_sim.py
```

Depth (the band cap at 3) is **not** the focus — the *faucet* (reward magnitude
+ frequency) is, exactly as the owner framed it.

## How the faucet works today (the model)

One dig yields `(ore, amount)` where

```
amount = randint(1, 3) * tool_multiplier * cell_richness
coins  = amount * ore_value(depth-weighted draw)
```

- tool multiplier ×1/×2/×3/×4/×5 for none / pickaxe / iron / gold / diamond
  (`rewards.mine_multiplier` = `1 + mining_power // 2`),
- cell richness 1.0 / 2.0 / 0.5 / 3.0 for NORMAL / RICH / BARREN / TREASURE, with
  feature weights 60 / 20 / 15 / 5 → **25% of cells are a "lucky strike"**
  (`utils/mining/grid.py`),
- ore sells for 1 / 2 / 3 / 4 / 6 / 12 (stone…diamond), and deeper bands draw
  richer ore (`rewards.ore_weights_for_depth`),
- **there is no cooldown, no energy, and no rate limit on digging** — the faucet
  is throttled only by how fast a human can click.

**Benchmark — the rest of the economy is gated.** `!daily` pays a weighted
500–5000 once / 24h (mean ≈ **1,692 coins**); `!work` pays ~60 coins once / hour
(`services/economy_helpers.py`). So a casual player earns on the order of
**~1,700 coins/day** from the gated faucets.

## Diagnosis — the owner is right, and by a lot

At a realistic active cadence (one dig ≈ every 2.5s through the button UI), the
**current** faucet pays (sim, seed 42):

| profile | coins/dig | coins/active-hour | = dailies/hr |
|---|---|---|---|
| Newcomer (no tool, surface) | ~7.8 | ~11,300 | **6.7×** |
| Casual (pickaxe, cavern) | ~18.9 | ~27,300 | **16×** |
| Regular (iron pick, deep) | ~34 | ~49,000 | **29×** |
| Veteran (diamond pick, magma) | ~64 | ~92,000 | **54×** |

- **Too large:** a *fully-geared veteran earns a full `!daily` (~1,700) in ~1
  active minute*; even a fresh newcomer earns one every ~9 minutes. Mining
  dwarfs the entire gated economy.
- **Too frequent:** no cooldown means earnings are bounded only by clicking
  speed, and **lucky strikes fire on 25% of cells** — a bonanza every fourth dig
  doesn't feel special.
- **Not playable-for-everyone:** the geared/fresh gap is **8.2×**, so gear
  progression runs away from new players.

## Recommended configuration (lowest-penalty sweep result)

The sim sweeps 144 candidate configs (cooldown × base roll × tool curve ×
feature mix) and scores each against the balance targets below. The winner:

| knob | live | **recommended** |
|---|---|---|
| **dig frequency brake** | none | **~10s** equivalent throttle (≈ 360 digs/active-hr) |
| base roll | `randint(1, 3)` | `randint(1, 2)` |
| tool multiplier curve | ×1 / 2 / 3 / 4 / 5 | **×1 / 1.2 / 1.3 / 1.4 / 1.5** |
| cell feature weights | 60 / 20 / 15 / 5 (25% bonanza) | **70 / 10 / 18 / 2 (12% bonanza)** |
| treasure richness | ×3.0 | **×2.0** |
| ore values & depth weighting | — | **unchanged** (gear-coupled; do not touch) |

Resulting faucet (sim, seed 42):

| profile | coins/active-hour | = dailies/hr |
|---|---|---|
| Newcomer | ~1,675 | **1.0×** |
| Casual | ~2,280 | 1.3× |
| Regular | ~3,330 | 2.0× |
| Veteran | ~4,540 | 2.7× |

geared/fresh ratio **2.7×** (was 8.2×). Progression stays satisfying: a newcomer
affords their first pickaxe (25c) in ~1 active min, an iron pickaxe (60c) in ~2,
and the diamond pickaxe (320c) is a ~12-min goal — a real arc, not instant and
not a slog.

### Balance targets (the operational definition of "fun & playable for everyone")

- every player profile earns **~1,000–5,000 coins / active hour** (≈ 0.6–3
  dailies/hr) — clearly worth doing, but not trivializing the gated economy;
- the maxed-veteran : absolute-newcomer hourly ratio stays **≤ 3.5×** (the
  structural floor is depth-richness ≈1.7× × the tool-curve gap, so this is the
  tightest a tool-curve change alone reaches);
- **lucky strikes fire on 8–16% of cells** — special, not constant.

## The one design decision for the owner: how to brake frequency

The sim models the frequency brake as a **per-dig cooldown** because it is the
single cleanest knob, but a flat 10s lockout between digs can feel sluggish in a
grid navigator where *dig = move*. Two equivalent ways to deliver the same
~360-digs-per-active-hour throttle, better-feeling:

1. **Energy / stamina budget** (recommended feel) — e.g. a pool of digs that
   refills over time (≈ 6 digs/min, cap ~120). Lets a player **burst-explore**
   the grid, then taps out for a while. Caps the faucet without making every
   action wait. (New mechanic — a small `mining_energy` column + a refill clock.)
2. **Per-dig cooldown** — simplest to ship (reuse `utils/cooldowns.py`, as
   `!daily`/`!work` already do); the number above is the cooldown value.

Magnitude changes (base roll, tool curve, feature mix) are **independent of**
the frequency choice and are pure-constant edits — see below.

## Implementation map (when approved — not done in this PR)

All magnitude knobs are constants in the pure mining domain:

- base roll `randint(1, 3)` → `randint(1, 2)`: `utils/mining/rewards.py`
  (`roll_mine_loot`, and mirror in `roll_harvest_amount` if harvest is retuned too).
- tool curve: `rewards.mine_multiplier` (currently `1 + mining_power // 2`) — or
  retune the `mining_power` values in `utils/equipment.py`.
- feature weights + treasure richness: `_FEATURE_WEIGHTS` / `_RICHNESS` in
  `utils/mining/grid.py`.
- the frequency brake is a **new** seam in `services/mining_workflow.dig`
  (cooldown check, or an energy debit/refill) — the audited write path already
  owns the transaction.

A `tests/unit/tools/test_mining_economy_sim.py` parity test pins the sim's
mirrored constants to the live source, so this record can't silently drift from
the bot — when the constants change, update the sim's `CURRENT` config (and the
parity test will confirm the match).

## Caveats

- **Unverified faucet model.** The 2.5s active cadence and the four profiles are
  reasonable but estimated; confirm against a real play session before treating
  the absolute coins/hour as gospel. The *relative* finding (current faucet is
  ~7–55× the daily; recommended is ~1–3×) is robust to cadence.
- Harvest (`!chop`) and `!explore` use the same `randint(1,3)` base and were not
  separately swept; if mining is retuned, sanity-check those for parity.
- This record changes **no runtime behavior** — it is design input the owner
  approves (and chooses the frequency mechanic for) before any cog/util edit.
