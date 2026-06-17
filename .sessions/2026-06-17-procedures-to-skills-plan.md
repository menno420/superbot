# 2026-06-17 — Procedures→skills conversion plan

> **Status:** `complete`
> Manual, owner-live continuation of the 2026-06-17 routine-review session. Docs-only.

**PR:** (this PR) — capture the procedures→skills conversion as an executable plan.
**Branch:** `claude/procedures-to-skills-plan`

## What was done

- Captured the chat-only skills inventory (33 procedures, A/B/C buckets) into an **executable plan**:
  `docs/planning/procedures-to-skills-conversion-plan-2026-06-17.md`.
- Recorded the **owner-confirmed approach** (2026-06-17): relocate procedures to on-demand skills,
  keeping a thin pointer + the binding rules in CLAUDE.md ("only get loaded when necessary").
- Defined the **must-NOT-move safety list** (C-bucket) + the **thin-pointer convention** + the
  **enforcement caveat** (mandatory enders stay hook-triggered) + a **batched build order**, with a
  concrete before→after sample (the Q-0107 reconciliation bullet, ~28 → ~6 lines).
- Linked the plan from the agent-tooling shortlist idea (Q-0170).

## Decisions recorded

- Owner approved the procedures→skills **direction** + the **relocate-not-delete / thin-pointer**
  approach (extends Q-0170). **CLAUDE.md-editing batches are held born-red for owner review** (his core
  instructions); add-only skill batches may merge on green.

## Left open / next session

- Execute **batch 1** (slim the Q-0107 reconciliation bullet → pointer) on the owner's go — held born-red
  because it edits CLAUDE.md. Then batch 2 (enders → `/session-close`), batch 3 (new standalone skills).

## 💡 Session idea

**Idea:** a `check_pointer_integrity` lint — when CLAUDE.md keeps a "full procedure: `<doc/skill>`"
thin pointer, assert the target exists and still contains the procedure.
**Why:** the thin-pointer pattern's one failure mode is a dangling pointer after a later edit; a cheap
stdlib guard makes the whole conversion safe to repeat across batches. (recorded here; small/disposable.)

## ⟲ Previous-session review

The previous session (#1026, this same conversation) correctly **held the governance edits born-red for
owner review** instead of auto-merging — the right call for CLAUDE.md-touching work, and it paid off
(the owner engaged and approved the direction). The improvement it surfaces, now captured in this plan:
that "hold CLAUDE.md edits for review" instinct is written into the plan as an explicit per-batch rule,
so it's a stated convention rather than a remembered one.

## 📤 Run report

- **Did:** captured the procedures→skills inventory as an executable plan + linked it · **Outcome:** shipped
- **Run type:** manual (owner-live)
- **⚑ Owner decisions needed:** greenlight to execute batch 1 (reconciliation bullet → pointer); choose all batches vs. a subset
- **⚑ Owner manual steps:** none
- **↪ Next:** execute batch 1 on the owner's go (held born-red — edits CLAUDE.md)
