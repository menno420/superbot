# 2026-06-22 — Surface BTD6 round XP (NL reply + round-embed Economy field)

> **Status:** `complete`

Owner-directed follow-up to the XP-per-round data PR (#1318): the maintainer asked
to let the bot answer "how much XP does round N give?" and to show XP next to
RBE/cash in the round embed. Discovered the round embed didn't actually show
RBE/cash either — `RoundFact` dropped them — so this threads all three economy
stats through. Stacked on the #1318 branch for the `round_xp` helpers (PR #1324).

## Shipped

- **`disbot/services/btd6_context_service.py`** — `deterministic_round_xp_reply`,
  a pre-emptive BUG-0009 floor builder (same seam as the monkey-knowledge roster)
  grounded entirely on `round_xp_earned()`. Fires on an XP cue (`xp`/`experience`)
  + a resolvable round number; honours an optional map difficulty
  (Beginner/Intermediate/Advanced/Expert → ×1.0/1.1/1.2/1.3) and `freeplay` cue
  (×0.30 ≤R100, ×0.10 R101+); defers without an XP cue / without a round / for an
  out-of-range round. Registered in `_BTD6_LIST_BUILDERS`.
- **`disbot/services/btd6_knowledge_service.py`** — `RoundFact` now carries
  `rbe` / `cash` / `cumulative_cash` / `base_xp`; `round_fact()` populates them
  (XP via `round_base_xp`).
- **`disbot/services/btd6_response_builder.py`** — `for_round` renders an
  **Economy** embed field (`RBE … · Cash $… (cumulative $…) · XP …`). The round
  embed previously surfaced none of these.
- **Tests** — `test_btd6_round_xp_reply.py` (reply difficulty/freeplay/defer
  paths, dispatcher routing, the embed Economy field) + a `_SHOULD_FIRE` /
  `_SHOULD_DEFER` corpus entry in the floor-exclusivity invariant.

Verified: targeted btd6 suites green (74 passed); `mypy` clean on all three
services; `check_architecture --mode strict` 0 errors.

## ⚑ Self-initiated

No — owner-directed (the maintainer said "Yes you can build that next" to the
explicit follow-up offer). PR #1324 opened born-red → flipped ready; auto-merge
armed (Q-0191 owner-directed → merge on green). Stacked on #1318; the diff
narrows to just this PR's changes once #1318 merges.

## 💡 Session idea (Q-0089)

**A round "economy card" that unifies RBE / cash / XP across the embed, the NL
floor, and a `!btd6 round N` summary.** This PR surfaced the three round-economy
stats in the embed and answers XP in NL; cash is answered by a *separate*
workflow (`ai_round_cash_workflow`) and RBE has no dedicated NL reply. A single
`deterministic_round_economy_reply` ("what's the economy of round 95?") grounded
on the same `RoundEntry` + `round_xp` data would give one coherent answer instead
of three partial paths — and the embed Economy field is already exactly that
shape. Genuine: the data + helpers all exist now; it's a consolidation, not new
modelling.

## ⟲ Previous-session review (Q-0102)

The immediately-preceding work (#1318, the XP *data*) deliberately shipped
"data foundation only" and named this surfacing as the follow-up — and that split
paid off: the data landed with its own clean validation story, and this PR is a
thin, low-risk consumer. Good use of the 2–3-PR envelope. The one thing #1318's
investigation *surfaced but didn't act on*: the round embed silently dropped
RBE/cash (a pre-existing gap, not introduced by #1318). This session fixed it as
part of "achieve the goal" rather than filing it — the right call, since the user
explicitly expected RBE/cash to be visible. System note: when an investigation
turns up an adjacent gap ("the embed should show X but doesn't"), folding the fix
into the related PR beats a separate ticket when it's contained and on-goal.

## 🔎 Doc audit (Q-0104)

- targeted suites + `mypy` + `check_architecture` green; full `check_quality
  --full` run before flipping this card ready.
- No owner-decision/router change (a feature build on owner direction, not a
  policy change).
- No `current-state` ledger touch — recorded by the auto-triggered Q-0107
  reconciliation pass. Unmerged PRs #1318 / #1324 correctly absent.
- The reply + embed are self-documenting (builder docstring, `RoundFact` field
  comment); the round-economy consolidation is filed as the Q-0089 idea above,
  not a gap this PR leaves open.

## Context delta

- **Needed but not pointed to:** that round *cash* Q&A goes through a heavy
  orchestration workflow (`ai_round_cash_workflow`, gated by presets) while other
  grounded round/roster answers go through the lightweight pre-emptive
  `_BTD6_LIST_BUILDERS` floor. The floor was the right home for round XP (simpler,
  same pattern as the MK fix), but the two-paths-for-round-economy split isn't
  documented anywhere — a one-line note in the btd6 subsystem doc would help.
- **Pointed to but didn't need:** the orchestration/preset machinery — the floor
  dispatcher made the NL reply a self-contained ~40-line builder with no stage
  wiring.
