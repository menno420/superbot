# 2026-06-23 — Fishing: the `premature_grace` rod knob (the design's 5th knob)

> **Status:** `in-progress` — routine dispatch run, no work order → advance the next plan slice.

> **Run type:** `routine · dispatch`

## What I'm about to do

Fake-out bites are already shipped (`minigame.roll_fakeout` + the cast view's "you reeled too early —
the fish darted off" penalty). The fishing design
(`docs/planning/fishing-minigame-design-2026-06-22.md`) names a **fifth rod knob, `premature_grace`**,
that fake-outs were meant to "make meaningful" — but it was never built: every rod is equally, harshly
punished for an early reel. This slice adds it.

`premature_grace` (0…1) = the chance a **premature reel is forgiven** (the fish isn't spooked; the cast
survives and the real bite still comes). One forgiveness per cast (so it rescues an itchy-finger slip,
never rewards button-mashing). Scales up the ladder: bare 0.0 → diamond. Pure roll in
`utils/fishing/minigame.py`; the knob on `Rod` (`utils/fishing/rods.py`); the view spends the grace in
`views/fishing/cast_view.py`; surfaced in the rod-shop knob summary.

Also folding in **drift fixes I can see** (Q-0166): the S1 `▶ Next startable` line lists fake-out bites
as *remaining* when it shipped; the design "Other ideas" fake-out bullet isn't marked shipped; and 7
stale claim files for already-merged PRs (#1294/#1322/etc.) need GC.

## What shipped

_(filled at close)_
