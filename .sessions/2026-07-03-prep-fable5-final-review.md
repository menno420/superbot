# 2026-07-03 — Prepare (not execute) a Fable-5 ultracode final-judgment prompt

> **Status:** `complete`
> **Branch:** `claude/prep-fable5-final-review-2026-07-03` · **PR:** #1700
> **Session type:** docs-only prompt-prep (owner-directed). Owner asked me to PREPARE, not
> execute, a Fable 5 ultracode work/plan-review prompt for a final judgment over everything done
> + found today, plus what's missing / should move up in priority.

## What happened

Wrote `docs/planning/rebuild-phase-a-final-review-fable5-brief-2026-07-03.md` — a launchable brief
(mirrors the #1688 two-prompt pattern) holding one paste-ready **Fable 5 ultracode** capstone-review
prompt. The prompt is a JUDGE, not a fourth audit: reconciles the whole 2026-07-03 body of work
(the Phase-A freeze Q-0219…Q-0236; both foundations audits #1690 engine-room + #1691 surface/proving;
the two prod fixes #1693; the owner's 5 independent Codex reviews) into one master ledger,
spot-verifies the top claims + the fixes against source (Q-0120), adversarially stresses the biggest
frozen decisions (flag-not-reverse), completeness-critics the whole day, and delivers a VERDICT +
RE-PRIORITIZATION + what's-still-missing + a consolidated owner-decision queue. Linked from the #1688
brief for reachability; check_docs --strict green. Did NOT execute the review (owner runs it).

## Decisions made alone

- **Committed the prompt as a launchable planning doc** (vs. only pasting it in chat), following the
  #1688 precedent + the standing "PR every session" rule. Reversible docs-only; the prompt is also
  reproduced in the chat reply for immediate copy-paste.
- **Empowered the Fable-5 judge to challenge a frozen decision *with evidence, as an owner flag*** —
  a deliberate step beyond the audits' pure pressure-test, because a final judge that can't say "this
  frozen call is wrong" isn't a judge. Bounded to flag-not-reverse (Q-0120 spirit).

## Flagged for maintainer

- The prompt assumes the **5 Codex reviews** are available to the Fable-5 session — they're external
  (not committed). The prompt says: grep the repo for them, else the owner pastes their headlines. If
  you want them reconciled properly, drop them into `docs/` or the session before launching.
- Set the session to **Fable 5 at max reasoning** before launching (the launcher can't set the model).

## Session idea (Q-0089)

**A standing "capstone judge" rung in the review ladder.** Today's chain was: build -> 2 audits ->
5 Codex reviews -> (this) Fable-5 judge. That final reconcile-and-rank layer — one judge that merges
every independent reviewer into a master ledger + a re-prioritization + a GO/NO-GO — is reusable
beyond this rebuild. Worth capturing as a named review stage (like Gate-V) so any large multi-review
effort ends with a single decisive reconciliation instead of N parallel ledgers the owner must merge
by hand. (Recorded here; file + index in a non-parallel session.)

## Previous-session review (Q-0102)

The two-prompt brief (#1688) and the two audits it spawned worked exactly as designed — disjoint
scope, no collision, both landed. The one gap the day exposed: **N independent reviewers (2 audits +
5 Codex) produce N ledgers with no built-in reconciliation step** — the owner had to ask for this
capstone explicitly. Improvement: bake the reconcile-and-judge stage into the review pattern up front
(the session idea above), so multi-review efforts converge by default.

## Friction -> guard (Q-0194)

Friction: the new `plan` doc was an orphan (check_docs reachability fail) until linked — the same
class I hit last session. The enforcing guard (check_docs --strict) already exists and caught it
locally; the residual gap is discoverability. Durable capture stays the ready-to-promote journal
Quick-reference line from the prior session ("new non-historical doc -> link it from a read-path
doc"); deferred to a non-parallel window to avoid a shared-journal collision. No new guard needed.

## Grooming (Q-0015) · Self-initiated

- **Grooming:** advanced the review pipeline one stage — the day's audits + Codex reviews now have a
  launchable reconciliation capstone instead of dangling as parallel ledgers.
- **Self-initiated:** none — executed the owner's explicit "prepare a Fable-5 review prompt" ask.
