# 2026-07-01 — Fishing Tide Pool structure (coral structure-target sink)

> **Status:** `complete`
<!-- born-red flow (Q-0133): `in-progress` while open; flipped to `complete` as the final close step. -->

**PR:** [#1598](https://github.com/menno420/superbot/pull/1598) — Fishing Tide Pool (5th cast knob).
**Branch:** `claude/funny-franklin-4n38rf` (restarted from origin/main #1597).
**Run type:** `routine · dispatch`

## What this run did

Empty scheduled fire → advanced the next plan slice. The S1 sector's explicit `[offline]`
"▶ Next offline successor" for the fishing rare-material arc was *"a second curio tier or a
**structure-target variant** (a deepwater material that builds a fishing structure rather than a
collectible)."* Built the **structure-target variant**: the **Tide Pool** — coral's first
*functional* sink (alongside the cosmetic curios shipped the same morning).

## Shipped (PR #1598)

- **`utils/mining/structures.py`** — new `TIDE_POOL` registry entry (3-level coral + coin build
  ladder) + pure `tide_pool_pull_mult(level)` payoff helper (`1.0 + 0.04·level`, clamped). Reuses the
  generic Forge/Home/Campfire registry math.
- **`utils/mining/market.py`** — `TIDE_POOL_BUILD_REASON` economy-audit tag.
- **`services/mining_workflow.py`** — Tide Pool wired into the audited `build_structure` seam
  (`_STRUCTURE_BUILD_REASON` + a `+N%` reward suffix); no new mutation path.
- **`services/fishing_workflow.py`** — `begin_cast` reads the player's tide-pool level and folds its
  pull multiplier as the **5th "how-well" knob** (rod × bait × weather × gear × **tide pool**);
  unbuilt (level 0) ⇒ ×1.0 ⇒ byte-identical (the additive-safety property the gear knob uses). A new
  `CastStart.tide_pool_bonus` flag surfaces a 🪸 cast-footer note.
- **`views/fishing/tide_pool.py`** + `cogs/fishing_cog.py` `!tidepool` + a 🪸 Tide Pool button on the
  fishing menu — the build panel (mirrors the Forge/Home panels), reachable + buttonized (0 gaps).
- Tests: +6 structure-math cases, +2 `begin_cast` fold cases (built raises pull / unbuilt
  byte-identical), +1 service build case (coral consumed + reward line); regenerated dashboard/site
  artifacts for the new command; `docs/planning/fishing-tide-pool-numbers-2026-07-01.md` (sim-pinned).

Full CI mirror green (13,423 passed); `check_architecture --mode strict` 0 errors. No migration
(coral + structures reuse existing stores). Self-merge on green.

## Decisions made alone (owner should be aware)

- **Payoff = rarity-pull, not bite-speed or new fish.** The Tide Pool reweights the *already-unlocked*
  band toward rarer fish (max +12% at level 3); it never unlocks species (that stays the fishing-level
  axis) and never changes bite wait. Chosen as the single most intuitive, easily-bounded "my
  investment gets better fish." Reversible (a number + one multiplier).
- **Domain placement:** a *fishing* feature stored on the *mining*_structures table + built via
  `mining_workflow`. Precedent: the Campfire structure already gates "cooking fish," and coral itself
  already crosses fishing→mining_inventory. The table is explicitly generic `(user, guild, structure, level)`.

## Flagged for maintainer / known limits

- Never played live — the numbers (coral 3/6/10, +4/8/12%) are sim-reasoned, not balance-tested. A
  live walk may want them re-tuned; all are single-line constants in the numbers doc + test.

## Context delta

- **Needed but not pointed to:** that CI **excludes `tests/`** from black is in CLAUDE.md, but it's
  easy to trip — a broad `black tests/` reformatted ~120 unrelated test files (see friction below).
- **Pointed to but didn't need:** nothing notable — the S1 sector file routed straight to the pick.
- **Discovered by hand:** the structure system is fully registry-driven — a new structure is one
  `_DEFS` entry + ladder + names + (optional) a reward-suffix + payoff hook; `build_structure`,
  `_check_materials`, and `describe_materials` are all material-agnostic (coral "just works").

## 🛠 Friction → guard

- **Friction:** `python3.10 -m black tests/…` reformatted ~120 test files CI never formats (`tests/`
  is a black exclude), creating a huge spurious diff I had to revert file-by-file. **Guard shipped:**
  none code-level this run (a black-scope guard touching config is owner-gated). **Proposed (DISCUSS):**
  a tiny pre-commit/checker that warns when a formatter is invoked over a CI-excluded path, or a
  `scripts/fmt.py` wrapper pinned to CI's exact scope so agents never pass a raw path. Recorded here so
  the next run reaches for `scripts/check_quality.py` (correct scope) rather than a bare `black <path>`.

## 💡 Session idea

**A "fishing dock" bite-speed structure** as the Tide Pool's sibling — the same coral (or a new
deepwater material) building a structure whose payoff is a *bite-speed* knob (faster bites) rather than
rarity-pull, giving the two structures distinct roles. Genuinely worth having: it turns the single
"tide pool" into a small *choice* of coral investment (rarer fish vs. faster fishing), which is the
kind of build-order depth the mining structure ladder already rewards. Left as the sharpened ▶ Next in
the S1 sector file; not built this run (kept scope to one clean slice).

## ⟲ Previous-session review

The prior dispatch run (coral 🪸 / curios, same morning) did the *cosmetic* half of the rare-material
arc cleanly and, notably, **left the roadmap ▶ Next crisply worded with two concrete options** — which
is exactly why this run could pick up and ship in one hop with zero re-derivation. That's the
self-improving loop working: a good handoff line is worth more than a long narrative. One thing it
*could* have done: it catalogued the previously-uncatalogued pearl as a fix-on-sight, but the coral
doc's "second curio tier or a structure variant" was slightly under-specified on *which* stores/seams
a structure variant would reuse — I had to confirm `mining_structures` is generic by reading source. A
**system improvement** this surfaces: when a roadmap ▶ Next names an option that spans a *different*
subsystem (here, fishing → mining structures), a one-line "reuses X seam" pointer in the handoff would
save the next agent the cross-domain source dig. Minor; not worth a guard.

## 📤 Run report

- **Did:** shipped the Tide Pool — coral's functional fishing-structure sink (the roadmap's named
  structure-target variant) · **Outcome:** shipped
- **Shipped:** #1598 — Tide Pool structure + the fishing cast's 5th rarity-pull knob (coral sink,
  no migration, byte-identical when unbuilt).
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none` (merge auto-deploys; no data step — coral/structures reuse
  existing stores)
- **⚑ Self-initiated:** `none` (the work was the sector's explicit `[offline]` ▶ Next startable pick,
  grounded in the shipped coral arc's roadmap successor — not an invented feature)
- **↪ Next:** S1 fishing — a second Tide Pool-style structure with a *different* payoff (a bite-speed
  "dock"), or a second curio tier; both pure + sim-pinnable, self-mergeable. (Sharpened in
  `docs/current-state/S1-bot.md`.)
