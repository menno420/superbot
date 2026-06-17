# 2026-06-17 — Skills conversion batch 1: reconciliation bullet → pointer

> **Status:** `in-progress`
> Manual, owner-directed (he greenlit batch 1). **Born-red per Q-0133 — edits `.claude/CLAUDE.md`
> (the owner's core instruction file), so HELD for his review before merge.** Flip to `complete`
> on his go.

**Branch:** `claude/skills-batch1-reconciliation`

## Goal

Batch 1 of the [procedures→skills conversion plan](../docs/planning/procedures-to-skills-conversion-plan-2026-06-17.md):
slim the always-loaded Q-0107 reconciliation bullet in CLAUDE.md to a **thin pointer**, since the full
step-by-step procedure already lives in the docs-reconciliation routine prompt.

## What was done

- Slimmed the CLAUDE.md "Reconciliation + planning pass" bullet (~31 → ~21 lines). **Kept** the binding
  rules verbatim — cadence (every 30th PR, Q-0107/Q-0134), the **manual-session carve-out** (a manual
  session doesn't run the pass unless asked, Q-0124; the `Recon: DUE` banner is for the routine), the
  auto-trigger wiring, and every Q-number. **Moved** the detailed `(1) reconcile` / `(2) plan-the-band`
  steps to a pointer.
- **Verified the destination owns the detail** (`docs/operations/autonomous-routines.md`): `STEP 2 —
  RECONCILE`, `DISPOSITION OPEN PRs (Q-0125)`, `PLAN THE NEXT FULL BAND (Q-0144 + Q-0164)`, and the
  marker reset are all present in the routine's saved prompt. Nothing lost.

## Decisions recorded

- First executed slice of the procedures→skills plan (extends Q-0170). Held born-red for owner review
  because it edits CLAUDE.md (the per-batch convention the plan states).

## Left open / next session

- On owner approval → merge. Then batch 2 (session enders → `/session-close`) + batch 3 (new add-only
  skills), per the conversion plan.

## 💡 Session idea

**Idea:** build the `check_pointer_integrity` lint (from the conversion plan) **before** batch 2 —
assert every CLAUDE.md "procedure … lives in `<target>`" pointer resolves to a target that still
contains the procedure.
**Why:** batch 2+ adds more pointers; a cheap stdlib guard means a later edit can't silently orphan a
runbook, making the whole conversion safe to repeat.

## ⟲ Previous-session review

The previous session (#1028, the conversion plan) did the right thing writing the **must-NOT-move
safety list before any surgery** — this batch leaned on it directly (the manual-session Q-0124 rule was
correctly *kept*, not moved). Improvement it surfaces, applied here: each conversion PR should carry a
one-line **"kept vs moved"** summary so the owner can audit the split at a glance (now in the run report).

## 📤 Run report

- **Did:** slimmed the CLAUDE.md reconciliation bullet to a thin pointer (batch 1 of the skills plan) · **Outcome:** shipped (held born-red for owner review)
- **Run type:** manual (owner-live)
- **Kept in CLAUDE.md:** cadence 30 · manual-session carve-out (Q-0124) · auto-trigger wiring · all Q-numbers · the pointer. **Moved to the routine doc:** the `(1) reconcile` + `(2) plan-the-band` step detail (verified already present there).
- **⚑ Owner decisions needed:** glance at the before/after and say merge (edits your core file, so it's held)
- **⚑ Owner manual steps:** none
- **↪ Next:** batch 2 (enders → `/session-close`) on your go
