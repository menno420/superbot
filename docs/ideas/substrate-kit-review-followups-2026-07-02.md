# Idea — substrate-kit hardening follow-ups (from the #1649 independent review)

> **Status:** `ideas` — capture only, not approval, not a plan. Source + binding contracts win.
> **Subsystem:** none (cross-cutting — the portable substrate-kit / agent-workflow substrate).
> **▶ PROMOTED (2026-07-03, Stage-1 review PR #1679):** follow-up #1 (re-entrant transaction →
> atomic `apply_review_verdict`) is now **item ① of the substrate-kit pre-bootstrap gate** —
> owner-directed "fully complete the kit before the new repo bootstraps" (Q-0223; tail + gate in
> [`../planning/rebuild-stage1-global-review-2026-07-03.md`](../planning/rebuild-stage1-global-review-2026-07-03.md)
> §4 D-4). Any session may pick it up now as its own PR; #2 stays verified-low-risk/no-action.

## Provenance

Surfaced by the **independent review of session #1649** (the ultracode memory-substrate finalize),
a 4-reviewer adversarial pass over the shipped kit. That review confirmed **12 defects the session's
own adversarial round missed**; **10 were fixed at root that session** (render `$$`-corruption,
contextpack slug collision, NotebookEdit matcher, two `check_seam_authority` bugs, `check_namespace`
singledispatch false-positive, ledger stamp-bleed, kpis crash-on-malformed-state, the anti-gaming
floor + Q-001 `min_len`, and the never-cleared review payload). These two are the deliberate
carve-outs — captured here rather than folded into that fix batch because each needs its own design +
tests.

## The follow-ups

1. **Re-entrant `JsonStateBackend.transaction` → atomic `apply_review_verdict` (the real one).**
   `review_seam.apply_review_verdict` mutates state across **3 un-batched flushes** on the `fail`
   path (`escalate_blocking` → `downgrade_promotion` → `_rev_log`) and 2 on the pass path
   (`confirm_slot` → `_rev_log`). A crash between flushes can leave inconsistent state — e.g. a
   blocking question escalated (holding graduation) but promotion **not** downgraded and no audit
   row. The analogous multi-write in `interview._set_without_open_question` is already guarded with
   `backend.transaction()`, so this is a known failure mode left unguarded on the review path.
   The clean fix is **not** to wrap `apply_review_verdict` naively — `confirm_slot` already opens its
   own transaction and the backend's `transaction()` is **not re-entrant** (`_in_txn` is a bool; a
   nested `with` would reset it and flush mid-operation). So: make `transaction()` re-entrant
   (participate-don't-nest — only the outermost snapshots/commits), *then* wrap the whole verdict
   application in one transaction. Because it changes core backend semantics for **every** caller,
   it wants its own PR + the full suite green, not a review-batch side-quest.

2. **`confirm_slot` re-validate the floor — verified LOW-RISK, likely no action.** A hollow
   provisional value promoted to `filled` without re-checking `answer_is_substantive` would count
   toward graduation. Traced to effectively **unreachable**: `record_answer` makes a hollow *user*
   answer `"partial"` (never provisional), and the only provisional path uses the substantive
   `"ASSUMED: <slot>"` self-answer — so a hollow provisional value never arises. The #1649 review's
   anti-gaming floor fix hardens this further at the root. Recorded for completeness; add the
   defense-in-depth re-check only if a future path can set a hollow provisional value directly.

## Also noted (cosmetic, no fix)

`triggers.py` populates `Trigger.question_ids` for `blocking_open` triggers but `mandatory_questions`
pulls named ids only from `critical_unfilled` triggers — a set-then-ignore asymmetry. Practical
impact is nil (the interview's `pending_questions` re-surfaces the unfilled slot anyway) and it
matches the docstring, so likely intentional; flagged only so a later reader isn't surprised.
