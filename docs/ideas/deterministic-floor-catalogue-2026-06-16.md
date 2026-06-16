# Idea — a generated "deterministic floor catalogue" index

> **Status:** `ideas` — captured 2026-06-16 (Q-0089 session ender, from the AI §7.6 capability/bloon
> roster-floor PR #975). Small/safe/decided-lane agent-tooling enhancement. Owner of the area: AI / BTD6 floor.

## The friction

`btd6_context_service._BTD6_LIST_BUILDERS` now grows roughly **one member per dispatch run**
(BUG-0009 list floors → §7.5 comparison floors → §7.6 roster floors). Each session that picks up
"the next AI §7 floor" must first answer *what is already fronted, and which data surface has no
floor yet?* — and the only way to answer it today is to grep the dispatcher tuple and read every
builder + the service it calls (the navigation cost this PR paid first-hand). The coverage of the
deterministic-floor family is **tribal knowledge**, recoverable only by re-reading the source.

## The idea

A tiny stdlib script (`scripts/btd6_floor_catalogue.py`, read-only, disposable per Q-0105) that:

- introspects the **live** `_BTD6_LIST_BUILDERS` tuple (so it never drifts from source),
- maps each builder → its representative trigger phrase (reuse the exclusivity-test corpus) and the
  service/data surface it fronts (e.g. `deterministic_capability_roster_reply` →
  `btd6_capability_service.towers_with_capability`),
- and **flags roster-shaped service surfaces that have NO floor yet** — e.g. hero capability
  rosters, CT-relic property lists — so the next unbuilt member is obvious, not discovered.

Output is a short generated index (or a `--json` for a future Hermes dispatch-resolve consumer).

## Why it's worth having

It directly removes the per-session "what's the next floor?" navigation cost, and it makes the
family's coverage **legible** — the same legibility win the floor-builder exclusivity invariant
(`test_btd6_floor_builder_exclusivity.py`) gave the *non-overlap* contract, applied to *coverage*.

## Disposition

Decided-lane, small — execute as a backlog-grooming slice in a future dispatch run, or fold into the
next §7.6 roster PR (the script's "surfaces with no floor" output IS that PR's worklist).

→ relates `services/btd6_context_service.py::_BTD6_LIST_BUILDERS` ·
`services/btd6_capability_service.py` · `tests/unit/invariants/test_btd6_floor_builder_exclusivity.py`.
