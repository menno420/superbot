# Idea — a shared `docs_ledger` markdown-parsing helper (one source of truth for the ledger regexes)

> **Status:** `ideas` — captured 2026-06-16 (Q-0089 grooming-promotion). First surfaced in the
> developer-dashboard session (#967) as a Q-0089 idea recorded only in its `.sessions/` log;
> promoted here into the backlog so it isn't orphaned. Small/decided-lane refactor. Area: repo
> tooling (`scripts/` checkers + the dashboard exporter).

## The gap

The repo's markdown ledgers (`.sessions/` Status badges, `docs/health/bug-book.md` `## BUG-NNNN`
headings, `docs/ideas/*.md` title/Status/date) are *almost* machine-readable, but **every consumer
re-implements the extraction**, and the regexes have already started to drift-by-copy:

- `scripts/export_dashboard_data.py` `_STATUS_RE` carries the comment *"Mirrors
  scripts/check_session_gate.py"* — a literal copy, kept in sync by hand.
- `scripts/check_session_gate.py`, `scripts/check_session_log.py`, and `scripts/check_docs.py`
  each re-derive "parse a Status badge / a `BUG-NNNN` entry / an idea file" themselves.
- `scripts/scan_env_usage.py` (this session) is a *new* consumer of the same "scan the repo's
  structured data" principle, reinforcing that the pattern is reusable.

Two copies of one regex is a latent bug: a fix to the badge grammar (e.g. a new terminator) lands
in one checker and silently not the other, and the dashboard then disagrees with the merge gate
about what "complete" means.

## The idea

Extract the shared parsers into **one tiny stdlib module** — `scripts/_docs_ledger.py` (or
`tools/docs_ledger.py`) — with a single home for: `status_badge(text)`, `iter_bug_entries(text)`,
`iter_idea_files(dir)`, and the `YYYY-MM-DD`-from-name helper. Every checker and the dashboard
exporter import it. One regex, one set of unit tests, no drift.

## Why it's worth having

- **One source of truth** for the ledger grammar — the repo's standing value, applied to its own
  tooling. The "surface the repo's data" principle (dashboard, env scanner) becomes a reusable
  primitive instead of N parallel re-implementations.
- The dashboard and the merge gate provably agree on what a Status badge *is*.

## Caveat / sequencing (why it wasn't built in #967 or #969)

`check_session_gate.py` is the **born-red merge gate** — the very check a `claude/*` session's own
PR merge depends on. Refactoring it in the same session whose merge it gates is poor risk
discipline (a regression deadlocks your own PR). **Build this in a session that does not depend on
`check_session_gate` for its merge** — e.g. a docs-reconciliation routine PR (workflow-authored,
never adds a session card, so the gate doesn't engage), or with the extraction landed and verified
*before* the session card flips to `complete`. Keep it behaviour-identical (golden tests: the new
helper's output byte-matches each old call site on the live repo before the swap).
