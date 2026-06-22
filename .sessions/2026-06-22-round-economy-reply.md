# 2026-06-22 — Unified round economy NL reply (RBE + cash + XP)

> **Status:** `complete`

Owner-directed (the maintainer approved the round-economy consolidation idea
filed in the #1324 session: "Yes that's a good idea you can implement that").
Round economy data (RBE, cash, cumulative cash, XP) was answered by three
separate paths — cash via `ai_round_cash_workflow`, XP via
`deterministic_round_xp_reply` (#1324), RBE via none — so "what's the economy of
round 95?" had no single answer even though the round embed already shows all
three together. This adds one consolidated reply.

## Shipped

- **`disbot/services/btd6_context_service.py`** — `deterministic_round_economy_reply`,
  a pre-emptive BUG-0009 floor builder grounded on `RoundEntry` (RBE / cash /
  cumulative cash) + `round_base_xp`. Fires on a round number + an economy cue
  (`economy` / `overview` / `summary` / `stats` / `rewards` / `rbe` /
  `breakdown`); supports ABR via the standard `_ABR_CUE_RE` (cash + RBE differ
  between sets, XP does not). Registered **before** `deterministic_round_xp_reply`
  in `_BTD6_LIST_BUILDERS` so a multi-stat / economy question gets the
  consolidated answer while a pure "how much xp" (no economy cue) still routes to
  the narrower XP reply.
- **Tests** — `test_btd6_round_economy_reply.py` (RBE+cash+XP presence, grounding
  on the helpers, multiple economy cues, ABR support, the three defer paths,
  dispatcher routing, and the pure-XP-question-defers-to-XP-builder boundary) +
  a `_SHOULD_FIRE` corpus entry in the floor-exclusivity invariant.

Verified: economy + xp-reply + floor-exclusivity suites green (52 passed); `mypy`
clean; `check_architecture --mode strict` 0 errors; full `check_quality --full`
run before flipping this card ready.

## ⚑ Self-initiated

No — owner-directed (explicit "Yes that's a good idea you can implement that").
PR #1326 opened born-red → flipped ready; auto-merge armed (Q-0191 owner-directed
→ merge on green).

## 💡 Session idea (Q-0089)

**Surface the round economy on the embed/`!btd6 round N` path with the *scaled*
XP, difficulty-aware.** The NL economy reply and the embed both show the Beginner
base XP; a player on an Expert map earns ×1.3. A small follow-up: let the embed
(and the economy reply) optionally echo the four difficulty XP values
(or at least name the scaling) the same way the standalone XP reply already does,
so the consolidated answer is as difficulty-complete as the dedicated one.
Genuine: `round_xp_earned` already computes it; it's a formatting extension, not
new modelling.

## ⟲ Previous-session review (Q-0102)

The #1324 session surfaced round XP in two places and *filed* this consolidation
as a Q-0089 idea rather than building it — correct scoping (it kept #1324 a clean
two-surface change), and the idea was specific enough that this session could pick
it up directly with no re-discovery. That's the idea-backlog loop working as
designed: a session generates a concrete, buildable idea; the next one ships it.
System note: the BTD6 round-answer surface now has four builders/paths
(cash workflow, XP reply, economy reply, embed) — worth a short
`docs/subsystems/btd6.md` note mapping "round question shape → which path owns it"
so the next agent doesn't add a fifth overlapping one. Filed as a grooming
candidate.

## 🔎 Doc audit (Q-0104)

- economy + exclusivity + xp suites + `mypy` + `check_architecture` green; full
  `check_quality --full` before flipping ready.
- No owner-decision/router change (a feature build on owner direction).
- No `current-state` ledger touch — recorded by the auto-triggered Q-0107
  reconciliation pass. Unmerged PR #1326 correctly absent.
- The reply is self-documenting (builder docstring + cue-regex comment); the
  "round-question shape → owning path" map is filed as the Q-0089/grooming note
  above, not a gap this PR leaves open.

## Context delta

- **Needed but not pointed to:** the dispatcher's order-resolves-genuine-overlap
  contract — registering the broader economy builder *before* the narrower XP
  builder is exactly the documented pattern (multi-entity before single), but it
  is easy to get backwards. The exclusivity invariant + the explicit
  "pure-XP-defers" test pin it.
- **Pointed to but didn't need:** nothing notable — a contained, single-builder
  addition reusing the round-number regex and ABR cue already in the module.
