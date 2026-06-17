# Session — night-queue slot 3: relic category/effect roster floor

> **Status:** `in-progress`

## Origin

Same scheduled dispatch fire that shipped slot 2 (#1008, power cost comparison),
continuing down the ▶ NIGHT QUEUE
([`planning/night-queue-2026-06-16.md`](../docs/planning/night-queue-2026-06-16.md))
now that #1008 has merged to `main`. Topmost `TODO` = **slot 3 — relic
category/effect roster** (§7.6). One PR.

## What I'm about to do

Add the **relic** member of the §7.6 BUG-0009 roster floor — the Contested
Territory sibling of the shipped capability roster (towers) and bloon roster
(#975). "what economy relics are there?", "list all offensive relics", "which
relics are utility?" buckets the 24 CT relics by `category` (+ each relic's
`effect`) so the model can never mis-bucket the list (every relic name is
grounded, so the value-only faithfulness guard can't catch a mis-*grouping*).

- `btd6_data_service.relics_by_category()` — group `ct_relics.json` by `category`
  in a fixed display order, name-sorted within each group.
- `btd6_context_service.deterministic_relic_roster_reply` — fires on a relic
  subject + an enumeration shape; a named category lists that category's relics +
  effects, a bare "all relics" lists every relic grouped; defers on single-relic
  effect lookups ("what does the el dorado relic do") and strategy. Registered in
  `_BTD6_LIST_BUILDERS` after the bloon roster.
- Tests: `tests/unit/services/test_btd6_relic_roster.py` + an exclusivity corpus
  should-fire phrase.

Ships under **Q-0048** (read-only deterministic floor, no prod-check, auto-deploys).
