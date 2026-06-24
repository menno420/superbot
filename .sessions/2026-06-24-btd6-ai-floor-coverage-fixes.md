# 2026-06-24 — BTD6 AI floor coverage: range RBE + paragon elite-boss multiplier

> **Status:** `complete` — owner-reported bugs (Discord screenshots), fixed and
> verified live through the dispatcher. PR #1408; auto-merge armed; merges on green.

> **Run type:** `manual · owner-directed`

> **⚑ Self-initiated:** none — all three fixes are owner-reported production refusals.

Owner showed three live failures (all the *same* root cause — deterministic-floor
coverage gaps, so the model is left to freelance and refuses / gets faithfulness-
rejected). Notably, two of them were gaps left by *this same session-arc's* prior
PRs (#1402 elite, #1404 round commands) — the data/grounding shipped, but the live
answer path still refused.

## Shipped (PR #1408)
Both fixes are deterministic floors in `btd6_context_service.py` — immune to model
refusal / the faithfulness floor:

1. **Range-aware economy floor.** `deterministic_round_economy_reply` now detects a
   single round range and returns deterministic range totals via
   `_round_range_economy_reply` (total RBE base + freeplay-scaled from `round_rbe`,
   total cash from `round_cash`, heaviest rounds from `round_composition`); ≥2 ranges
   defer to the §7.5 comparison floor. **Verified it reproduces the proven 06/18
   answer exactly:** ABR rounds 8-66 = **168,518** RBE, heaviest R65/R63/R62.
   - Was: `rbe of r20 to r80` → only Round 20 (the single-number regex grabbed `r20`).
2. **`deterministic_paragon_elite_reply`** (new floor, registered + corpus-pinned).
   Owns the elite-boss-multiplier question — general *and* named paragon — returning
   the global runtime constant (×2 every degree, ×2→×4.5, paragon-category-wide).
   - Was: general → "no verified data" refusal; named (`dart paragon`) → faithfulness
     floor held the model draft back.

Tests: range totals + the 168,518 anchor (`test_btd6_round_economy_reply.py`); the
elite floor incl. value-pinning to `paragon_degrees` (`test_btd6_paragon_elite_reply.py`);
floor-exclusivity invariant extended. Full CI mirror green.

## 💡 Session idea (Q-0089)
A **`_MUST_ANSWER` regression corpus** — sibling to the exclusivity test's
`_SHOULD_FIRE` / `_SHOULD_DEFER` — seeded with the owner's *actual production-failed*
phrasings ("rbe of r20 to r80", "elite boss multiplier for the dart paragon", …),
asserting `deterministic_btd6_list_reply` returns non-`None`. Every prod refusal the
owner reports becomes a permanent entry, so the *same* refusal can't regress. Cheap,
directly motivated by today's three-in-a-row. Dedup-checked: the exclusivity corpora
test fire/defer routing, not must-not-refuse. (Not built; flagged for grooming.)

## ⟲ Previous-session review (Q-0102)
Reviewed **2026-06-24-btd6-per-round-economy-commands** (#1404, merged hours ago).
Did well: clean, fully-verified feature; caught + fixed its own `round_composition`
duplication at the mirror. **What it (and #1402) missed:** both shipped *data +
grounding* but never ran the **live natural-language questions** through
`deterministic_btd6_list_reply` / the answer pipeline to confirm the bot actually
**answers** — so both left prod refusals the owner had to find. **System improvement
(the real lesson of today):** *grounding present ≠ question answered.* After any BTD6
data/grounding change, run a handful of representative end-user phrasings through the
answer path, not just the unit-level data function. The Q-0089 must-answer corpus
would make that a CI guard instead of a manual habit. This session is the correction.

## Backlog grooming (Q-0015)
`round-range-comparison-bare-range-list-2026-06-16.md` is now **partially delivered**:
the range-economy floor handles a single round range with an economy/rbe cue. The
idea's remaining piece — comma-list phrasing ("rounds 1-30, 30-60") for the *cash
comparison* floor — is still open (it lives in `_extract_round_ranges` bare-range
parsing + the ≥2-range comparison floor). Noted on the idea; not promoted here.

## Doc audit (Q-0104)
`check_docs --strict` ✓, ledger ✓, full mirror green. No new runtime-formula fact
(elite ×2 already in the gamedata-dictionary from #1402); the floors are internal
answer-path coverage. No owner-decision/router change. Ledger entries for #1408 land
via the next reconciliation pass (Q-0052).
