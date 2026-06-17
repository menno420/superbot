# Session — night-queue slot 2: power (activated-ability) cost comparison floor

> **Status:** `complete`

## Origin

Scheduled dispatch, empty work order → the live ▶ NIGHT QUEUE
([`planning/night-queue-2026-06-16.md`](../docs/planning/night-queue-2026-06-16.md)).
Slot 1 (hero cost comparison) shipped #1000; the topmost `TODO` is **slot 2 —
power (activated-ability) cost comparison** (§7.5). One PR.

## What I'm about to do

Add the **power** member of the §7.5 multi-entity cost-comparison floor — the
power-store sibling of the shipped paragon (#962) / tower (#946) / difficulty
(#950) / hero (#1000) builders. "Which power is cheaper, Cash Drop or Monkey
Boost?" ranks the **monkey-money** store price of two-or-more powers — the
BUG-0009 "grounded values, wrong assembly" class the value-only faithfulness
guard can't catch. Powers cost **monkey money** (fixed, not difficulty-scaled),
so this primitive has no difficulty axis (the one shape difference from #1000).

- `btd6_data_service.compare_power_costs(names)` — resolve each via the shared
  `find_power` resolver, dedup on id, rank ascending by `monkey_money_cost`, fail
  closed (<2 distinct).
- `btd6_context_service.deterministic_power_cost_comparison_reply` — fires on a
  cost-compare cue + ≥2 resolved powers; defers on a paragon cue / strategy /
  single-power lookups. Registered in `_BTD6_LIST_BUILDERS` after the hero builder.
- Tests: `tests/unit/services/test_btd6_power_cost_comparison.py` + an exclusivity
  corpus should-fire phrase.

Ships under **Q-0048** (read-only deterministic floor, no prod-check, auto-deploys).

## Done

- `btd6_data_service.compare_power_costs(names)` — Monkey-Money ranking, no
  difficulty axis (powers are a fixed store price; the one shape difference from
  the #1000 hero builder).
- `btd6_context_service.deterministic_power_cost_comparison_reply` +
  `_extract_power_names` + `_format_power_cost_comparison`; registered in
  `_BTD6_LIST_BUILDERS` after the hero builder.
- `tests/unit/services/test_btd6_power_cost_comparison.py` (16 tests) + the
  exclusivity-corpus should-fire phrase.
- Docs: night-queue slot 2 ticked `✅ #1008`; current-state ▶ NIGHT QUEUE
  re-pointed at slot 3 (relic roster) + a Recently-shipped ledger line.
- `check_quality.py --full` GREEN (10292 passed, +38) · `check_architecture
  --mode strict` 0 errors (only pre-existing `[known]` warnings).

**Data note found while building (not a bug, recorded for the next slice-author):**
several power canonicals carry in-game flavour punctuation — `"Battle Cat!"` (trailing
`!`), and renamed entries where the canonical no longer matches the id
(`dart_time` → `"Time Stop"`, `she_ra` → `"Sword of Protection"`, `skeletor` →
`"Havoc Staff"`, `monkey_boost_pro` → `"Hype Boost Monkey"`, `stamina_potion` →
`"Banana Cookies"`). The `\bcanonical s?\b` word-boundary extractor therefore does
**not** match a punctuation-bearing canonical typed without the punctuation — fine
for this cost-compare floor (the cost cue + ≥2-powers gate keep it conservative),
but the slot-3 relic roster author should resolve on `find_power`/`find_*`'s
substring-partial path, not a strict surface scan, if a relic name has the same
shape.

## Handoff → next dispatch

Slot 2 done. **Next ▶ = night-queue slot 3 — relic category/effect roster (§7.6)**
(`ct_relics.json` → `category` + `effect`; mirror the #975 roster builders;
`deterministic_relic_roster_reply`). Slots 4 (bloon property roster) + 5 (hero
ability roster) follow. Per the per-fire discipline in the queue doc: **sync
`origin/main` first** (this PR appends to the shared `_BTD6_LIST_BUILDERS` +
`_SHOULD_FIRE` anchors — let it merge before branching the next slice, or the
appends conflict).

## 💡 Session idea (Q-0089)

The night-queue slices share a near-identical primitive shape — *resolve N
entities → dedup on id → rank by one numeric axis → fail closed <2*. Hero (#1000)
and power (#1008) are byte-for-byte the same logic bar the resolver + axis field.
**Idea:** extract a tiny generic `rank_entities_by(items, key, *, name, ident)`
helper in `utils/btd6/` (or a `_compare_costs` private in `btd6_data_service`) that
the per-entity `compare_*_costs` primitives call, so a new comparison slice is ~5
lines (pick resolver + axis) instead of a copied 40-line block. Lowers the cost of
every remaining §7.5 comparison and removes the copy-paste drift risk (the spread/
all_equal/tie-break logic is currently duplicated five times). Filed as worth doing
when the comparison family is "done" enough to see the stable shape — captured here,
not built, to keep this PR one clean slice.

## ⟲ Previous-session review (Q-0102)

Previous run: **#1007** (`test(btd6): class-guard corpus for community-shorthand
routing`). *Did well:* it was a pure test-hardening PR that pinned routing
behaviour with a corpus — exactly the kind of cheap, durable regression guard the
BUG-0009/community-shorthand lane benefits from. *Could improve / system note:* the
ledger guard still flags **6 merged PRs not yet in current-state** at this session
start (the SessionStart `Ledger: ⚠` banner). That backlog is precisely what the
Q-0107 reconciliation routine exists to absorb, and it's not yet due (#1020). The
small workflow improvement this surfaces: a dispatch fire shipping a *new* ledger
line (like this one) could opportunistically reconcile **one** of the already-merged
stragglers it can cheaply verify, rather than only appending its own — shrinking the
gap the reconciliation pass has to close in one batch. Not done here (out of this
slice's scope + the strict ledger checker is the reconciliation routine's tool), but
worth a router note if the straggler count keeps growing between passes.

## 📋 Doc audit (Q-0104)

`current-state.md` ▶ NIGHT QUEUE re-pointed; the new #1008 ledger line added; the
night-queue table ticked. The standing `Ledger: ⚠ 6 merged PR(s) not yet in
current-state` predates this session (see the previous-session review) and is the
reconciliation routine's job — not introduced or worsened here. No new owner
decision, no new doc home needed (this slice rides the existing §7.5 floor seam).
