# 2026-06-23 — BTD6 freeplay curve fix + ground-truth round-scaled RBE

> **Status:** `complete` — owner-directed (the owner chose "full ground-truth RBE" +
> "source the curve properly" via AskUserQuestion, then corrected the spawn model).
> PR #1387; auto-merge armed on green (Q-0127); owner-directed → merges immediately
> (Q-0191).

> **Run type:** `manual · owner-directed`

Follow-up to PR #1384 (round-scaled bloon health). Two things shipped:

## 1. Bug fix — #1384's r>100 health brackets were WRONG

#1384 shipped a `bloon_scaling.json` whose r≤100 bracket was cross-verified but whose
r>100 brackets were "documented but unverified" — and they were wrong. Ground truth: a
**fortified BAD on round 140 has 200,000 HP** = ×5.0 of its 40,000 base, but the
shipped curve predicted ×2.38. Sourced the **authoritative 8-bracket piecewise curve**
from topper64's calculator and validated it against **both** independent anchors:
`v(100)=1.40` (BAD 28,000 ✓) and `v(140)=5.00` (fortified BAD 200,000 ✓). It steepens
sharply past r100 (NOT a flat +2%/round) and maxes ~round 500.

## 2. Feature — ground-truth round-scaled RBE

Late-game RBE is a full spawn-tree recompute: **every MOAB-class layer × v(r)** AND
**ceramics → superceramics** (60 HP shell + a single halved line of children → RBE
**68**, vs base ceramic 104). This reproduces the authoritative **BAD@100 = 67,200 RBE
to the unit** (`MOAB 552 → BFB 3,188 → ZOMG 18,352`; `28,000 + 2×18,352 + 3×832`).
`bloon_rbe_at_round()` + surfaced in the bloon-health reply, the round-economy reply
(`RBE 55,760 base → 67,200 on round 100`), and the MOAB-class grounding note.

**On the owner's "spawned bloons stay normal" steer:** close but not quite — the
spawned *MOAB-class* children DO scale (they pop on the same round, so they take v(r)
too; `body×1.4 only` gives 63,760, not 67,200). It's the *ceramic leaves* that don't
take ×1.4 — but they become superceramics. Walked the owner through the three candidate
models + the ground-truth figure before building.

## Validation

Health multiplier: 12/12 anchors exact (incl. r140=×5.0). `BAD@100`=28,000,
`fort BAD@140`=200,000, `BAD@100 RBE`=67,200 — all exact. Fortified RBE is model-derived
(429,920 vs the wiki's r140 fortified 430,300, ~0.09% — likely wiki rounding; standard
is exact, so standard is pinned and fortified is computed-not-pinned-against-wiki).
Sources: topper64.co.uk/nk/btd6/rounds (curve + superceramic 60 HP) · BAD / Round 140
wiki anchors. Full CI mirror green (12,190 passed).

## 💡 Session idea (Q-0089)

**Programmatic drift-check of curated freeplay/scaling data against topper64.** This
whole two-PR arc started because a *user noticed a wrong answer*. NK rebalances freeplay
periodically (the curve itself changed across patches). A small test/routine that samples
a few (bloon, round) pairs and asserts our `bloon_scaling.json` + `bloon_rbe_at_round`
match topper64's published calculator values would catch a future NK rebalance as a red
test instead of a user complaint — the same "executable oracle" discipline as the round-XP
and RBE recompute tests, extended to an *external* ground truth. (Dedup-checked
docs/ideas/ + roadmap: no existing entry for external-source drift-checking.)

## ⟲ Previous-session review (Q-0102)

Reviewed **2026-06-23-btd6-bloon-health-round-scaling** (#1384 — my own predecessor).
**Did well:** clean root-cause fix (base-only data → model flattens the BAD), validated
the r100 anchor to the unit, reused the `round_xp.json` curated-sidecar pattern, and was
*honest in the data file* that the r>100 brackets were unverified. **What it missed:** it
*shipped* those unverified brackets anyway — and they were wrong (×2.38 vs the real ×5.0
at r140), so a "BAD on round 140" answer would have been ~2× low. **System improvement
(applied this session):** when a formula has a "verified at one point, unverified beyond"
shape, don't ship the unverified tail — either **restrict to the verified range** or
**get a second anchor first**. One anchor (r100) under-determined the curve; the second
(r140) was what exposed and fixed it. Good rule for any curve/scaling data: *N unknowns
need N+ anchors before shipping.*

## Doc audit (Q-0104)

`check_current_state_ledger --strict` exit 0 (benign newest-merge lag, Q-0166);
`check_docs --strict` passed. The corrected curve + RBE capability are in their durable
homes (the `bloon_scaling.json` `scaling_source` note, the gamedata-dictionary
"Runtime-formula facts" section — updated this session, and this log). Ledger entry for
#1387 lands via the next reconciliation pass (no placeholder — Q-0052). Note for the
ledger: **#1387 fixes a data bug in #1384** (wrong r>100 health brackets).
