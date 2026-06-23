# 2026-06-23 — BTD6 freeplay curve fix + ground-truth round-scaled RBE

> **Status:** `in-progress`

Owner-directed follow-up to PR #1384 (round-scaled bloon health). The owner chose
**"full ground-truth RBE"** + **"source the curve properly."** Two things:

## 1. Bug fix — the r>100 health brackets I shipped in #1384 are WRONG
#1384 shipped a `bloon_scaling.json` whose r≤100 bracket was cross-verified (BAD@100
= 28,000 ✓) but whose r>100 brackets were "documented but unverified" — and they're
wrong. Ground truth: a **fortified BAD on round 140 has 200,000 HP** = ×5.0 of its
40,000 base, but my shipped curve predicted ×2.38. Sourced the **authoritative
piecewise curve** from topper64's calculator, validated against BOTH anchors:
```
81–100:  1 + (r−80)·0.02     → r100 = 1.40  (BAD 28,000 ✓)
101–124: 1.4 + (r−100)·0.05
125–150: 2.6 + (r−124)·0.15  → r140 = 5.00  (fort BAD 200,000 ✓)
151–250: 6.5 + (r−150)·0.35
251–300: 41.5 + (r−250)·1.0
301–400: 91.5 + (r−300)·1.5
401–500: 241.5 + (r−400)·2.5
501+:    491.5 + (r−500)·5.0
```

## 2. Feature — ground-truth round-scaled RBE
Late-game RBE is a full spawn-tree recompute: **every MOAB-class layer ×v(r)** AND
**ceramics → superceramics** (60 shell + halved children → RBE **68**, vs base
ceramic 104). This reproduces the authoritative **BAD@100 = 67,200 RBE** *to the
unit*. (The owner's "spawned bloons stay normal" steer was close — the spawned
MOAB-class children DO scale, since they pop on the same round; it's the ceramic
leaves that don't take ×1.4, but they become superceramics.) Added
`bloon_rbe_at_round()` + surfaced in the economy/health replies.

Sources: topper64.co.uk/nk/btd6/rounds (health curve, superceramic 60 HP) · BAD wiki
(28,000/67,200 @ r100) · Round 140 wiki (200,000 HP fort BAD). Standard RBE validated
exact at r100; fortified RBE is model-derived (~0.1% vs the wiki's r140 fort figure,
likely wiki rounding).
