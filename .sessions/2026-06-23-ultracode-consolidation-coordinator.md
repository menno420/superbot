# 2026-06-23 — Ultracode consolidation fleet (coordinator)

> **Status:** `in-progress` — born-red coordinator card (Q-0133). Phase 0 verified green; Phase 1
> fleet dispatched (U1 ai · U2 roles · U3 games · U3b casino/cleanup); Phase 2 reconcile + the
> `edit_in_place` warn→error graduation land here as the deliberate final step. LEAVE RED until the
> fleet PRs merge and `check_consistency.py` reports `edit_in_place=0`.

> **Run type:** `manual · ultracode-coordinator`

## Role

Coordinator session for the consolidation/discoverability fleet
(`docs/planning/consolidation-fleet-plan-2026-06-23.md`). I own **Phase 0 (verify rails)** + **Phase 2
(reconcile + merge + rule graduation)**; the worker agents own their Phase-1 leaves. I do **not** write
feature code in worker file sets.

## Phase 0 — pre-flight (verified before dispatch)

- Synced to `origin/main` @ `cac321a` (#1374). 0 open PRs.
- `disbot/views/hub_children.py` present (`discover_hub_children` + `HubChildButton`).
- `check_quality.py --full` → **12119 passed**, all checks ✓. `check_architecture --mode strict` → only
  known WARN items, no errors.
- Live `check_consistency.py`: **edit_in_place=36** — `views/ai/` 17 · `views/roles/` 16 · casino 2 ·
  cleanup 1 (matches the snapshot).
- Lane overlap: U1/U2 clean; U3 (`views/games/`) overlap is only #1371's Phase-0 hub delegation
  (expected — U3 is the planned drop-in follow-on); U3b cleanup overlap is the recent cleanup-panel UX
  PRs (#1359/60/63), the 1 finding survived → still valid.
- `!temproles` confirmed still the **1 live reachability GAP** (#1371 didn't actually close it) → U2's
  fix is real.

## Phase 1 — dispatched fleet (file-disjoint, born-red, coordinator-merged)

| Unit | Branch | Owned files | Task | PR |
|---|---|---|---|---|
| U1 AI | `claude/u1-ai-inplace-nav` | `views/ai/` (+ `cogs/ai*`) | 17 `edit_in_place` → 0 (in-place nav) | _pending_ |
| U2 Roles | `claude/u2-roles-inplace-nav` | `views/roles/` + `cogs/role*` | 16 `edit_in_place` → 0 + `!temproles` gap | _pending_ |
| U3 Games | `claude/u3-games-hubchildbutton` | `views/games/` | migrate child-buttons → `HubChildButton` | _pending_ |
| U3b tail | `claude/u3b-casino-cleanup-tail` | `views/casino/` + `views/cleanup/` | 3 `edit_in_place` → 0 | _pending_ |

## Phase 2 — reconcile (filled as PRs land)

_(per-PR diff scope check, green-on-latest-head, fix misses, flip card, merge; then graduate
`edit_in_place` warn→error once `check_consistency.py` reports 0, reconcile `current-state`, GC claims.)_

## 📤 Run report

_(filled at close-out)_
