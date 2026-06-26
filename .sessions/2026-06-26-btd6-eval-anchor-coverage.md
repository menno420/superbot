# Session — 2026-06-26 · BTD6 eval-anchor coverage + distractor negative-anchor guard

> **Status:** `in-progress` — born-red card (Q-0133). Run type: routine · dispatch.

## What this run is doing

Empty-fire dispatch → advancing the **S2 BTD6 ▶ "Anchor-tooling follow-ons (offline, self-mergeable)"**
lane that the #1458/#1460 anchor runs explicitly teed up. Two additive slices on
`tests/evals/test_btd6_grounding_anchors.py`:

1. **Eval-anchor coverage guard** — inventory every *significant* (≥ $1,000) numeric token in the BTD6
   eval cases' rubrics + fixtures and assert each is either anchored (an `Anchor`/`FixtureAnchor`) or on
   a documented allowlist of distractors + user-inputs. A future rubric/fixture edit that introduces a
   new dollar/HP **truth** without anchoring it then fails CI. The ≥ $1,000 threshold drops structural
   noise (round numbers, tiers, crosspath digits, the "6" in BTD6) so the report isn't noisy.
2. **Distractor negative-anchor guard** — pin that each documented distractor ($71,315.20, $107,164.60)
   stays *distinct from the truth(s)* the case asserts, so a data re-seed can't silently collapse a
   case's discrimination (the wrong answer coinciding with the right one). Where the distractor IS a
   derivable wrong computation (standard-set range given as the ABR answer), pin that too.

Offline, no DB, no AI hot-path, no runtime/`disbot/` change — pure test-layer correctness tooling.
