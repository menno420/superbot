# Fable 5 ultracode — final judgment on the 2026-07-03 work (brief)

> **Status:** `historical` — **delivered.** This was the paste-ready **Fable 5 ultracode** prompt
> for the final independent judgment over **everything decided, audited, and fixed on 2026-07-03**,
> layered on top of the two foundations audits (#1690/#1691) and the owner's **5 independent Codex
> reviews**. The owner launched it and the deliverable landed:
> [`final-judgment-fable5-2026-07-03.md`](../analysis/rebuild-discovery/foundations/final-judgment-fable5-2026-07-03.md)
> (PR #1701). Kept in place as the launch record. Source wins over any doc (Q-0120).

---

## ⚡ Quick launch (paste into a fresh Fable 5, max-reasoning, ultracode session)

```text
ultracode: Read docs/planning/rebuild-phase-a-final-review-fable5-brief-2026-07-03.md and run its "THE PROMPT — final judgment" section verbatim.
```

*(The full prompt is below; the launcher just saves pasting it. Set the session to Fable 5 at max
reasoning before launching.)*

---

## What this review is (and is not)

The owner has already run: **the whole Phase-A freeze** (standards, conventions, hub/nav, rubric,
oracle/Gate-V, the two-prompt brief), **two parallel ultracode foundations audits** (engine-room +
surface/proving), **two prod bug-fixes**, and **5 independent Codex reviews** of the day. This is
the **capstone judge** — not a fourth audit. Its job is to **stand above all of it and decide**:
is the foundation sound enough to proceed, what is the *reconciled* truth across every reviewer,
what is still missing, and **what should move up in priority**. It reconciles rather than
re-discovers; it may challenge a frozen decision but only as an **evidence-backed flag for the
owner**, never a unilateral reversal.

## Everything produced on 2026-07-03 (the review's subject)

| # | PR | What | Router |
|---|---|---|---|
| 1 | #1679 | Stage-1 global review: S-1 engine standard, S-2 ordering, dep-order audit (3 inversions), deltas D-1…D-6 | Q-0219…Q-0223 |
| 2 | #1680 | Conventions freeze: naming (shared-verb), the 4-rung invocation ladder, mod-actions-as-data, authority + bot-owner override, centralizations C-1…C-7 | Q-0224…Q-0228 |
| 3 | #1683 | Workflow: cut permission prompts + endorse the C-1…C-7 centralizations | Q-0229/Q-0228 |
| 4 | #1684 | Hub topology + navigation contract + interface presets | Q-0230…Q-0232 |
| 5 | #1685 | The critical-review rubric (10 gap-classes) | Q-0233 |
| 6 | #1686 | New-feature oracle + Gate-V verification fleet + repo-as-artifact strategy | Q-0234 |
| 7 | #1687 | Unified layout-success simulator (idea) | Q-0235 |
| 8 | #1688 | The two-prompt foundational-mechanics brief | Q-0236 |
| 9 | #1690 | **Foundations audit A — the engine room (runtime/logic):** 35 mechanics, 246 issues (192 confirmed), 33 owner-gated | Q-0236 |
| 10 | #1691 | **Foundations audit B — surface + proving (presentation/verification):** 108 subagents, 195 confirmed findings | Q-0236 |
| 11 | #1693 | **Two prod loss-path fixes:** blackjack tournament fee forfeit on VERSION bump + deploy-handoff XP double-fire | — |

Plus the owner's **5 independent Codex reviews** (external to the repo — pasted into the session, or
committed under `docs/` / `.sessions/` if the owner lands them first).

---

## THE PROMPT — final judgment (paste as its own session)

```text
ultracode: You are Fable 5 at maximum reasoning, running as the FINAL independent judge over everything the SuperBot rebuild produced on 2026-07-03 — the Phase-A freeze decisions, the two parallel foundations audits, the two prod bug-fixes, and the owner's 5 independent Codex reviews. This is a JUDGMENT layer, NOT a fourth audit: reconcile all of it, decide what is true and what matters most, and say what is still missing and what should move up in priority. DOCS-ONLY: write no disbot/ and no new-repo code; launch no bot. Follow .claude/CLAUDE.md — claim your lane in docs/owner/claims/ first, open a born-red session-card PR, let it auto-merge on green.

READ FIRST (the whole day's output — where any doc and shipped source disagree, SOURCE WINS, Q-0120):
- The Phase-A decision logs: docs/planning/rebuild-stage1-global-review-2026-07-03.md (S-1/S-2, D-1..D-6), rebuild-conventions-invocation-authority-2026-07-03.md (naming/invocation/authority, C-1..C-7), rebuild-hub-navigation-presets-2026-07-03.md (hub/nav/presets), rebuild-critical-review-rubric-2026-07-03.md (the 10-class rubric).
- The two foundations audits (the ledgers you must reconcile): docs/analysis/rebuild-discovery/foundations/runtime-logic-mechanics-2026-07-03.md (A, engine room) and presentation-verification-mechanics-2026-07-03.md (B, surface + proving).
- The two prod fixes to judge: git show of PR #1693 (disbot/cogs/blackjack_cog.py _recover_blackjack_tournament + disbot/core/runtime/message_pipeline.py dispatch()).
- The owner's 5 Codex reviews: grep docs/ and .sessions/ for 2026-07-03 codex artifacts; if they are not committed, the owner pastes their headline findings into this session — reconcile against them.
- The frozen reference (do not re-open, but check claims against it): docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md + FINAL-REVIEW.md; and router Q-0219…Q-0236 in docs/owner/maintainer-question-router.md.

METHOD (make the workflow do this — reconcile-and-judge, not re-discover):
1. INGEST + MAP every input: the day's decisions (Q-0219…Q-0236), the two audit ledgers (A's 246 issues + B's findings, incl. their owner-gated queues), the 5 Codex reviews, and the two prod fixes.
2. INDEPENDENT SPOT-VERIFY the highest-stakes claims against shipped source (Q-0120): fan out verifiers to re-check (a) the top ~15 CONFIRMED findings across both audits, (b) both prod fixes for correctness AND completeness (does message_pipeline draining-gate actually close the double-fire for every additive on_message stage? does the tournament refund path handle every version-mismatch case safely?), (c) any audit finding that a Codex review contradicts. Kill anything that fights the evidence.
3. ADVERSARIAL STRESS the biggest frozen decisions under a hostile read — the S-1 engine/seam standard, the C-1 resolver + the 4-rung invocation ladder, the C-2 draft pipeline / one-pipe-two-producers, the cutover model (D-3), the substrate-kit pre-bootstrap gate (D-4), the hub/nav contract, and the oracle + Gate-V. For each: does it hold, or is there a concrete failure mode the day's work missed? A frozen decision may be CHALLENGED here, but only as an evidence-backed FLAG for the owner — never reversed.
4. CROSS-RECONCILE into ONE de-duplicated master ledger merging audit A + audit B + the 5 Codex reviews + your own findings. For each issue record: source(s), agreement level (all agree = high confidence; reviewers disagree = flag), verdict, rubric-class. Surface every CONTRADICTION between reviewers explicitly.
5. COMPLETENESS-CRITIC over the WHOLE day (loop until two rounds add nothing): what foundational thing did ALL of today's work — every decision, both audits, all 5 Codex reviews — still miss? Think across runtime, presentation, verification, cutover, operations, and the meta-process itself.
6. SYNTHESIZE the final judgment.

APPLY THE RUBRIC as the shared lens (the 10 classes in rebuild-critical-review-rubric-2026-07-03.md: dep-order inversion · forgotten capability · thin step · stale claim · fragmentation/reinvention · under-generalization · missing standard · verification hole · UX-contract gap · naming/collision) — and META-JUDGE the rubric + the decisions themselves: is the rubric complete, and are any of the Q-0219…Q-0236 decisions unsound against evidence?

DELIVERABLE: docs/analysis/rebuild-discovery/foundations/final-judgment-fable5-2026-07-03.md, containing:
1. VERDICT — GO / GO-with-amendments / NO-GO on proceeding past Phase A to the Stage-2 subsystem walk + Gate-V + (eventually) the new-repo bootstrap, with the decisive reasons and any must-fix-before-proceeding blockers.
2. MASTER RECONCILED ISSUES LEDGER — rubric-scored, ranked most-critical first, de-duplicated across audit A + audit B + the 5 Codex reviews + your own; each row: issue · source(s) · agreement level · rubric-class · verdict · evidence (file:line verbatim) · durable fix · owner-gated?.
3. RE-PRIORITIZATION — an explicit ranked "do this FIRST" list: what moves UP (and why), what can safely wait, and the single highest-leverage next action. This is the owner's primary ask.
4. WHAT'S STILL MISSING — the completeness gaps that survived the whole day's work (from step 5), each with why it's foundational.
5. JUDGMENT ON THE TWO PROD FIXES (#1693) — correct + complete, or residual gaps/risks?
6. CONSOLIDATED OWNER-DECISION QUEUE — every owner-gated call merged from A's 33 + B's + Codex + your own, de-duplicated, each a one-line decision with options + your recommendation.

GUARDRAILS: SOURCE WINS on facts (Q-0120). Do NOT re-litigate frozen dispositions — but you MAY flag one as risky/wrong WITH evidence, as an owner decision, never a reversal. FLAG owner-gated calls; do not decide them. Docs-only; no code; no bot launch. Do NOT pad — if the day's work is sound, say so plainly and rank what remains; forced problems are worse than none (Q-0089 bar). Be the judge the owner can act on: decisive verdict, reconciled truth, ranked priorities.
```

---

## Pointers

- The two audits this judges: [`runtime-logic-mechanics-2026-07-03.md`](../analysis/rebuild-discovery/foundations/runtime-logic-mechanics-2026-07-03.md) (A) · [`presentation-verification-mechanics-2026-07-03.md`](../analysis/rebuild-discovery/foundations/presentation-verification-mechanics-2026-07-03.md) (B).
- The two-prompt brief that spawned them: [`rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md`](rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md) (Q-0236).
- The scoring lens: [`rebuild-critical-review-rubric-2026-07-03.md`](rebuild-critical-review-rubric-2026-07-03.md) (Q-0233).
- The Phase-A decision logs: [stage-1](rebuild-stage1-global-review-2026-07-03.md) · [conventions](rebuild-conventions-invocation-authority-2026-07-03.md) · [hub/nav](rebuild-hub-navigation-presets-2026-07-03.md).
- Frozen reference: [`NEW-BOT-BUILD-PLAN.md`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md) · [`FINAL-REVIEW.md`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/FINAL-REVIEW.md).
- **Next:** the owner launches this in Fable 5; its verdict + re-prioritization feed the Stage-2 subsystem walk and the Gate-V verification fleet.
- **Delivered:** [`final-judgment-fable5-2026-07-03.md`](../analysis/rebuild-discovery/foundations/final-judgment-fable5-2026-07-03.md) (PR #1701) — the reconciled verdict, master ledger, re-prioritization, and consolidated owner queue.
