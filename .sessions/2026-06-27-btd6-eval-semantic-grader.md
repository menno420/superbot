# 2026-06-27 — BTD6 live eval: semantic grading (fix false-negatives) + honest limits

> **Status:** `complete`

**Run type:** owner-directed (owner ran the live eval, pasted the scorecard)

## What this run did

The owner ran the new `suite: btd6` live eval against a real Anthropic key. The scorecard read 2/12 —
but **the replies were almost all correct**; my grader was wrong. It graded the *live* (paraphrased)
answer by substring-matching the *grounded-fact wording* (`"lead does not resist glue"`), which the model
restates in its own words. That's the right check for the offline grounding layer (we control the fact
text) but a false-negative machine for the live layer.

**Fix (PR — eval-only, no `disbot/` change):**

1. `GroundingProbe` gains a `rubric` — the correctness criterion for the LIVE answer. `expect`/`forbid`
   still grade the offline layer (substrings of the grounded *facts*); `rubric`/`forbid` grade the live
   layer.
2. `btd6_live_path._grade` is now async and judges each reply **semantically** with the same
   `llm_judge` the golden set uses (refusal or a known wrong claim still hard-fails). So the live
   scorecard now reflects whether the *answer* is right, not whether it echoes the fact's wording.
3. Documented two honest limits surfaced by the run:
   - **DB-backed workflow answers can't run in CI.** `_invoke_gateway` degrades the DB-resolved
     orchestration profile, so round-cash "cash on round N" questions (which need that profile to engage
     the workflow) refuse in a DB-less run. The corpus deliberately covers interaction/immunity/damage
     questions, not round-cash.

## Real findings reported to the owner (not silently changed)

The fixed eval surfaced a **genuine** issue worth its own decision, not a quiet patch:

- **Over-refusal on "how do I deal with a DDT"** (and, in the golden set, round-cash / elite-Lych-HP /
  despo-cost / bomb-MOAB). The faithfulness guard rejects the model's answer when it names towers/numbers
  not in the grounded facts, then serves the deterministic refusal. For "deal with a DDT" the model wants
  to recommend towers the grounding doesn't carry → refusal. Two fix paths, both focused follow-ups: (a)
  enrich the interaction grounding with VERIFIED tower recommendations (derive from the dump's capability
  data — needs a careful verification pass; it's the tower-specifics I deliberately kept out), or (b)
  loosen the guard to allow known BTD6 tower *entity names* (riskier — it's the bot's anti-hallucination
  seam). Reported for an owner decision rather than rushed.
- A couple of **golden rubrics look stale** (e.g. `knowledge.btd6_lead` expects "Sharp Shots lets Dart
  pop Lead" — Sharp Shots is +pierce, not lead-popping). Flagged, not touched (pre-existing golden set).

## ⚑ Self-initiated

None unprompted — owner ran the eval and asked (implicitly) for it to be trustworthy. The grader fix is
the direct response; the over-refusal is reported, not silently changed (it's a guard/grounding decision).

## 💡 Session idea (Q-0089)

*A `--show-replies` flag that dumps every live reply + its grounded facts to a file*, so triaging a live
fail is "read the reply + what it was given," not a re-run. The runner already holds both. Routed as an
idea.

## ⟲ Previous-session review (Q-0102)

The previous run (the faithful live path, #1490) was right to reuse production internals — that's exactly
why this run could trust the *replies* and locate the bug in the *grader*. What it missed: it carried the
`expect`/`forbid` substrings straight from the offline layer into the live grader without re-checking that
a paraphrased answer would match — a grader should be designed against *the thing it grades*. Lesson
applied: offline grades facts (exact), live grades answers (semantic); never share a matcher across the
two. The faithful path also surfaced a real product signal (over-refusal) the offline layer never could —
evidence the live layer earns its cost.

## 🧾 Doc audit (Q-0104)

`check_docs`/`check_consistency` green. Homed: the grading method + the DB-workflow limitation in the
`btd6_live_path` docstring + `tests/evals/README.md`. The over-refusal finding is captured here + reported
to the owner in-chat; if the owner picks a fix path it becomes a router decision + a plan. Ledger: next
reconciliation pass.
