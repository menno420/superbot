# Ledger dedup linter (companion to the merge=union fix)

> **Status:** `historical` — **SHIPPED** `scripts/check_ledger_hygiene.py` (2026-06-19) and
> **de-staled 2026-06-27** for the Q-0195 per-claim-file restructure: the claim half no longer scans
> the retired shared `active-work.md` "Active claims" section (now a pointer stub) — it scans the
> per-file `docs/owner/claims/*.md` directory and flags a `claude/<branch>` claimed by more than one
> file. The idea-index dedup half is unchanged. Captured 2026-06-16 (session idea, Q-0089, from the
> merge=union fix #1003). Source + merged PRs win.

## The gap

PR #1003 marked the two append-only coordination ledgers — `docs/owner/active-work.md` (claim ledger)
and `docs/ideas/README.md` (idea index) — with git's **`merge=union`** driver, so concurrent appends
from parallel sessions auto-merge instead of conflicting (the livelock #995 hit 3×). That fix has one
known, accepted downside: **union never deletes and never dedups**. So over time it can leave:

- a **stale claim** in `active-work.md` (a claim a session removed on its branch survives the merge
  because the other side didn't touch that line), and
- a **duplicate** entry (two sessions that add near-identical claim/idea lines both land).

The convention already permits pruning these by hand ("stale lines are fine to prune when you see
them"), but nothing *surfaces* them — so they accumulate silently until someone notices.

## The idea

A tiny stdlib **`scripts/check_ledger_hygiene.py`** (or a `check_docs` sub-rule) that reports:

- **Duplicate claim branches** in `active-work.md` — the same `` `claude/<branch>` `` appearing twice
  under Active claims.
- **Duplicate idea-file links** in `ideas/README.md` — the same `./<file>.md` linked twice.
- *(Optional, higher-value)* **merged claims still in Active** — a claim whose branch corresponds to a
  merged PR (cross-reference is harder offline; keep this advisory).

Report-only by default (exit 0 + a list), with a `--strict` that fails CI on a duplicate. It pairs
with #1003: union keeps the ledgers conflict-free, this keeps them *clean*.

## Why it's worth having

- Closes the one real downside of the union fix — without it, the ledgers slowly fill with cruft.
- Pure stdlib, read-only, disposable (Q-0105) — same lane as the other `check_*` scripts.
- Cheap: duplicate detection is a few lines of parsing the two well-structured lists.

## Disposition

Decided-lane, small → **execute when the dashboard/tooling lane next has capacity** (a few-line linter
+ a test). Wire to CI only after it proves reliable across a few sessions (Q-0105). → relates
`docs/owner/active-work.md` · `docs/ideas/README.md` · `.gitattributes` (the union driver) · #1003.
