# 2026-06-27 — EffectiveStats knob-coverage guard + dead-stat finding (BUG-00xx)

> **Status:** `in-progress` — born-red card; opening the PR before the build (Q-0133/Q-0189).

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

## 📤 Run report

*(filled at close)*
