# 2026-06-16 — fix the ledger-file merge-conflict livelock (.gitattributes merge=union)

> **Status:** `in-progress` — born-red per Q-0133; flipped to `complete` as the deliberate
> final step. Config + card only (no `disbot/` runtime, no Python).

## What I'm about to do

Fix the **root cause** of the merge-conflict livelock PR #995 hit 3× this session: the append-only
coordination ledgers (`docs/owner/active-work.md`, `docs/ideas/README.md`) conflict whenever two
parallel sessions both add a line, because git can't auto-merge concurrent edits to the same region.
Under the maintainer's high parallel-session velocity, `main` merged a new entry into those files
faster than my merge→verify→push cycle could land, so the `conflict-guard` (Q-0154) kept re-firing.

**The standard fix:** mark those two files with git's **`merge=union`** driver via `.gitattributes`.
On a conflicting hunk, union takes **both** sides' lines (no markers, exit 0) instead of failing —
exactly right for append-only lists. **No convention change** (sessions still append claims/entries);
only git's *merge resolution* for those paths changes.

**Verified before shipping** (`git merge-file --union`): two sessions each prepending a different
claim → both kept, exit 0; the same case *without* union → exit 1 (conflict). So the driver is what
removes the conflict.

**Caveats (documented in the file):** union never deletes, so a *removed* claim on one side survives
the merge (stale line lingers → prune it, which the convention already allows), and near-identical
concurrent adds yield duplicates (visible/prunable). Acceptable for these ledgers; **not** applied to
files where order/uniqueness matters (the router's Q-numbers, current-state prose).

This PR touches **only** `.gitattributes` + this card — zero contended-file edits, so the fix can't
itself livelock.

## Status checklist

- [ ] append `merge=union` for active-work.md + ideas/README.md to `.gitattributes` (with rationale)
- [ ] sanity: `git check-attr merge` reports `union` for both paths
- [ ] `check_quality --check-only` (docs gate) green
- [ ] session enders + flip card `complete`
