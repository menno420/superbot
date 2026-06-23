# 2026-06-23 — Record Q-0199 (AI-setup apply decision) in the router

> **Status:** `complete` — docs-only. Records the owner's in-session Q-0048 per-exposure **write**
> decision (AI may apply generated setup changes, but only after confirmation, via per-suggestion
> Accept/Deny/Edit) as an append-only **Q-0199** block in the question router — the durable home for owner
> decisions, which the session card for PR #1386 flagged as still owed. PR this session; auto-merge armed
> on green (Q-0127); owner-directed → merge immediately (Q-0191).

> **Run type:** `manual · owner-directed (docs hygiene)`

## Why

PR #1386 implemented the owner's decision (AI-setup Accept/Deny/Edit) but the **decision itself** — a real
per-exposure write lift under Q-0048, granting AI the ability to mutate a guild (after confirmation) — only
lived in the session card. Owner decisions about irreversible capabilities belong in the question router
(CLAUDE.md: "route durable conclusions to their correct documentation home"). This closes that gap.

## Change

One append-only Q-block (`Q-0199`) in `docs/owner/maintainer-question-router.md`: context, the decision
(AI applies only through the human-gated Accept/Deny/Edit + audited Final Review path; does not generalize
to other AI write surfaces), what shipped (#1386), and the noted follow-on (bind-target re-pick).

## Close-out

**Verification:** `check_docs --strict` + ledger pass (docs-only; no code/tests touched).

**💡 Session idea (Q-0089):** *A `check_docs` lint that flags an implemented owner decision whose Q-block
is missing from the router.* This session existed because a decision (Q-0048 setup-apply) shipped in code
(#1386) a session before its router entry. A heuristic guard — e.g. a session card that records a
`Q-00NN` decision in its body should have a matching router block within N PRs — would catch
decision→router drift the way the ledger checker catches PR→ledger drift. (Captured; small follow-on.)

**⟲ Previous-session review (Q-0102):** the previous (AI-setup Edit) session correctly *flagged* this
router gap in its own close-out ("should also be appended to the question router … flagged for the
docs-reconciliation pass") — good drift-awareness — but deferred it to a future pass rather than closing
it. **System improvement (applied):** a decision-recording follow-up that's one paragraph of docs is
cheaper to do immediately than to track; when a session surfaces a *small* durable-home gap, close it the
next session rather than queueing it for reconciliation. Did that here.

**Claim** `docs/owner/claims/claude__q0199-ai-setup-apply.md` deleted at close (Q-0126).
