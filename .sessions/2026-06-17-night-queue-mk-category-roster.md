# Session — night-queue buffer slices: MK category roster (+ planned slot-4 reframe)

> **Status:** `in-progress`

## Origin

Scheduled dispatch fire, no work order → advance the ▶ NIGHT QUEUE
([`planning/night-queue-2026-06-16.md`](../docs/planning/night-queue-2026-06-16.md)).
The §7.5/§7.6 ready slots are all consumed (#1000/#1008/#1009/#1010); slot 4 is
`NEEDS-REFRAME`. Next work per the prior handoff = the **buffer slices**: the
*Monkey-Knowledge category roster* and the *Geraldo items-by-unlock-level roster*.
No new actionable bug in the bug-book (BUG-0011 is the OPEN Hermes-gateway issue,
out of scope here).

## What I'm about to do

**Slice 1 — Monkey-Knowledge category/tab roster (§7.6).** The MK member of the
BUG-0009 roster floor. "what Support monkey knowledges are there?", "list all
Military monkey knowledge" — buckets the 134 MK by its in-game tab so the model
can never mis-bucket the grouping (the inverse of the owner's verbatim "related to
the farm" miss). Distinct from the shipped `deterministic_mk_reference_reply`
("MK related to <tower>"): fires only on a *tab* cue and defers when a tower is
named, so the two MK builders never both fire.

- `btd6_data_service.monkey_knowledge_by_category()` — group by tab in the in-game
  order, name-sorted within each tab.
- `btd6_context_service.deterministic_mk_category_roster_reply` — MK cue + a named
  tab (Primary/Military/Magic/Support/Heroes/Powers) + an enumeration cue; defers
  on strategy, no-tab, and a named tower. Registered after the relation builder.
- Tests: `tests/unit/services/test_btd6_mk_category_roster.py` + an exclusivity
  corpus should-fire phrase.

Then **slice 2** (a second buffer/clean slice) in the same fire, syncing
`origin/main` between PRs per the per-fire discipline.

Ships under **Q-0048** (read-only deterministic floor, no prod-check, auto-deploys).
