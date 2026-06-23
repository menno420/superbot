# BTD6 runtime/simulation mechanics — extract straight from the game

> **Status:** `ideas` — capture, not a plan, not approval.
> **Subsystem:** btd6
> **Owner-raised** (2026-06-23, in-chat): *"our original plan was once to get the data
> straight from the original game … because we see so many different stats and numbers
> everywhere."*

## The problem this fixes

Every BTD6 number dispute we've had traces to the same root: **the data we have is
*entity models*, but the numbers people argue about are produced by the *runtime
engine*.** Community calculators (topper64, cyberquincy, bloonswiki) each re-derive the
runtime layer independently, and they disagree — sometimes badly:

- **Freeplay health scaling** — not in the dump at all; sourced from topper64 (PR #1384
  shipped *wrong* unverified brackets, fixed in #1387 only after a second anchor exposed
  them: r140 fortified BAD is 200,000 HP / ×5.0, not the ×2.38 we first shipped).
- **Round-scaled RBE** — a spawn-tree recompute with MOAB ×v(r) + superceramics; we
  reproduced `BAD@100 = 67,200` exactly, but only by reverse-engineering the superceramic
  RBE (68) against one anchor.
- **Cumulative cash at r140** — three sources, three answers: cyberquincy ~400K, our bot
  ~350K, topper ~300K. Ours is the best-grounded (the cash-per-pop decay **is** in the
  dump, `IncomeSets/`), but nobody can point to a single authoritative figure.

We keep playing detective against contradictory secondary sources. A single
game-authoritative source for the *runtime* layer ends that whole class of bug.

## What we already have vs. the gap

- **Have (Phase 1, done):** the **model** data via BTD Mod Helper's "Export Game Data"
  dump — `Bloons/` base stats, `Rounds/` composition+timing, `Towers/`, `Upgrades/`,
  `IncomeSets/` cash decay. See `docs/btd6/btd6-game-file-extraction-plan.md` (historical).
- **Gap:** the **runtime/simulation mechanics** the model export omits — the freeplay
  health/speed ramp `v(r)`, the superceramic swap (60 HP shell, halved children, the
  +$86 compensation), per-round RBE, and how cash-per-pop is actually applied. These live
  in the compiled `Assembly-CSharp` (Il2Cpp) simulation code, not in any exported model.

## Two routes (recommendation: the runtime mod)

1. **Runtime-extraction mod (preferred).** A BTD Mod Helper mod that walks the *live*
   `Simulation`: for each round set × round × bloon, read the **engine-computed** health,
   speed, RBE, and cash. Dump it to JSON the same way "Export Game Data" already does.
   This is empirical ground truth, uses the toolchain we already depend on, and produces a
   table our curated sidecars (`bloon_scaling.json`, round cash/RBE) can be **pinned to**
   — replacing the topper64/cyberquincy cross-checks with a game-sourced oracle.
2. **Decompilation.** Read the constants/formulas directly from `Assembly-CSharp` (the
   freeplay-scale function, the superceramic model, the cash application). More precise on
   *formula shape*, but a heavier, more brittle toolchain (Il2Cpp dumping per patch).

## Value & shape

- **Kills the recurring "conflicting numbers" bug class** at the root — the motivation the
  owner named. Turns `bloon_scaling.json` / round cash / RBE from *community-derived* into
  *game-verified*.
- **Pairs with the drift-check idea** (`.sessions/2026-06-23-btd6-freeplay-curve-and-rbe.md`
  §idea): once we have game-sourced runtime values, they become the test oracle, and a CI
  check catches an NK rebalance as a red test instead of a user complaint.
- **Scope: large, "eventually"** (owner's word) — a modding/extraction toolchain, run per
  game patch. Not urgent, must not derail current work. Best sequenced as its own
  planning effort when capacity allows; a first slice could target just the freeplay
  health curve + per-round RBE/cash (the exact things we fought this session).

## Links
- `docs/btd6/btd6-game-file-extraction-plan.md` — Phase 1 (models), historical.
- `docs/btd6/btd6-gamedata-dictionary.md` § "Runtime-formula facts the dump does NOT store".
- PRs #1384 / #1387 (freeplay health + RBE), and this session's cash investigation.
