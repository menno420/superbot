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

**Part A — `active-work.md` → one file per claim (the conflict fix).**
- New `docs/owner/claims/` directory: `README.md` (the convention — explicitly **no shared
  hand-edited index**, discover via `ls`) + one file per active claim (`<branch>.md`, deleted at
  close). `active-work.md` is now a `reference` pointer stub.
- `scripts/check_lane_overlap.py` reads the directory (`_load_claims` iterates `claims/*.md`, README
  excluded; new `parse_claim_file` / `_build_claim` / `_bullets_to_claims` helpers; `parse_claims`
  kept for the legacy block). +6 tests (18/18 green).
- `scripts/check_docs.py` excludes the transient claim files from the census (same lifecycle as
  `.sessions/` logs) — only `claims/README.md` is a real doc.

**Part B — GC failsafe.**
- `scripts/check_stale_claims.py` (+5 tests) — flags/`--prune`s claim files whose branch is
  gone/merged; injectable `state_fn` keeps the logic git-free for tests; Q-0105 disposable header.
- Wired into the docs-reconciliation routine (`autonomous-routines.md`) as a GC step.

**Part C — `current-state.md` → per-sector live state (discoverability).**
- New `docs/current-state/` with `README.md` + `S1-bot`/`S2-btd6`/`S3-ai-memory`/`S4-docs`/`S5-ops`
  snapshots. The hub's all-sector `▶ Next action` blockquote → a compact per-sector pointer table
  (callout 267 chars, was ~6000). Hub keeps `## Recently shipped` + the ledger marker (ledger
  checker unaffected).

**Provenance.** Router **Q-0195**; CLAUDE.md Q-0126/Q-0189 claim-convention references updated
(owner-directed in-session → Q-0106 carve-out). Evidence artifact kept at
`tools/sim/claim_layout_sim.py`. CI mirror green (black/isort/ruff/check_docs/check_consistency/mypy);
PR #1283.

> **⚑ Self-initiated:** none — owner-directed in-session ("implement both"); merge on green, no
> `needs-hermes-review`.

## ⟲ Previous-session review

Previous session (`2026-06-22-friction-to-guard-reflex`, Q-0194) did well to build *both* halves of
the owner's ask — the concrete wrong-branch hook **and** the systemic "friction → guard" reflex —
rather than just the narrow fix. What it could have done better: it left a **DISCUSS proposal** to
elevate the friction→guard reflex into CLAUDE.md but didn't act, which is correct under propose-first
— yet this session shows the complementary lesson: *when the owner directs a workflow change
in-session, the Q-0106 carve-out lets you apply it directly.* **System improvement surfaced:** the
born-red card + the "open PR in ~2 min" rule (Q-0189) are in tension with a large multi-part session
like this one — the PR opened with only the card + scaffolding, which is correct, but the
*claim* mechanism it was changing was the very thing being restructured. A small future guard:
`check_lane_overlap.py` could warn when a session's own branch has **no** claim file (catch the
"forgot to claim" case the new per-file system makes silent — no shared list to eyeball).

## 💡 Session idea

**Idea — `dispatch_menu.py --sector-state` reads the new per-sector `current-state/` files.** Now
that live per-sector state is one file per sector, the dispatch resolver
(`scripts/dispatch_menu.py`) could surface each sector's `▶ Next startable` directly from
`docs/current-state/S*.md` instead of re-deriving it from the roadmap — making "dispatch S2" a
one-file read. Worth having because it closes the loop between the discoverability split shipped here
and the machine dispatch path; small, stdlib, testable. (Dedup-checked `docs/ideas/` + roadmap — not
already present.)

