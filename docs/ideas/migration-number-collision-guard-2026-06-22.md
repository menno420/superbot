# Idea: pre-merge migration-number collision guard (kill the renumber treadmill)

> **Status:** `ideas` — **Option 1 SHIPPED** 2026-06-22 (`scripts/check_migration_collision.py`,
> dispatch grooming run); Options 2 (merge-aware local mirror) + 3 (assign-number-at-merge) remain.
> Source code and the binding contracts win over this file. **Subsystem:** none (cross-cutting dev
> tooling / CI).

**Captured:** 2026-06-22 · **Source:** reaction-roles PR 6 (#1279) — a held
`needs-hermes-review` PR whose migration was renumbered **four times** (085→086→088→089)
in one afternoon as the active routine fleet kept appending the next number to `main`. ·
**Lane:** small / decided — implementable.

## The problem it solves

Migrations are numbered `NNN_name.sql` and the number is a **single shared append point**:
the next free integer above the highest on `main`. Under a fast multi-session fleet, several
PRs in flight all pick the *same* next number, and whichever merges first wins — every other
PR now has a **duplicate migration number** against `main`.

Two things make this especially painful for a **held** PR:

1. **CI tests the *merge result*** (`refs/pull/N/merge`), so `test_migrations_runner` /
   `test_migrations_structure` fail on the duplicate — but a **branch-only local**
   `check_quality.py --full` run **passes** (it never merges with `main`), so the author
   gets a green local signal and a red CI with no obvious cause.
2. The fix (renumber + re-merge) takes longer than the fleet's inter-migration interval, so
   by the time CI re-runs, `main` has appended *another* migration and the collision recurs.
   #1279 hit this four times in a row.

## Sketch (any one of these; the first is the cheapest, highest-value)

1. **A `scripts/check_migration_collision.py`** (stdlib, read-only): fetch `origin/main`,
   compare the branch's *new* migration numbers against it, and on a collision print the
   **next free number** + the exact `git mv` + `sed` to renumber. Wire it into the Stop hook
   (advisory) and/or a `pre-pr` step so the author sees it **before** pushing — not after a
   4-minute CI round-trip. (Disposable, Q-0105.)
2. **Make the local CI mirror merge-aware:** have `check_quality.py --full` optionally run the
   migration-structure tests against `HEAD` *merged with* `origin/main`, closing the
   local-green / CI-red gap that hides the collision.
3. **Bigger / structural:** assign the migration number at **merge time** (a merge-queue step
   renames `NNN_` → the then-current next free), or move off a globally-ordered integer to a
   per-PR token the runner orders by a manifest — removing the shared append point entirely.
   This is the real fix but a meaningful infra change (own plan).

## Why it's worth having

- It is a **recurring, measured tax** — four renumbers on one PR, and every migration-bearing
  PR pays some of it. Option 1 alone turns a 4-round CI treadmill into one local one-liner.
- Cheap, offline, read-only (option 1/2); option 3 is the durable cure when the fleet grows.

→ relates `disbot/utils/db/migrations.py` · `tests/unit/db/test_migrations_{runner,structure}.py` ·
`scripts/check_quality.py` · the `.sessions/2026-06-22-reaction-roles-pr6-pil-cards.md` saga.
