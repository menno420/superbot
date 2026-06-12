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
- **Built the ledger drift guard** (executing this session's 💡 idea). `scripts/check_current_state_ledger.py`
  (+ 9 tests) reads merged PR numbers from `git log origin/main` (expanding `#AAA–#BBB` range
  entries) and flags recent ones absent from `current-state.md` / `current-state-archive.md`.
  Advisory by default, `--strict` for `/session-close` (now wired into the skill's quality gate).
  It immediately surfaced **pre-existing** drift — #724–#728 (another session's readiness/roadmap
  arc) were in neither the ledger nor the archive — so reconciled those too with an aggregated
  range entry. `--strict` now clean (last 15 merges all present). This makes the *living ledger*
  self-checking, the way `check_session_log.py` made the *session log* self-checking.
- **Two new owner directives (voice).** **Q-0104** — close every session with a documentation
  audit (the "is anything undocumented?" question that found this drift; automated half =
  `check_current_state_ledger --strict` in `/session-close`, judgment half = the "only in chat?"
  sweep). **Q-0105** — adopt tooling freely without asking, but every adopted tool carries a
  "delete this if it proves unreliable over multiple sessions" kill-switch in its header
  (extends Q-0014). Applied the kill-switch header to `check_session_log.py` +
  `check_current_state_ledger.py` (dogfood). CLAUDE.md + router + `/session-close` updated.

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

> _The prior batch's 💡 idea — `check_current_state_ledger.py` — was **executed this batch**
> (idea → implemented in one hop). Fresh idea below._

## 💡 Session idea

**Idea:** Session-arc aggregation for the ledger — a convention (and a `check_current_state_ledger`
hint) that collapses the several small PRs of one conversation/session-arc into a single
aggregated `#AAA–#BBB` Recently-shipped entry, the way #685–#698 / #715–#723 / #724–#728 already
do, instead of one bullet per PR.
**Why:** this very session shipped #730 + #733 + #734 as three separate ledger bullets on one
topic-arc; the Recently-shipped ratchet (budget 20) stays leaner if same-arc PRs aggregate. The
checker already parses ranges, so it could detect "N consecutive merges from one session not yet
aggregated" and suggest collapsing them. Keeps the second-most-read doc scannable.
_Small — recorded here; promote to an idea file if it grows._
