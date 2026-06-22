# 2026-06-22 — Repo navigation cleanup: stale claims + conflicting instructions

> **Status:** `in-progress` — owner-directed cleanup pass. The maintainer reports the repo
> "feels a little messy" after a burst of merges + the now-mostly-fixed merge problems, and
> wants it easy to navigate and work in **without conflicting claims or instructions**.
> Owner-directed (Q-0191) → merge immediately on green; no `needs-hermes-review`.

> **Run type:** `manual · owner-directed`

## What I'm about to do

A docs/orientation hygiene pass (no `disbot/` runtime code). Confirmed + candidate scope:

- **Prune stale `active-work.md` claims.** Both "Active claims" are merged work:
  `claude/modest-gates-0ble76` (CI-strand fix → **#1267 merged**) and
  `claude/funny-franklin-mjvqrx` (BUG-0023 → **#1272 merged**). The claim ledger is the
  early duplicate-work signal — stale claims defeat its purpose (Q-0166 drift-on-sight).
- **Reconcile genuinely conflicting / contradictory instructions** surfaced by a docs sweep
  across `.claude/CLAUDE.md`, `.claude/rules/`, `docs/collaboration-model.md`, the journal,
  `docs/owner/*`, and the binding contracts — where a reader can't tell which guidance is
  current. CLAUDE.md *content* stays propose-not-edit unless the owner directs the specific
  change in-session (Q-0106); anything load-bearing there → a router DISCUSS Q, not a self-edit.
- **Remove resolved-but-still-present merge/CI scaffolding** cluttering active reading paths,
  now that the merge problems are mostly fixed.

## What shipped

_(in progress)_
