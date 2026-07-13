# Idea — give the S4-docs sector's reconciliation-pass history the same trim ratchet as current-state.md

> **Status:** `ideas` — captured 2026-07-13 (Q-0089) by the forty-sixth reconciliation pass
> (band-#2070). Routing: **S4 docs system / tooling**. Small, safe, in-repo.

## The gap (observed this pass)

`docs/current-state.md` ▶ Recently-shipped is bounded at 20 by `scripts/trim_recently_shipped.py`
(with `check_docs` enforcing the ratchet) — the routine calls it every pass and the oldest bullets
flow to the archive. Its per-sector sibling **`docs/current-state/S4-docs.md` has no equivalent
bound**: every pass appends a new "**Nth Q-0107 reconciliation pass**" bullet to its Recently-shipped
list and nothing ever trims it. As of this pass the list holds **21** pass bullets and grows by one
every ~30 PRs — pure unbounded accumulation of `historical` prose that each session re-reads on
orient.

Each pass already has a durable, canonical home for its full detail: its own
`docs/planning/reconciliation-pass-YYYY-MM-DD-bandN.md` record. So the S4 sector list only needs the
most-recent ~6–8 pass bullets inline; older ones are fully recoverable from the pass records + git.

## The fix (one small slice)

- Extend `trim_recently_shipped.py` (or a thin `trim_sector_pass_history.py` companion) to bound the
  S4-docs.md reconciliation-pass bullet list to ~8, dropping the oldest to a one-line "older passes:
  see `docs/planning/reconciliation-pass-*.md`" pointer (the records are already the source of truth).
- Have the reconciliation routine call it alongside the existing trim, so the sector list self-bounds
  every pass with zero extra owner/agent effort.
- Optionally a `check_docs` soft-warn when the S4 pass list exceeds the cap (belt-and-suspenders;
  the trim call alone keeps it in range).

## Why it's worth having

Orientation cost: S4-docs.md is on the task-specific reading route, and 21 near-identical pass bullets
is exactly the kind of low-signal accumulation the orientation-cost-reduction plan targets — the fix
is one small trim slice that keeps the next session's read lean, using machinery that already exists.
It also closes a genuine *inconsistency*: the hub ledger self-trims, its sector mirror does not.
