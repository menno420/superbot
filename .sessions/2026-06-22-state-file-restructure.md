# 2026-06-22 — State-file restructure: per-claim active-work + per-sector current-state

> **Status:** `in-progress` — owner-directed. Two evidence-backed restructures of the
> coordination files: (1) convert `active-work.md` (the parallel-session claim ledger) from one
> shared append-list into **one file per claim** under `docs/owner/claims/`, killing the merge
> conflicts a git simulation measured at ~98%; (2) split `current-state.md`'s mixed all-sector
> `▶ Next action` blockquote into **per-sector live-state files** (`docs/current-state/S1..S5.md`)
> behind a thin hub, for dispatch discoverability. Owner-directed in-session → merge on green; no
> `needs-hermes-review`.

> **Run type:** `manual · owner-directed`

## Why (the simulation)

The owner asked whether per-sector or per-file is the better fix for claim-ledger merge conflicts,
and whether I could *test* it rather than assert. A real-`git merge` simulation
(`tools/sim/claim_layout_sim.py`) replayed concurrent sessions distributed by the **actual** sector
weights (S1 ~55%) under three layouts:

| concurrent sessions | status quo (1 shared file) | per-sector (5 files) | per-claim (1 file each) |
|---|---|---|---|
| 2 | 98.3% | 35.0% | **0.0%** |
| 3 | 98.3% | 56.0% | **0.0%** |
| 5 | 98.3% | 66.2% | **0.0%** |

Finding: **per-sector only half-helps and *worsens* with concurrency** (S1 clustering), while
**per-claim is structurally conflict-free** (disjoint file sets cannot conflict) — *provided there
is no shared hand-edited index*. So: `active-work.md` → per-claim (conflicts); `current-state.md` →
per-sector (discoverability, a different goal).

## What shipped

_(filled in as the work lands; flipped to `complete` as the final step)_

## ⟲ Previous-session review

_(end-of-session)_

## 💡 Session idea

_(end-of-session)_
