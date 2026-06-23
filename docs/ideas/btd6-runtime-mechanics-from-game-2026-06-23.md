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

## Empirical validation log — 2026-06-23 (cash)

First real-game data point against the cash model (owner-run, BTD6 **sandbox**), and a
preview of why the controlled per-round capture matters:

- **r100→r120, clean** (2 paragons, no income, every round sent fully): cash gained
  **$176,369**.
- **Three confounds nearly caused wrong "fixes":** (1) **double cash** active (÷2);
  (2) **sandbox has no `$100+n` round bonus**; (3) **CHIMPS ≠ sandbox**. Removing them:
  de-doubled pop cash ≈ **$88,185** vs our model's pop cash **$85,468** → **within ~3%.
  Cash model VALIDATED.** (Each confound flipped the conclusion mid-thread — the whole
  point of the runtime-extraction idea: read clean engine values under known conditions.)
- **Settled the calculator spread.** CyberQuincy ($139k for r100–120) **over-counts
  fortified bloons** — it pays extra cash for fortified, and the per-round divergence from
  us tracks fortified density exactly (r100 *no fortified* → matches us to the cent;
  r101/r102 *heavily fortified* → 1.6–1.7× our pop cash; r140 *half-fortified* → 1.48×).
  The game gives **fortified-independent cash**, confirming our `modifier-independent`
  assumption — **CQ is the one that's off**; topper is low (stale 0.02 decay past r120).
- **Residual ~3%** = the superceramic payout (we treat superceramic = normal ceramic; the
  +$86 may pay a hair more than exact compensation) and/or screenshot timing — too small to
  chase by fitting one measurement.
- **Owner's next step (planned):** a detailed **per-round** in-game cash capture (every
  round, no modifiers) → diff against our per-round numbers to pin that ~3% exactly. That
  table is the oracle the runtime-extraction mod (or a drift test) pins to.

## Links
- `docs/btd6/btd6-game-file-extraction-plan.md` — Phase 1 (models), historical.
- `docs/btd6/btd6-gamedata-dictionary.md` § "Runtime-formula facts the dump does NOT store".
- PRs #1384 / #1387 (freeplay health + RBE), and this session's cash investigation.
