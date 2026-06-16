# 2026-06-16 — BTD6 paragon base-cost comparison floor (AI §7.5)

> **Status:** `complete`

**Branch:** `claude/magical-rubin-u3arq6` · **Date:** 2026-06-16 · scheduled dispatch (empty work
order → advance the next plan slice).

## What I'm about to do

The live ▶ NEXT buildable plan-first lane is **the AI §7 next workflow family**. §7.5 (multi-entity
comparison) has now shipped three of its four listed members — tower-vs-tower cost (#946),
by-difficulty cost (#950), round-range cash (#955). The one member still flagged *not yet built* in
the plan (`docs/ai/ai-complex-request-tool-orchestration-plan.md` §7.5) is **paragon
degree/resource scenarios**. I'm building the **paragon base-cost** comparison — the paragon entity's
headline resource number (its tier-6 build price), fully grounded in `utils/btd6/paragon_math`'s
committed `BASE_PRICES_MEDIUM` table and difficulty-aware via `base_price`, so it ships under Q-0048
with no prod-check exactly like the sibling cost builders.

Question shape: "is Glaive Dominus or Ascended Shadow cheaper?" / "which paragon costs the most?" —
rank the base build price of **two or more** paragons. This is the §7.5 comparison member of the
BUG-0009 "grounded values, wrong assembly" class: each paragon's base price is grounded, but a model
can mis-state *which is cheaper / by how much*, which the value-only faithfulness guard cannot catch.

Plan (mirrors #946/#950/#955 exactly, contained + test-covered):
- `btd6_data_service.compare_paragon_costs(names, *, difficulty="medium")` — resolve each name via
  `paragon_math.resolve_paragon`, price via `paragon_math.base_price`, dedup on paragon id, rank
  **ascending** (cheapest first), fail closed (<2 distinct priceable paragons).
- `btd6_context_service.deterministic_paragon_cost_comparison_reply` — high-precision floor: the
  existing cost-compare cue **+ an explicit `paragon` token** + two-or-more resolved paragons.
  Appended to `deterministic_btd6_list_reply` **before** the tower cost builders, and the two tower
  cost builders gain a `paragon`-present defer so the exclusivity invariant stays exactly-one-fires
  (a "dart/ninja paragon" question must not reach the base-tower cost builder).
- Tests: a new per-builder test module + the §7.5 exclusivity corpus entry (the invariant test
  iterates the live `_BTD6_LIST_BUILDERS` tuple, so the new builder needs a corpus phrase).

If capacity remains: a second clean slice (next plan member, a bug-book sweep, or a docs de-stale).

## ✅ Done — PR #962 (self-merge on green via born-red flip, Q-0113/Q-0133)

**The §7.5 paragon comparison member — the last unbuilt member is now shipped.**

- `btd6_data_service.compare_paragon_costs(names, *, difficulty="medium")` — resolves each name via
  `paragon_math.resolve_paragon`, prices the **base tier-6 build cost** via `paragon_math.base_price`
  (difficulty-adjusted with the shared BTD6 multipliers), dedups on paragon id, ranks ascending,
  fails closed (<2 distinct). Two paragons share a $500k base, so `all_equal`/tie is a real outcome.
- `paragon_math.paragon_surfaces()` — new public helper exposing every resolver surface (names /
  towers / ids / aliases) so the floor can scan *all* paragon mentions in a sentence the same way
  `resolve_paragon` matches one (the alias map was module-private; exported a scan view, not the map).
- `btd6_context_service.deterministic_paragon_cost_comparison_reply` + `_extract_paragon_names` +
  `_format_paragon_cost_comparison` — high-precision floor: explicit `paragon` token + cost-compare
  cue + ≥2 resolved paragons. Registered in `_BTD6_LIST_BUILDERS` **before** the tower cost builders.
- **Exclusivity:** both tower cost builders now defer the moment `_PARAGON_CUE_RE` matches, so a
  "dart/ninja paragon" question (tower aliases present) is never priced as the base tower. Pinned by
  the §7.5 exclusivity invariant (new corpus phrase) + a dedicated builder-tuple test.
- Tests: `tests/unit/services/test_btd6_paragon_cost_comparison.py` (21 cases) + the exclusivity
  corpus entry. Plan §7.5 de-staled (member marked SHIPPED).

Verification: `check_architecture --mode strict` ✓ · `check_quality --full` ✓ (10051 passed) ·
new+invariant+paragon-math suites 53 passed.

## Context delta (what the next session should know)

- **Needed but not pointed to:** the §7.5 comparison floor is a *family* with a hard exclusivity
  invariant (`tests/unit/invariants/test_btd6_floor_builder_exclusivity.py`) that runs **every**
  builder against a corpus and asserts exactly-one-fires. Any new floor builder MUST (a) be added to
  `_BTD6_LIST_BUILDERS` and (b) get a `_SHOULD_FIRE` corpus phrase, or the coverage test fails. The
  orientation route to `btd6_context_service` doesn't flag this — found it by reading the invariant.
- **Discovered by hand:** the resolver's alias map (`paragon_math._ALIASES`) was private; scanning a
  sentence for *all* paragons needs a public surface view — now `paragon_surfaces()`.
- **Decisions made alone:** the paragon comparison axis is **base build price** (the headline,
  unambiguous, fully-grounded paragon resource number), not a target-degree resource solve — the
  least-cash solve collapses to all-equal for most sub-cap targets, so it is a poor comparison axis.
  The plan said "degree/resource scenarios" loosely; base price is the clean, honest member. If the
  owner wants a *degree-target* resource comparison ("cheapest to reach degree 100"), that is a
  follow-on slice on top of `solve_requirements` — captured below as the session idea.
- **Flagged for maintainer / known limit:** the reply compares **base price only** and says so
  explicitly in its footer; it deliberately does not fold in the degree-grind sacrifices (those
  depend on the player's build). No prod-check needed (Q-0048 read-only deterministic floor).

## Session enders

**💡 Session idea (Q-0089).** *Paragon degree-target resource comparison* — a `compare_paragon_to_degree`
member: "is it cheaper to get Glaive Dominus or Ascended Shadow to degree 100?" ranks the
least-cash `solve_requirements` cost-to-target across paragons. Distinct from this slice (base price
vs. degree-grind resources); genuinely useful for the "which paragon should I commit to" question.
Worth a small idea file if the owner wants the degree axis — dedup-checked against `docs/ideas/` and
the §7.5 plan (only the base-price member existed as "paragon scenarios"; the degree-target framing
is new). Captured here, not promoted (a new idea is not a new priority).

**⟲ Previous-session review (Q-0102).** The previous §7.5 session (#955, round-range) did this lane
*right*: it explicitly noted "if capacity remains, assess the paragon member as a second slice" — a
clean, scoped handoff that made this session trivial to start. What it could have done better: it
shipped two round-range slices and stopped, leaving the named paragon member for a *whole separate
dispatch* when both are ~80-line mirror builders — finishing the §7.5 family in one session was
within reach. **System improvement surfaced:** the exclusivity invariant is excellent, but the
*family-completion* signal lives only in prose ("members still unbuilt") inside a 600-line plan; a
tiny `_SHIPPED`/`_UNBUILT` ledger at the top of the §7.5 plan section (or a check that greps the
builder tuple against a declared member list) would make "is the comparison family done?" answerable
without reading the plan body. Folded as a note, not built (docs-shape, low value vs. the plan prose).

**Doc audit (Q-0104).** Plan §7.5 de-staled (member SHIPPED). active-work claim added at open (to be
cleared at close). No new owner decision (the base-price axis choice is an in-lane engineering call,
recorded above; if the owner wants the degree axis it routes through the session idea). The ledger
`⚠ N PRs not in current-state` drift is the **reconciliation routine's lane** (next pass at #960,
Q-0124) — not this dispatch session's to reconcile.

## 📤 Run report

- **Did:** shipped the §7.5 paragon base-cost comparison floor — the last unbuilt multi-entity
  comparison member, completing the family · **Outcome:** shipped
- **Shipped:** #962 — `compare_paragon_costs` + `deterministic_paragon_cost_comparison_reply`
  (deterministic paragon base-price ranking; BUG-0009 wrong-assembly floor; Q-0048 read-only, no
  prod-check). CI mirror green (10058); arch 0; auto-merge armed on green.
- **⚑ Owner decisions needed:** `none` (the base-price comparison axis is an in-lane engineering
  call; the optional paragon *degree-target* axis is captured as a session idea, not a decision).
- **⚑ Owner manual steps:** `none` (merge auto-deploys; no seed-data / env / Discord step).
- **↪ Next:** the §7.5 comparison family is COMPLETE — next AI §7 work is a *new* workflow family
  beyond §7.5 (plan-first / prod-check-gated for model-loop families); the buildable deterministic
  floor members are exhausted. Other plan-first lanes: image moderation (Q-0108), Hermes bug-triage
  `gh issue create` write (Q-0121). See current-state ▶ NEXT.

