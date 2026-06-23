# 2026-06-23 — Fishing bait speed knob

> **Status:** `in-progress`

**Run type:** routine · dispatch

## Plan

Empty-fire dispatch run (no work order). Synced live `main`, oriented (working
agreement → collaboration model → current-state → newest sessions → bug-book),
confirmed the open bugs are gated/owner (BUG-0009 data-gated, BUG-0011 needs a VPS
repro, BUG-0019 #1 owner design fork) and no open PRs are in flight. Picked the S1
▶ next-startable lane the previous session (bait layer #1329) explicitly teed up:
the **bait speed knob** — owner decision 4 named "faster bites" the clean future
knob on the same `CastStart`/cast-view seam the rarity knob already uses.

About to: add `Bait.bite_speed`, compound rod×bait bite-speed in
`fishing_workflow.begin_cast`, thread it through `CastStart` →
`FishingCastView._run_bite`; broaden the bait shelf (dedicated speed baits + a
premium combo) and show both knobs in the shop UI. No migration, no new command,
no artifact regen. Tests for the catalog, the workflow compounding, and the view
threading. CI mirror green + arch strict before flipping this card to complete.
