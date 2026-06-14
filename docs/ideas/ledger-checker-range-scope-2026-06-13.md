# Idea — scope the ledger guard's range-expansion to the Recently-shipped section

> **Status:** `historical` — **IMPLEMENTED 2026-06-14** (paired with the print-subjects slice) — shipped in
> `scripts/check_current_state_ledger.py`: `known_ledger_numbers` partitions `current-state.md`
> at `## Recently shipped` and expands `#AAA–#BBB` ranges only in that tail (+ the whole
> archive); individual `#N` refs still count everywhere. The convention mitigation stays good
> practice but is no longer load-bearing. Kept here as the implemented-idea record. Source code
> wins over anything below.

## The idea

`scripts/check_current_state_ledger.py` should expand `#AAA–#BBB` ranges into "present"
coverage **only when the range appears in the `## Recently shipped` section (or the
archive)** — not when it appears anywhere in `current-state.md`. Individual `#N` references
should keep counting everywhere (stamp lines legitimately cite them).

## Why (the bug that surfaced it)

The guard expands every range it finds *anywhere* in the file (`ledger_pr_numbers`). The
band-#800 pass found that a **forward-looking planning range** in the `▶ Next action`
pointer — the previous pass had written `(band #781–#800)` there — silently masked that
entire band from the guard the moment those 20 PRs merged. The checker reported **green
while the ledger was ~14 entries short** (the whole substrate-kit arc + the auto-merge
migration were never individually recorded). This is a *second, independent* false-green in
the same guard (the first was the 2026-06-12 "Merge PR #N:" regex blindness, fixed in #763).

The band-#800 pass mitigated it by **convention** (the live-queue pointer now references the
pass *by name*, never by an inline range — the range lives in the pass doc, which isn't
scanned). But convention is only as good as the next agent's discipline, and the masking
*recurs at every boundary* if a range ever lands in the top pointer again. A structural guard
is the durable fix.

## Sketch

- Split `current-state.md` text at the `## Recently shipped` header; expand ranges only in
  that tail + the full archive. Keep `_LEDGER_REF_RE` (individual `#N`) scanning the whole
  file so stamp-line refs still count.
- Add a test mirroring the failure: a `(band #900–#919)` range in a simulated `▶ Next
  action` block must **not** mark #905 present, while the same range in `## Recently shipped`
  must.

## Why this is an idea, not done here

The band-#800 pass is **docs-only / self-merge** — touching the guard's logic plus adding a
test is a runtime-lane change (the existing `tests/unit/scripts/test_check_current_state_ledger.py`
asserts `ledger_pr_numbers` expands ranges on bare strings, so the signature/behavior change
must update tests too). That belongs in a normal session, not a docs reconciliation. Small,
well-scoped, high-leverage (it re-arms a guard that the whole autonomous loop relies on to
catch ledger drift between passes).
