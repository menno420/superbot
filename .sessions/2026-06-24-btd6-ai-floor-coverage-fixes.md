# 2026-06-24 — BTD6 AI floor coverage: range RBE + paragon elite-boss multiplier

> **Status:** `in-progress` — owner-reported bugs (Discord screenshots). Born-red
> card; flips to `complete` last. PR pending.

> **Run type:** `manual · owner-directed`

Owner showed three live failures (all the *same* root cause — deterministic-floor
coverage gaps, so the model is left to freelance and refuses / gets faithfulness-
rejected):
1. **"rbe of r20 to r80"** → returns only Round 20. `deterministic_round_economy_reply`
   matches the "rbe" cue, grabs the first round number (`r20`) via the single-number
   regex, and ignores the range. (Regression: "rounds 8 to 66 in ABR" still works —
   "rounds" doesn't match the single-number regex, so it defers to the round_composition
   tool. Only the `rN`-shorthand range form broke.)
2. **"elite boss multiplier for paragons"** (general) → "no verified data" refusal. The
   #1402 elite grounding lives in `_render_paragon_stats`, which only runs when a
   *specific* paragon resolves — the general question gets no grounding.
3. **"elite boss multiplier for the dart paragon"** (named) → "I drafted an answer but
   held it back" = the faithfulness floor killing a model draft. Grounding alone isn't
   surviving.

## What I'm about to do
- **Fix 1 — range-aware economy floor:** when `deterministic_round_economy_reply` sees
  exactly one round range, return a deterministic range-total reply (total RBE base +
  freeplay-scaled via `round_rbe`, total cash via `round_cash`, heaviest rounds via
  `round_composition`). ≥2 ranges defers to the §7.5 comparison floor. Verified: this
  reproduces the proven 06/18 answer (ABR 8-66 = 168,518 RBE; heaviest R65/R63/R62).
- **Fix 2 — deterministic paragon elite floor:** new `deterministic_paragon_elite_reply`
  in `_BTD6_LIST_BUILDERS`, fires on elite+paragon+(multiplier/damage) cues, returns the
  ×2 rule (×2 at Degree 1 → ×4.5 at Degree 100; global, runtime constant). Bypasses the
  model + faithfulness floor entirely, so it can't refuse — works for both the general
  and the named-paragon question.
- Tests for both + the floor-exclusivity invariant; full CI mirror before flip.
