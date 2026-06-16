# 2026-06-16 — Night work queue for the dispatch routine

> **Status:** `complete`

## Shipped

- **`docs/planning/night-queue-2026-06-16.md`** — 5 ordered + 2 buffer slices,
  each a read-only deterministic BTD6 floor builder (AI §7.5/§7.6 lane,
  data-complete today, Q-0048, closes the BUG-0009 class). Turn-key per slice:
  question shape · data field · service fn · test file · dispatch-shadowing note.
- **`docs/current-state.md`** — ▶ NIGHT QUEUE pointer added (scheduled fires read
  it first); makes the `plan-first` "AI §7 next family" lane concrete + buildable.
- **`docs/owner/active-work.md`** — claim line.
- PR **#997** (auto-merge armed) — must land on `main` before 00:00 UTC so the
  first night fire reads the repointed ▶ Next action.

## Context delta

- **Needed but not pointed to:** the mechanism "a scheduled fire reads
  `current-state.md` ▶ Next action *from `origin/main`* after a hard reset" is the
  load-bearing fact for directing routines — it lives in
  `operations/autonomous-routines.md` + `hermes-dispatch-bridge.md`, not in the
  orientation route. To *direct* the fleet you must land the pointer on `main`, not
  just a branch. Worth a one-line pointer in AGENT_ORIENTATION's "how the routines
  pick work" path.
- **Pointed to but didn't need:** the big band-#930 decade queue prose — the
  buildable detail I needed was in the data files + the shipped builders, not the
  plan narrative.
- **Discovered by hand:** `check_current_state_ledger` is **not** a CI gate (only
  `check_docs --strict` + `check_session_gate` run in `code-quality.yml`), so a
  docs PR can auto-merge with pre-existing ledger drift outstanding — the strict
  ledger guard is a session-close advisory, not a merge blocker.

## Decisions made alone

- Made the otherwise-`plan-first` "AI §7 next workflow family" lane the night
  queue's content (vs. inventing a new lane) — it is the one ungated, proven,
  data-complete runtime backlog. Each slice = one PR, ordered easiest/most-proven
  first (hero/power cost comparison before the rosters).
- Left the pre-existing 4-PR ledger drift (#990/#991/#981 + 1) for the
  auto-reconciliation routine (Q-0124: manual sessions don't run the recon pass).

## Flagged for maintainer

- This *directs* the fires but is only as good as the lane: each builder is
  read-only deterministic (no prod-check), but the **cue/shadowing tuning** is the
  real care point — the exclusivity invariant (`test_btd6_floor_builder_exclusivity`)
  is what keeps a new builder from firing on a sibling's question. Each fire must
  add its corpus phrase.

## 💡 Session idea

A tiny `scripts/next_night_slice.py` that reads the night-queue table + the live
ledger and prints the topmost un-shipped `TODO` slice (the machine version of
"pick the topmost TODO") — so a fire never mis-picks an already-built slice and the
self-chaining is deterministic, not prose-judged. Filed under the dispatch-tooling
idea family (sibling to `dispatch_menu.py`).

## ⟲ Previous-session review

The previous run (control-API mutation endpoints, #993) did the write-side cleanly
over the audited seams — good seam discipline. What it (and the band) left thin:
the *ready* runtime queue, which is exactly why an empty scheduled fire had nowhere
obvious to go. **System improvement:** the gap is that "what does an empty scheduled
fire build?" had no durable, grounded home — `current-state` ▶ Next action pointed
at `plan-first` abstractions, not buildable slices. A standing **night-queue doc**
(refreshed when a lane thins) is the durable fix; this session creates the first
one. Worth promoting the *pattern* (a kept-fed buildable queue for empty fires) into
`autonomous-routines.md` so future thinned-queue moments don't strand the fleet.

## 📤 Run report

- **Did:** seeded a grounded night-work queue (5 BTD6 floor-builder slices) + repointed `current-state` ▶ Next action so the overnight scheduled fires self-chain real bot-section work · **Outcome:** shipped
- **Shipped:** #997 — night queue doc + ▶ Next action repoint + claim (docs-only, auto-merge armed)
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none` — auto-merges on green; the scheduled dispatch fires pick it up from `main` automatically (no console/Railway change). *(If you want it live before 00:00 UTC, just confirm #997 merged.)*
- **↪ Next:** the scheduled dispatch fires advance the [night queue](../docs/planning/night-queue-2026-06-16.md) — topmost `TODO` first (hero cost comparison), one PR each, re-pointing ▶ Next action as they go.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#997, pending auto-merge) |
| CI-red rounds | 0 |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (`next_night_slice.py`) |
| Ideas groomed | 0 |

**Arc:** Owner directive (in-session) — seed a *grounded* night-work queue so the
~4 scheduled dispatch fires overnight (`0 */2 * * *` → 00:00/02:00/04:00/06:00 UTC,
"including that from 12am") advance genuinely useful **bot-section (`disbot/`
runtime)** work instead of stalling on the thinned `ready` queue.

**What I'm about to do:** land a turn-key [night queue](../docs/planning/night-queue-2026-06-16.md)
of independent, read-only deterministic BTD6 floor builders (the proven
#946/#950/#955/#962/#975 lane) + repoint `current-state.md` ▶ Next action at it, so
each scheduled fire (which `git reset --hard origin/main` then reads ▶ Next action)
picks the topmost unbuilt slice and self-chains.
