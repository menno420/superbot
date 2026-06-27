# 2026-06-27 — EffectiveStats knob-coverage guard + dead-stat finding (BUG-00xx)

> **Status:** `complete` — ready to merge (Q-0133). Run type: routine · dispatch.
> Full CI mirror green (**12851 passed**, arch 0, check_docs/consistency clean; guard verified to flag
> exactly `light_radius` + `luck` when the allowlist is emptied).

> **Run type:** `routine · dispatch` — second slice of the same empty-fire dispatch run (slice 1 =
> #1504, fishing-gear stats, merged). Executes the Q-0089 idea I raised in slice 1's log.

**Branch:** `claude/funny-franklin-iv2rzi` (re-synced to `main` @ #1504 merge, `2aa5360b`).

## What I'm about to do (intentions)

While building slice 1 I extended the cross-game `EffectiveStats` block (added `fishing_power`/
`bite_luck`) and wired them into a consumer (`begin_cast`). Nothing in the repo asserts that a *new*
stat field actually gets read by some game's consumption path — the "added the stat, forgot the knob"
half-ship class. Building the check **surfaced a real latent bug**: `EffectiveStats.light_radius` and
`EffectiveStats.luck` are **dead stats** — defined, summed, and labelled, but **no game reads them** to
change behaviour (the diamond pickaxe's `luck=1`, the lucky charm's `luck`, and every torch's
`light_radius` currently do nothing; only `depth_access`/`loot_bonus`/`mining_power`/`damage`/… are
consumed).

Slice 2 (offline, test-only + docs):

1. **`tests/unit/invariants/test_effective_stats_consumed.py`** — an AST guard asserting every
   `EffectiveStats` field is read (`stats.<field>`) by at least one `disbot/` consumer module (excluding
   the `equipment.py` definition + generic label/glyph/`__add__` plumbing), with a documented
   `_UNWIRED_STATS` allowlist for `light_radius` + `luck` pointing at the bug-book entry. A second
   assertion keeps the allowlist honest (an allowlisted stat that *gains* a consumer must leave the list).
2. **`docs/health/bug-book.md`** — a new entry capturing the dead-stat finding (root cause + the
   wire-it-or-remove-it decision flagged to the owner, since "what should luck/light do?" is a gameplay
   design call, not a contained mechanical fix).

No runtime/`disbot/` behaviour change — a guard + a finding.

## What shipped

1. **`tests/unit/invariants/test_effective_stats_consumed.py`** — an AST guard: every `EffectiveStats`
   field is read (`<expr>.<field>`) by ≥1 `disbot/` consumer outside the definition module, or is on the
   documented `_UNWIRED_STATS` allowlist. Three tests: the coverage floor, an **honesty check** (an
   allowlisted stat that gains a consumer must leave the list), and a guard-the-guard (allowlist only
   names real fields). Verified fails-closed: with the allowlist emptied it flags exactly `light_radius`
   + `luck`.
2. **`docs/health/bug-book.md` → BUG-0026 (OPEN)** — captures the dead-stat finding: `light_radius`
   (every torch/lantern grants it; descent gates only on `depth_access`) and `luck` (diamond pickaxe +
   lucky charm grant it; only `loot_bonus` is read) are defined/summed/labelled but read by no game.
   Left OPEN because wiring them (or removing them) is a gameplay-design decision for the owner; the
   guard prevents the class from growing meanwhile.

Test-only + docs — no runtime/`disbot/` behaviour change.

## Why OPEN, not auto-fixed

"What should luck / light_radius *do*?" (a crit-find chance? a grid reveal radius?) is a balance/design
call the owner owns — and the alternative (remove them + their gear bonuses + labels) is equally a
design choice. Guessing either would be inventing product intent. The honest move is capture + guard +
flag; the guard makes the eventual fix self-enforcing (the allowlist entry can't survive a wiring).

## Context delta

- **Discovered by hand:** the two dead stats — surfaced *by building the guard*, which is the
  completeness-critic value (the check found the thing it was built to prevent). **Needed but not
  pointed to:** nothing new; the invariants-dir convention (`tests/unit/invariants/`, `parents[3]/disbot`,
  the Q-0105 UNVERIFIED header) was easy to mirror from a sibling test.
- **Decisions made alone:** scoped this as **guard + finding, not a gameplay fix** (the wiring is
  owner-design); used a **name-based AST attribute scan** (inclusive — a coincidental `.<field>` counts
  as consumed), acceptable for a "read by nothing" floor. Both reversible.
- **🛠 Friction → guard:** none new this slice. The guard *itself* is the friction-prevention: it
  converts the "added a stat, forgot the knob" half-ship class (which `fishing_power`/`bite_luck` could
  have hit in slice 1, and which `light_radius`/`luck` actually did historically) into a CI failure.

## 💡 Session idea (Q-0089)

Already contributed in slice 1's log (the knob-coverage guard — *built here*). No second forced idea
this slice (Q-0089 is one genuine idea per session, not per PR; forced filler is worse than none).

## ⟲ Previous-session review (Q-0102)

Covered in slice 1's log (review of #1466 + the dispatch-menu offline-tag drift note). No new
predecessor to review for this same-session slice.

## 📤 Run report

- **Did:** shipped the Q-0089 knob-coverage guard (executing slice 1's own idea) + captured BUG-0026
  (dead stats `light_radius`/`luck`) the guard surfaced. · **Outcome:** shipped
- **Shipped:** #1505 — test(equipment): EffectiveStats knob-coverage guard + BUG-0026 finding
  (self-merge on green, Q-0113)
- **Run type:** `routine · dispatch`
- **Class:** correctness/guard (test + docs; contained, reversible) + a bugs-first finding
- **⚑ Owner decisions needed:** **BUG-0026** — wire `luck` + `light_radius` into a game (what should
  they do?) **or** remove them + their gear bonuses/labels. A gameplay/balance call.
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** **yes** — built the Q-0089 idea I raised in slice 1, no dispatch/owner ask
  (idea→ship open, Q-0172). The dead-stat finding is a bugs-first root sweep (CLAUDE.md §6), not an
  invented feature.
- **↪ Next:** unchanged from slice 1 — S1 ▶ **fishing-gear acquisition depth**; plus BUG-0026 awaits the
  owner's wire-or-remove call.

