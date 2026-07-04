# 2026-07-01 — Fishing Dock structure (bite-speed coral sink, Tide Pool sibling)

> **Status:** `complete`
<!-- born-red flow (Q-0133): `in-progress` while open; flipped to `complete` as the final close step. -->

**PR:** [#1599](https://github.com/menno420/superbot/pull/1599) — Fishing Dock (bite-speed structure).
**Branch:** `claude/funny-franklin-4n38rf` (restarted from origin/main after #1598 merged).
**Run type:** `routine · dispatch`

## What this run did

**Second slice** of the same dispatch run (after #1598 shipped + auto-deployed the **Tide Pool**).
Built its **sibling**, the **Fishing Dock** — the ▶ Next I sharpened at the end of slice 1: a second
coral structure, but the *entry* one (cheaper, coral + wood) with a **bite-speed** payoff (faster
bites) rather than rarity-pull. The two now form a genuine build-order **choice** — faster fishing
(Dock) vs. rarer fish (Tide Pool) — and coral has **three** distinct sinks (cosmetic curios ·
rarity Tide Pool · speed Dock).

## Shipped (PR #1599)

- **`utils/mining/structures.py`** — `DOCK` registry entry (2-level coral + wood ladder) + pure
  `dock_bite_speed_mult(level)` payoff helper (`1.0 − 0.06·level`, ≤ 1.0, clamped; unbuilt ⇒ 1.0).
- **`utils/mining/market.py`** — `DOCK_BUILD_REASON` economy-audit tag.
- **`services/mining_workflow.py`** — Dock through the audited `build_structure` seam + a bite-speed
  reward suffix; no new mutation path. One `db.get_structures` read now serves both structures.
- **`services/fishing_workflow.py`** — `begin_cast` folds the dock's bite-speed multiplier into
  `effective_bite_speed`; unbuilt ⇒ ×1.0 ⇒ byte-identical. New `CastStart.dock_bonus` flag + ⚓ footer.
- **`views/fishing/dock.py`** + `!dock` + a ⚓ fishing-menu button (reachable, 0 gaps).
- Tests: +7 structure-math cases (incl. a "Dock is cheaper on coral than the Tide Pool" invariant),
  +2 `begin_cast` fold cases, +1 service build case (coral + wood consumed + reward line);
  regenerated dashboard/site artifacts (477→478 commands); `docs/planning/fishing-dock-numbers-2026-07-01.md`.

Full CI mirror green (13,433 passed); `check_architecture --mode strict` 0 errors. No migration
(coral + structures reuse existing stores). Self-merge on green.

## Decisions made alone (owner should be aware)

- **Payoff = bite-speed, deliberately a *different axis* than the Tide Pool's rarity-pull.** Speed is
  throughput (more casts/session → more of everything) without changing *what* you catch; pull is
  quality without changing the rate. So the two structures don't overlap. Both bounded ≤ 12%.
- **Cost shape differentiates them:** Dock = coral + **wood** (a common mined material) + lower coins,
  positioning it as the affordable *entry* structure vs. the Tide Pool's coral + coins premium. All
  single-line constants in the numbers doc + test.

## Flagged for maintainer / known limits

- Never played live — the numbers are sim-reasoned, not balance-tested; a live walk may retune.
- The fishing menu now carries **two** structure buttons (Tide Pool + Dock). It's within Discord's
  component budget, but the ▶ Next I left suggests folding them into a single "🏗 Structures" sub-hub
  before a third structure lands, to keep the menu lean.

## Context delta

- **Needed but not pointed to:** nothing new — I had the full structure pattern loaded from slice 1
  (#1598), so this slice was a near-mechanical application of it. That *reuse* is the point: the
  registry-driven structure system makes a new structure genuinely one entry + a payoff hook.
- **Pointed to but didn't need:** n/a (same-run continuation, no re-orientation).
- **Discovered by hand:** confirmed `build_structure`'s material check + `describe_materials` handle a
  *multi*-material cost (coral + wood) generically — no per-material wiring needed.

## 🛠 Friction → guard

- **Friction (same class as slice 1):** isort flagged the new `dock` import placed out of order in
  `views/fishing/__init__.py` — caught only by the full mirror, not the PostToolUse auto-fix (which
  fires per-edit but the manual `__all__`/import edit wasn't a formatter-triggering change it re-sorted).
  **Guard:** already covered by `scripts/check_quality.py --full` (the CI mirror) catching it pre-push;
  the durable lesson (carried from slice 1) is **run `check_quality`, never a bare formatter over a
  path** — I avoided the `black tests/` footgun this time. No new guard warranted (the mirror already
  enforces it); the slice-1 proposal (a formatter-scope wrapper) still stands in that log.

## 💡 Session idea

**A "🏗 Structures" fishing sub-hub** — fold the Tide Pool + Dock (and future fishing structures) menu
buttons into one child panel that lists all buildable fishing structures with their current level +
next cost, so the top-level fishing menu stays lean as the structure set grows. Genuinely worth having
now that there are two; it's the natural scaling seam and mirrors the mining Workshop hub. Left as the
sharpened ▶ Next in the S1 sector file; not built this run (kept scope to the one structure).

## ⟲ Previous-session review

The previous slice (#1598 Tide Pool, this same run) did exactly what a good first slice should: it
built a *reusable* pattern (the registry-driven structure + additive-safety knob fold) and **left a
crisp, specific ▶ Next** ("a bite-speed dock"), which is precisely why this slice shipped in a near-
mechanical pass with zero re-derivation. The one thing it could have done better — and which this slice
corrects — is that adding a second menu button revealed the fishing menu will get crowded; slice 1
could have anticipated the sub-hub seam. A **system observation**: the born-red + auto-merge flow made
the two-slice run clean, but there's an inherent serialization cost — slice 2 can't cleanly start until
slice 1 *merges* (else it stacks into the same PR), and webhooks don't signal merge-success, so I had
to rely on the merge webhook arriving. Worth noting for the routine: multi-slice runs are gated on
merge latency, not just token budget.

## 📤 Run report

- **Did:** shipped the Fishing Dock — a bite-speed coral structure completing the Tide Pool build-
  choice (faster fishing vs. rarer fish) · **Outcome:** shipped
- **Shipped:** #1599 — Dock structure + a bite-speed cast-knob fold (coral + wood sink, no migration,
  byte-identical when unbuilt). *(Same run also shipped #1598 Tide Pool, already merged + deployed.)*
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none` (merge auto-deploys; no data step)
- **⚑ Self-initiated:** **yes** — the Dock was my own slice-1 session idea, not a dispatched order
  (Q-0172). It's a contained, reversible deepening that completes the coral structure-choice; flagged
  here for owner review/revert. (The Tide Pool #1598 was the roadmap's explicit pick — not self-initiated.)
- **↪ Next:** S1 fishing — a "🏗 Structures" sub-hub folding the two structure buttons, or a second
  curio tier; both pure + self-mergeable. (Sharpened in `docs/current-state/S1-bot.md`.)
