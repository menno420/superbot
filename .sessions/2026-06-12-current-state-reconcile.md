# 2026-06-12 — current-state drift reconcile + permissions posture doc

> **Status:** `audit`

**PR:** opened this batch (current-state reconciliation)
**Branch:** `claude/current-state-drift-reconcile`

## Context

Maintainer asked, at session close, whether anything important from this session is
undocumented. An audit found a live drift bug in `current-state.md`.

## What was done

- **Fixed `current-state.md` drift (bug-first).** Verified PR numbers against live GitHub:
  #730 = Hermes installable skills (mine), #731 = untested-surface checklist (other session),
  #733 = workflow/memory/permissions (mine). The ledger **mislabeled** the untested-surface
  entry as #730 (it is #731) and was **missing** #730 and #733. Relabeled #731 and added the
  two missing merges (newest-first).
- **Documented the permissions posture** (Part 4 in `claude-code-hooks-and-plugins.md`) — its
  durable home. `acceptEdits` + curated allowlist + the `ask` guards + the deliberate
  prompt-as-injection-guard rationale + the env-mode note. Previously only in a session log.

## Verification

- `check_docs --strict` ✓. Docs-only.

## Grooming move

None this batch — the audit *was* the grooming (surfaced + fixed a real drift bug rather than
moving a backlog idea). Backlog already groomed in the #730/#733 batches this session.

## ⟲ Previous-session review (Q-0102 — reviewing the #733 batch)

- **What it did well:** shipped the Q-0102/Q-0103 rules + the enforcement hook + the
  permissions cut, all gated green, batched into one push (applying #730's own review lesson).
- **What it missed:** it did **not** update `current-state.md` to reflect #730/#733 — the exact
  "when work ships, update the ledger" step — which is the drift this batch just fixed. Mildly
  ironic given #733 was *about* workflow rigor.
- **System improvement surfaced:** the session-close gate checks the *log*, but nothing checks
  that **merged PRs land in the `current-state.md` ledger**. A ledger-reconciliation check
  would have caught this automatically. → captured as this session's 💡 idea.

## 💡 Session idea

**Idea:** A `check_current_state_ledger.py` (or a `check_docs` extension) that flags merged
PRs from `git log origin/main` whose `#number` is absent from `current-state.md` § Recently
shipped.
**Why:** `current-state.md` drift (missing/mislabeled merged PRs) is a recurring class — it
happened *this very session*. The log-completeness gate (Q-0089/Q-0102) made the *session log*
self-checking; this does the same for the *living ledger*, the second-most-read doc. Advisory
(non-blocking), git-driven, pure stdlib like `check_docs`. Closes the last unchecked corner of
the memory system. _Small — recorded here; promote to an idea file if it grows._
