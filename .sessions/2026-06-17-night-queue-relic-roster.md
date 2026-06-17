# Session — night-queue slot 3: relic category/effect roster floor

> **Status:** `complete`

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

## Done

- `btd6_data_service.relics_by_category()` — fixed-order category grouping,
  name-sorted within each group.
- `btd6_context_service.deterministic_relic_roster_reply` + `_match_relic_category`
  + `_mentions_specific_relic` guard + two formatters (per-category roster with
  effects · all-relics grouped view). Registered in `_BTD6_LIST_BUILDERS` after the
  bloon roster.
- `tests/unit/services/test_btd6_relic_roster.py` (12 tests) + the exclusivity
  corpus should-fire phrase.
- Docs: night-queue slot 3 ticked `✅ #1009`; current-state ▶ NIGHT QUEUE
  re-pointed at slot 4 (bloon property roster) + a Recently-shipped ledger line.
- `check_quality.py --full` GREEN (10304 passed, +12) · `check_architecture
  --mode strict` 0 errors.

**Design note:** the relic builder keys on the literal `relic` token (subject) +
an enumeration shape, which makes it mutually exclusive with the power/bloon/cost
builders for free (none of them key on "relic"). The one trap — "what does the el
dorado relic do" matches the enumeration regex by accident — is closed by the
`_mentions_specific_relic` surface scan (defers when a specific relic is named and
no category keyword is present).

## Two-slice fire summary

This scheduled fire shipped **two** complete night-queue slices end to end:
**#1008** (slot 2, power cost comparison) → merged → **#1009** (slot 3, relic
roster). The per-fire discipline held: slot 3 was branched off `main` only **after**
#1008 merged, so the shared `_BTD6_LIST_BUILDERS` + `_SHOULD_FIRE` appends never
conflicted.

## Handoff → next dispatch

**Next ▶ = night-queue slot 4 — bloon property roster (§7.6)** (`bloons.json` →
`properties[]`; sibling to the shipped `deterministic_bloon_roster_reply`, which it
**must defer to** on the MOAB-class / immunity cues — extend the exclusivity corpus
with a should-defer phrase pinning the split). Then slot 5 (hero ability roster).
Per the queue's per-fire discipline: **sync `origin/main` first** and let #1009
merge before branching slot 4 (shared append anchors).

## 💡 Session idea (Q-0089)

(One idea per fire — recorded in the slot-2 log
[`2026-06-17-night-queue-power-cost-comparison.md`](2026-06-17-night-queue-power-cost-comparison.md):
extract a generic `rank_entities_by(...)` helper so each §7.5 comparison primitive
is ~5 lines instead of a copied 40-line block.) **Roster-family extension of the
same idea:** the §7.6 roster builders (capability · bloon · relic · the queued
hero-ability) share the *roster shape* — `subject cue + enumeration cue + optional
category filter → grouped/labelled list, defer on single-entity lookup`. A second
helper, `roster_reply(subject_re, list_re, grouper, *, category_cues, specific_guard)`,
would collapse each new roster builder to its three cues + a grouper, the same way
the comparison helper would collapse the cost builders. Worth doing once slot 5
lands and the roster shape is fully stable (4 instances = enough to see the
abstraction). Captured, not built (keeps each PR one clean slice).

## ⟲ Previous-session review (Q-0102)

The *immediately* previous run in this same fire was slot 2 (#1008). *Did well:* it
left a precise, actionable handoff in `current-state` ▶ NIGHT QUEUE and a per-fire
discipline reminder, which let slot 3 start cleanly the moment #1008 merged — the
handoff loop worked exactly as designed (this fire is the proof: two slices, zero
conflict). *Could improve / system note:* slot 2's log flagged the 6-PR ledger
straggler backlog but (correctly, for scope) didn't touch it; that backlog is still
open and is the reconciliation routine's job (#1020 boundary). No new improvement to
add beyond slot 2's note — the system behaved well across the two-slice chain, and
inventing a second critique would be the filler Q-0102 warns against.

## 📋 Doc audit (Q-0104)

`current-state.md` ▶ NIGHT QUEUE re-pointed to slot 4; #1009 ledger line added; the
night-queue table ticked `✅ #1009`. No new owner decision; this slice rides the
existing §7.6 roster floor seam (no new doc home). The standing `Ledger: ⚠` merged-PR
backlog predates this fire and remains the reconciliation routine's lane (not due
until #1020) — not introduced or worsened here.
