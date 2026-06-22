# 2026-06-22 — migration-number collision guard (kill the renumber treadmill)

> **Status:** `in-progress` — born-red card (Q-0133). Flips to `complete` as the final step.
> Routine · dispatch ("Continue from where you left off"; grooming-executes a logged idea).

## Arc

Four PRs already merged this session (#1305 React foundation, #1308 contract guard, #1317 ledger/CI
hygiene, #1320 tool-pin CI guard). Product lanes are gated (PR 2 cutover needs attended browser
verification; Project Moon ingestion is network/IP-sensitive; bug-book rootfix backlog = BUG-0009
data-gated + BUG-0019 owner design-fork) and the recon is the separate routine's job (Q-0124). So
this turn takes the **sanctioned grooming pick** (Q-0015): execute a small/safe/decided-lane idea —
`docs/ideas/migration-number-collision-guard-2026-06-22.md`, Option 1.

**Real recurring bug** (not busywork): migration files are `NNN_name.sql` numbered off a single
shared append point, so concurrent fleet PRs pick the *same* next number and collide against `main`.
#1279's migration was renumbered **four times in one afternoon** (085→086→088→089). CI tests the
merge result so it goes red, but a branch-only local `check_quality.py --full` passes (never merges
with main) — the author gets green-local / red-CI with no obvious cause.

This PR (Option 1 — the cheapest, highest-value):
1. **`scripts/check_migration_collision.py`** (stdlib, read-only): compare the branch's *new*
   migration numbers (working tree) against `origin/main`; on a collision print the next free number
   + the exact `git mv` to renumber, **before** the push/CI round-trip. Covers `disbot/migrations/`
   + `botsite/migrations/`. Pure `analyze()` core + thin git I/O. Disposable-guard header (Q-0105).
2. **Tests** — the pure analyzer (collision detect, next-free suggestion avoiding taken numbers,
   no-collision clean, multi-collision cascade, non-migration files ignored).
3. **Idea bookkeeping** — mark Option 1 done in the idea file (Options 2/3 remain).
4. **Stale-claim GC** — delete my merged-branch claims (`s56i3y-3`, `s56i3y-4`).

**Not wired into the Stop hook** (that's a hook edit, Q-0106 — owner-only). The script is standalone +
documented; a follow-up can wire it into `/pre-pr` (a skill, editable) or the hook (owner consent).

## Shipped

_(filled at close)_

## Session enders

_(filled at close)_
