# 2026-07-02 — Refresh the Fable 5 capstone prompt for the completed fleet

> **Status:** `complete`
> **Branch:** `claude/review-recent-session-qcyc44` · **PR:** #1673
> **Session type:** owner-directed — "create a revised prompt for Fable if necessary, or a quick start prompt
> pointing Fable to the right file." The capstone prompts predate the fleet completing → revision necessary.

## What I'm about to do (born-red placeholder)

Freshen the two capstone-prompt docs (`FINAL-REVIEW-HANDOFF.md` + the capstone block in `HANDOFF-PROMPTS.md`)
for the now-complete 7-lane fleet: fix "four lanes"→"seven", note the amendment set is now **G-1…G-10**
(Lanes D/F added G-7…G-10), and add the **Lane F source-correction guard** (don't propose ADD-from-ecosystem
for capabilities that already ship). Then hand the owner a quick start prompt. Docs-only.

## What shipped

- `FINAL-REVIEW-HANDOFF.md` + capstone block in `HANDOFF-PROMPTS.md`: "four lanes"→"seven (all merged)",
  amendment set G-1…G-6 → **G-1…G-10** (D/F added G-7…G-10), and the **Lane F source-correction guard**
  (re-check ground truth before any ADD-from-ecosystem; competitor catalog is directional).
- Quick start prompt handed to the owner in chat.

## ⚑ Self-initiated

None beyond the owner request. The revision was gated on "if necessary" — it was (stale lane count + missing
G-7…G-10 would have had the capstone consolidate the wrong amendment set).

## 💡 Session idea

**Stamp handoff prompts with a `depends-on: <state>` freshness line.** These capstone prompts went stale the
moment the fleet's shape changed (4→7 lanes, G-6→G-10) because nothing tied them to the state they assume. A
one-line machine-checkable header (e.g. `> depends-on: lanes A–G merged · amendments G-1..G-10`) plus a tiny
checker that flags a handoff prompt whose asserted state contradicts the live substrate would catch prompt-drift
the same way `check_current_state_ledger` catches ledger-drift. Dedup: no existing checker validates prompt docs
against the state they claim.

## ⟲ Previous-session review

The prior step (my Lane F verify + land) correctly caught the raw research's errors — good Q-0120 discipline.
**What it could have done in the same pass:** update these capstone prompts *then*, since landing Lane F is
exactly what made "four lanes / G-1…G-6" stale. I split it into a second PR instead. **System improvement:**
a lane-landing checklist item — "if this is the last lane, refresh the capstone handoff" — would fold the
prompt-refresh into the completing PR instead of a follow-up (captured as the freshness-header idea above).

## 📊 Telemetry

- PR #1673 · docs-only · 3 files (FINAL-REVIEW-HANDOFF.md, HANDOFF-PROMPTS.md, this log).
- Fixes: 3 staleness classes (lane count, amendment range, Lane F guard) across both capstone-prompt docs.

## Doc audit (Q-0104)

`check_docs --strict` green · no new docs (edits to existing reachable files) · ledger unaffected (docs-only)
· no claim file (PR is the in-flight signal).
