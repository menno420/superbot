# Session: Routine workflow canon — foolproof prompts + idea→plan promotion

> **Status:** `in-progress` — born-red (Q-0133). Flip to `complete` as the last step.

**Branch:** `claude/routine-workflow-canon-2026-06-15` · **Date:** 2026-06-15 · **Type:** workflow/docs (S3 mechanism) · **Trigger:** owner-directed in-session (live conversation)

## What I'm about to do (intentions — born-red)

Owner-directed overhaul of the autonomous-routine prompts so they run **completely without
guidance** and are **foolproof against bad dispatch input** (the "write a story about chickens"
test). Provenance: a long live session with the owner + an independent review from a
Hermes-dispatched routine. Recorded as router **Q-0144**.

1. **Unify + harden the routine prompts** (`hermes-dispatch-bridge.md` dispatch prompt +
   `autonomous-routines.md` night-executor prompt) onto the owner's canonical 12-step session
   lifecycle, weaving in the two-reviewer fixes:
   - **sync-first** (stale clone was a named Hermes failure),
   - **orient-gate** (don't act until oriented),
   - **work-order-is-a-hint / never-stop** (a dispatched order = owner asking = build it; the
     phase gate doesn't apply to dispatched work — it only blocks self-invented features; a
     garbage order redirects to the plan, never derails),
   - **born-red mock PR** (Q-0133) as the async review surface,
   - **judgment over the plan** (a plan is a suggestion of the desired output),
   - **bugs-first / root-cause**,
   - **2–3 slices per session, bounded by ~700K tokens** (not 1M),
   - the standing enders (Q-0089 idea · Q-0102 prev-run review · Q-0104 doc audit),
   - **scope-brake vs safety-brake** (irreversible stays ask-first).
2. **Reconciliation routine — add idea→plan promotion** (owner directive): when plans are running
   low on executable work, review `docs/ideas/` and promote the best one into a **complete,
   executable plan**. De-stale its instructions.
3. **Update `ai-project-workflow.md` §10** bounded-session protocol: "~2 substantial tasks" →
   "2–3 slices, budget-bounded at ~700K."
4. Record router **Q-0144**; reconcile current-state.

Docs-only; self-merge on green (`check_docs --strict`). The in-repo prompt mirrors are canonical;
the owner re-pastes the final text into the routine console.
