# "Compute, don't refuse" — a capability sweep over the review log

> **Status:** `ideas`. **Not a plan, not approval.** A capture doc so the idea lives in
> the repo instead of in chat. Source code, the binding contracts, and
> `docs/current-state.md` always win over anything here.
>
> **Subsystem:** ai, btd6
>
> **Session idea (2026-06-30, Q-0089)** — surfaced building the BTD6 boss-fight estimator
> (PR #1574), itself prompted by the owner noticing the bot *refuses questions it has the
> data to compute*.

## The idea in one paragraph

The boss-fight estimator fixed one instance of a general failure: **the bot refuses (or
confabulates) questions it has the grounded data to _compute_** — "how do I beat Bloonarius",
"cheapest cost", "how long". The same shape recurs across domains: economy projections
("how much cash by round 40 with 3 farms"), XP-to-level ("how long to hit level 50"), mining
("how many of X to afford Y"), drop-rate expectations. Each is a *deterministic arithmetic*
question the model botches but a small compute seam nails. The idea: **mine the
`ai_review_log` (the answer-loop export) for `grounding_failed` / refusal entries that are
actually _computable_, and build a deterministic compute tool per recurring class** — the
generalization of `deterministic_btd6_list_reply`, the round-cash workflow, and now the
estimator.

## Why it's worth having

- **The review log already tells us what's failing.** The first export (#1572) had four
  refusals; the owner correctly flagged most as computable. A standing "computable refusal"
  triage category turns the log into a **compute-tool backlog**.
- **Deterministic > model for arithmetic.** Every time the model does multi-step math over
  grounded numbers it confabulates (the DDT list, the round-cash mislabels). A compute seam is
  correct, cheap (zero extra tokens), and testable.
- **It compounds.** Each tool (estimator, round-cash, list-floor) makes the bot answer a whole
  *class* of questions, and a regression probe keeps it fixed.

## Seams it would touch

- **`scripts/ai_review_triage.py`** — add a `computable` heuristic / disposition so the triage
  output flags "the bot has the data, it just refused" distinctly from "data gap".
- **A compute-tool pattern** — pure `services/<domain>_estimator_service.py` modules (like the
  BTD6 one) + a deterministic reply / grounding-injection seam in the answer path.
- **The answer path** — the conservative detection that routes a computable question to its
  tool instead of the model (the gated part; each needs live verification, per the AI gate).

## The hard part

- **Detection without over-firing.** A deterministic reply that bypasses the model must only
  fire on a clearly-computable question — the same conservatism the estimator's `parse_request`
  uses. Grounding-injection (augment the model's facts with the computed answer) is the
  lower-risk alternative where detection is fuzzy.
- **Scope discipline.** Not every refusal is computable (a true open-ended optimization, or a
  genuine data gap like BTD6 track length, should still be refused honestly). The triage flag is
  a *candidate* signal, not an auto-build trigger.

## Lifecycle

Routing candidate for `docs/planning/` once 2–3 computable classes are identified from real
exports. The BTD6 boss-fight estimator (#1574) is the first instance + the reusable pattern;
its deferred AI-answer-path integration is the first concrete next slice. Pairs with the
review-log frequency-suggestions idea (which ranks *what* to fix) and the resolve-with-reason
idea (which records outcomes) — all three sharpen the same answer-loop.
