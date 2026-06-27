# 2026-06-27 — Wire the two dead EffectiveStats (light_radius + luck) into mining (BUG-0026)

> **Status:** `in-progress`

**Run type:** owner-directed (in-session greenlight: *"Wire them into gameplay"* — AskUserQuestion answer
on BUG-0026, recorded as router Q-0208)

## What this run did

BUG-0026 found two `utils/equipment.EffectiveStats` fields — `light_radius` and `luck` — that gear grants
and the panel labels, but **no game read**, so the "Light"/"Luck" stats did nothing. The owner chose to
**wire** them (not remove). Both wirings are **additive-safe** (byte-identical when the stat is 0):

- **`light_radius` → the fog-of-war window.** New `utils/mining/grid.reveal_radius(light_radius)`
  (`min(2 + max(0, light_radius-1), 4)`); `views/mining/grid_mine_view.build_grid_embed` now computes it
  from the player's `character_stats(...).light_radius` and feeds it to **both** the discovered-cell query
  and the render so they stay in lock-step. **Non-regressive:** no-light/torch keep the prior radius 2; a
  lantern → 3, a diamond lantern → 4 (capped). A brighter light literally shows more of the map.
- **`luck` → rare-find weighting.** `utils/mining/exploration.resolve` now biases the weighted outcome
  pick toward rarer finds by `luck` (`_luck_weighted`: Common flat, Uncommon ×1.15, Rare ×1.4, Legendary
  ×1.6 per point). One luck source lifts the rare diamond-vein rate 7.7% → 10% **and** trims the hazard
  rate (Common stays flat, so hazards fall relatively). Numbers pinned in
  [`planning/mining-luck-light-numbers-2026-06-27.md`](../planning/mining-luck-light-numbers-2026-06-27.md).

The `_UNWIRED_STATS` allowlist (`test_effective_stats_consumed.py`) is now **empty**, so the
every-stat-is-consumed invariant *requires* both to stay wired. BUG-0026 → FIXED.

CI: `check_quality --full` green; arch 0 errors; new/updated tests (`reveal_radius`, `luck`, the view
light-widening case, the now-empty allowlist invariant) pass.

## ⚑ Self-initiated

Owner greenlit "wire them into gameplay" (Q-0208); **I chose the specific mechanics** — `light_radius` →
reveal-window width, `luck` → rarity-weighted find chance — within that goal, picking the thematic +
contained + reversible options over inventing a heavier mechanic (e.g. a new fog/visibility system or a
crit-damage stat). Sim-pinned + byte-identical-when-0, so fully tunable/reversible if the owner wants a
different feel.

## 💡 Session idea (Q-0089)

*Advertise the now-live `light_radius`/`luck` effects in the gear panel / character sheet.* The stats do
something now, but the panel still just shows a "Light: 3 / Luck: 2" number with no hint of the payoff —
a one-line effect blurb ("wider map view", "luckier rare finds") on the gear/character card would make the
upgrade path *legible*, turning a silent buff into a reason to chase better gear. Small view-layer
follow-on; routed as an idea, not built here.

## ⟲ Previous-session review (Q-0102)

The immediately-prior PR (#1511, absence-guard Layer B) scoped well to the safe grounded-contradiction
slice (no false-floor risk) and recorded the owner decision in the router. **What it could have done
better:** it shipped an *offline* guard for a *live-reported* false-"no" but didn't queue a
**live-battery probe** for the repro (for when creds are available) — the §4.3 half is noted as gated, but
the verification of the slice that *did* ship still rests on owner spot-checks. **System improvement:** when
shipping an offline guard for a live-reported bug, add the live-eval probe in the same PR even if it can't
run yet, so "verify live later" is a committed test, not a memory. (This session applied the same
principle — the BUG-0026 fix ships its full regression set, not a deferred "test later".)

## 🧾 Doc audit (Q-0104)

`check_quality --full` green (incl. `check_docs`/`check_consistency`); arch 0 errors. New facts homed: the
sim-pinned numbers doc (linked from the BUG-0026 entry), BUG-0026 flipped to FIXED with the fix detail.
The owner decision was recorded as router **Q-0208** in the prior (Layer B) PR — no new router entry
needed. Ledger: merged-only convention — the next reconciliation adds this PR.
