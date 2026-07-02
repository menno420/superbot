# Convergent-discovery as an amendment-confidence signal (multi-agent audit methodology)

> **Status:** `ideas` — not approved for implementation. A workflow/methodology capture, not a
> bot feature.
> **Subsystem:** none

**Session idea (2026-07-02, Q-0089, Lane A governance capability-audit session).**

During the Lane A new-bot capability audit, 11 independently-run subagents (one per subsystem,
no cross-talk) each proposed new §2 grammar amendments where the existing G-1…G-6 didn't fit. Two
proposals were **independently rediscovered by unrelated agents auditing unrelated code**:

- A declarative modal-form primitive (`ModalFieldSpec`) — proposed separately by the `admin`,
  `moderation`, `channel`, and `ticket` audits (4×), each pointing at a different hand-written
  `discord.ui.Modal` subclass.
- A declarative message-pipeline-stage primitive (`MessagePipelineStageSpec`) — proposed
  separately by `automod`, `image_moderation`, and `cleanup` (3×), each pointing at a different
  stage registration in `core/runtime/message_pipeline.py`.

Neither agent knew the others existed. That convergence is a stronger signal than any single
agent's individual argument for the amendment — it's evidence the gap is a *real, load-bearing*
grammar hole recurring across independent code, not one agent's idiosyncratic read of one file.

**The idea:** when a multi-agent audit/review fans out N independent workers over disjoint scopes
and asks each to propose fixes/amendments/refactors, **explicitly count and surface independent
rediscoveries** as a confidence-ranking signal during synthesis — before deduping proposals into
one canonical list, tag each canonical entry with "found independently by K of N workers." This
turns what would otherwise be lost (each agent's proposal looks like an isolated judgment call)
into a cheap, free, non-gameable prioritization signal: an amendment/fix independently found by 3+
unrelated workers should jump the queue over one found by only 1, all else equal.

**Where this could apply next:**
- The other lane audits (B/C/D) and the capstone's cross-lane amendment reconciliation — the same
  "count independent hits" step should run again once all 4 lanes' proposals are merged.
- Any future Ultracode workflow that fans out N reviewers/finders over disjoint scope and asks
  each to propose new primitives, refactors, or bug classes (the `code-review` skill's
  "adversarial verify" pattern already does something similar for *confirming* a single finding
  via N independent refuters — this is the mirror case: using *N independent proposers* who never
  saw each other's work as a *discovery*-confidence signal, not a verification one).

Small, cheap, and free of new tooling — it's a synthesis-step convention, not a new mechanism.
