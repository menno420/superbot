# Idea — a stdlib actuator for the Recently-shipped trim-to-archive step

> **Status:** `ideas` — capture only. **Not a plan, not approval.** Session idea (2026-06-20, Q-0089,
> from the band-#1170 reconciliation pass). Workflow/tooling. Quick-win, disposable (Q-0105).
> **Subsystem:** none

## The observation

Every Q-0107 reconciliation pass ends with the same **mechanical, drift-prone** chore: the
`current-state.md` § Recently shipped list is soft-ratcheted at 20 (`check_docs.py`), so after adding the
band's new grouped entries the pass must **trim the oldest bullets into `current-state-archive.md`**. Doing
that by hand means: count the `- **#` bullets, decide which oldest N to move, cut them out of
`current-state.md`, paste them into the archive's "Recently shipped — archived" section, and **hand-update
the "Older merges (#X … #535)" floor pointer** so it still roughly names the live/archive boundary.

This pass did exactly that for 8 bullets. The pointer floor is the fragile part — the ledger's grouped
band bullets are **non-monotonic** (a band like `#1101 · #1121` carries a recent PR even though its base
number is old), so the "#X … #535" floor can silently misstate the boundary. `check_current_state_ledger.py`
catches a *missing* PR, but nothing catches a *wrong floor pointer* — it is prose.

## The idea

A small stdlib **actuator** — `scripts/trim_recently_shipped.py` (or a `--trim` mode on
`check_current_state_ledger.py`) — that, given the current `current-state.md` + archive:

1. Counts the live Recently-shipped bullets; if over the ratchet, moves the **oldest (bottom) N** bullets
   verbatim from `current-state.md` into the archive's archived section (newest-first, with a dated
   "trimmed by the Nth pass" note).
2. Recomputes and rewrites the **"Older merges (#X … #535)"** floor pointer from the actual lowest live PR
   number, so the pointer can't drift from reality.
3. Runs **idempotently** and prints a dry-run diff first (`--check` / `--apply`), so a pass can preview the
   move before committing.

It is the *actuator* complement to the existing `check_current_state_ledger.py` **detector**: the detector
says "a PR is missing"; this says "here is the exact, safe trim" and performs it.

## Why it's worth having

- Removes the single most error-prone step of every reconciliation pass (this pass spent real effort
  reasoning about which non-monotonic bullets to move and what floor to write).
- Makes the trim **deterministic and reviewable** (dry-run diff) instead of a hand edit of two files.
- Closes the unguarded "wrong floor pointer" drift class — a #763-style ground-truth gap (Q-0120) where a
  prose pointer silently disagrees with the actual ledger boundary.

## Disposability (Q-0105)

Disposable convenience tooling — if it mishandles the non-monotonic band bullets even once, **delete it**
and keep trimming by hand. It must never *delete* a bullet (only move), and the pass still runs
`check_current_state_ledger.py --strict` afterward as the real guard.

→ relates `scripts/check_current_state_ledger.py` · `scripts/check_docs.py` (`_recently_shipped_count`) ·
the reconciliation routine · `ideas/band-pr-merge-status-helper-2026-06-19.md` (the merged/closed/open
classifier this would consume).
