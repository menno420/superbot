# 2026-06-12 — Reconciliation + planning cadence at every 10th PR (Q-0107)

> **Status:** `audit`

**PR:** opened this batch (Q-0107 cadence rule)
**Branch:** `claude/reconciliation-cadence-rule`

## Context

Owner directive (voice), final rule of the session: every 10th PR (#10, #20, #30, … — multiples
of 10) should be a **docs-only review + planning** pass that reviews repo state and refocuses;
and **every planning pass focuses on what the next ~9 PRs can realistically achieve — modular but
not over-segmented; each PR ships a reasonable change unless it really is a small required one.**

## What was done

- **Q-0107 (binding cadence rule).** `.claude/CLAUDE.md` § Session & plan workflow: PRs crossing a
  multiple of 10 are a docs-only pass that **(1) reconciles** (ledger, lanes, Q-blocks, ideas,
  roadmap; prune stale; restate priorities) and **(2) plans the next ~9 PRs** (realistic, modular,
  not over-segmented; reasonable change per PR). Router Q-0107.
- **`scripts/check_reconciliation_due.py`** (+ 9 tests): cadence guard — flags when merged PRs have
  crossed into a new multiple-of-10 band since the `Last reconciliation pass:** PR #N` marker in
  `current-state.md`. Advisory; `--strict` for the gate. Carries the Q-0105 kill-switch header.
  Wired into `/session-close`.
- **Marker set** in `current-state.md` (`Last reconciliation pass: PR #737`; next due at #740).
  Reconciled #737 into the ledger.

## Verification

- `check_docs --strict` ✓ · `check_session_log --strict` ✓ · `check_current_state_ledger --strict` ✓ ·
  `check_reconciliation_due` = not due (#737/#740) ✓ · 9 cadence tests pass. Docs/config only.

## ⟲ Previous-session review (Q-0102 — reviewing the #737 Context7 batch)

- **What it did well:** verified the npm version before pinning, wired Context7 cleanly (keyless,
  documented key setup), recorded the decision and provenance.
- **What it could have done better:** zoom out — this *whole conversation* shipped ~8 PRs, most of
  them small workflow tweaks landed one-at-a-time. That is precisely the over-segmentation Q-0107's
  "modular but not too segmented" guards against; a single up-front planning pass would have batched
  several (e.g. all the session-ender rules in one PR). The cadence rule is the system learning from
  its own session.
- **System improvement surfaced:** surface the cadence guard at **session start**, not just close —
  so a session knows *before* doing feature work whether it should be the planning pass. → 💡 below.

## 💡 Session idea

**Idea:** Surface `check_reconciliation_due` in the **SessionStart banner** (not only
`/session-close`), so a session learns at boot that it's the designated 10th-PR planning pass and
*becomes* one, instead of discovering it at close after already doing feature work.
**Why:** the cadence rule only helps if a session knows early. The boot hook already prints repo
state; one extra advisory line ("⚠ reconciliation/planning pass due — make this a docs-only Q-0107
pass") routes the session correctly from turn one. Cheap (the check is fast, advisory), and it
closes the loop between the guard and the behavior it's meant to trigger. _Small — recorded here._
