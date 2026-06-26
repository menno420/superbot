# 2026-06-26 — Meta-check: every "run-at-close" checker must be wired into /session-close

> **Status:** `complete`
> **Run type:** routine · dispatch
> **Branch:** `claude/funny-franklin-kmsak8` · **PR:** #1479

## What was done
Scheduled dispatch, empty work order → next plan slice. Built the previous run's Q-0089
session idea (PR #1477): a meta-check that closes the drift class #1476/#1477 hit — a
checker authored "to be run at session close" that silently lacks an invocation site (a
guard nobody runs is useless).

- **`scripts/check_session_close_gate.py`** (new) — asserts every checker declaring the
  distinctive `[session-close-gate]` sentinel is referenced in the `/session-close` SKILL.md
  **Step-4** block (FORWARD), and that every `scripts/check_*.py` referenced in Step-4 exists
  on disk (REVERSE — catches dangling/renamed-checker references). Read-only, stdlib,
  `--strict`/`--quiet`, Q-0105 provenance+kill-switch header.
- **Sentinel retrofitted** onto the 7 close gates: `check_docs`, `check_session_log`,
  `check_current_state_ledger`, `check_plan_code_drift`, `check_sector_next_freshness`,
  `check_reconciliation_due`, and the meta-check itself (it guards the block → it belongs in
  the block; self-referential closure).
- **Wired the meta-check into `/session-close` Step 4** so every session runs it.
- **`tests/unit/scripts/test_check_session_close_gate.py`** — 9 tests (live-repo-passes,
  block isolation, ref extraction, forward/reverse findings, missing-skill error).
- **Fix-on-sight (Q-0166):** `check_sector_next_freshness.py`'s provenance said it's "NOT
  wired into CI — run it by hand"; #1477 had wired it into `/session-close` Step 4 — corrected
  the stale line.
- **Grooming (Q-0015):** promoted the #1477 "left-open / option (b)" note into a tracked idea
  (`docs/ideas/dispatch-menu-suppress-shipped-lanes-2026-06-26.md` + README index entry).

**Design deviation from the idea (CLAUDE.md "take the better implementation, say why"):** the
idea proposed grepping for the Q-0105 provenance phrasing. That over-matches — many `check_*.py`
mention "session close / reconciliation routine" in headers without being Step-4 gates. A
dedicated `[session-close-gate]` sentinel is low-false-positive and explicit.

## Decisions recorded
none (no owner decisions; self-initiated mechanism work under Q-0172).

## Left open / next session
- Nothing open for this slice.
- A second slice was assessed and deliberately not built this run: the only clean offline
  lanes were either blocked (procedures→skills Batch 2 edits CLAUDE.md = off-limits to an
  autonomous run, Q-0106; BTD6 offline anchor tail is "none cleanly offline"; both
  rootfix-backlog bugs are owner-/data-gated) or convention-dependent (dispatch_menu
  shipped-lane suppression — groomed into an idea above rather than bolted on as fuzzy
  multi-link logic). Honest natural boundary, not an early stop.

## Verification
- `python3.10 scripts/check_session_close_gate.py` → OK (7 gates wired, 0 dangling).
- `python3.10 -m pytest tests/unit/scripts/test_check_session_close_gate.py` → 9 passed.
- `python3.10 scripts/check_quality.py --full` → **12637 passed**, 48 skipped, 2 xfailed.
- `python3.10 scripts/check_docs.py --strict` → all checks passed.
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors (2 pre-existing WARNs in
  `disbot/views/`, untouched by this PR).

## 💡 Session idea (Q-0089)
**Idea:** generalize the `[session-close-gate]` sentinel into a **gate-taxonomy** — every checker
declares which gate(s) invoke it (`[ci-gate]` / `[session-close-gate]` / `[reconciliation-gate]` /
`[stop-hook]`), and one meta-check (`check_gate_wiring.py`) asserts each declared gate actually
references the checker (Step-4 block, `code-quality.yml`, the reconciliation routine prompt, the
Stop hook). **Why:** today's meta-check only covers the session-close gate; the "guard authored
but never invoked" class exists for *every* gate type (a checker meant for CI but never added to
`code-quality.yml` is the same drift). One taxonomy + one meta-check would catch it everywhere,
and would make a checker's intended invocation site self-documenting in its own source.

## ⟲ Previous-session review (Q-0102)
The previous slice (#1477) did the right thing — it caught its own predecessor's omission
(#1476 shipped a checker with no caller) and wired `check_sector_next_freshness` into
`/session-close`, then explicitly proposed *this* meta-check as its Q-0089 idea. That chain
(find drift → fix → propose the class-level guard → next run builds it) is the self-improving
loop working as designed. What it left slightly imperfect — and this run fixed on sight — was a
**stale provenance comment**: it wired the checker into Step 4 but left the checker's own header
saying "NOT wired into CI — run it by hand," so the source contradicted the new invocation.
**System improvement surfaced (now acted on as this run's Q-0089 idea):** wiring a checker into a
gate should update the checker's self-described invocation site; the gate-taxonomy sentinel makes
that link machine-checkable so a checker can never again claim "nobody runs me" while a gate does.

## 📤 Run report
- **Run type:** routine · dispatch
- **PR:** #1479
- **⚑ Self-initiated:** built `scripts/check_session_close_gate.py` (the meta-check) + sentinel
  retrofit + `/session-close` wiring + groomed the dispatch_menu-suppression idea — no
  dispatch/owner ask (Q-0172, the previous run's flagged Q-0089 idea); flagged for owner
  review/revert. It is a disposable convenience guard (Q-0105) — delete it if it proves noisy.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none
