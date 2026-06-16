# Session — BTD6 round-range cash comparison floor (AI §7.5)

> **Status:** `complete`

**Branch:** `claude/magical-rubin-7iavf2` · **Date:** 2026-06-16 · scheduled dispatch (empty work
order → advance the next plan slice)

## What I'm about to do

The live ▶ NEXT buildable plan-first lane is **the AI §7 next workflow family**. §7.5 (multi-entity
comparison) has shipped its **cost** members — tower-vs-tower (#946) and by-difficulty (#950). The
plan lists two members still unbuilt: **paragon degree/resource** and **round-range cash**. I'm
building the **round-range** member — it has clean, fully-deterministic data (`round_cash` already
owns inclusive-range cash for both the standard and ABR round sets), so it ships under Q-0048 with no
prod-check, exactly like the sibling cost builders.

Question shape: "which earns more cash, rounds 20-40 or 40-60?" — rank the total cash of **two or
more** round ranges. This is the §7.5 comparison member of the BUG-0009 "grounded values, wrong
assembly" class: each per-round figure is grounded, but a model can mis-state *which range earns
more / by how much*, and the value-only faithfulness guard can't catch a mis-ranking.

Plan (mirrors #946/#950 exactly, contained + test-covered):
- `btd6_data_service.compare_round_ranges(ranges, *, roundset="default")` — the §7.5 round-range
  rank/diff primitive; price each inclusive range once via the existing `round_cash`, dedup
  normalized ranges, rank by cash **descending** (the question asks which earns *more*), fail closed
  (<2 distinct priceable ranges).
- `btd6_context_service.deterministic_round_range_comparison_reply` — high-precision floor: an
  earning-comparison cue (`more cash`/`earn more`/`which … money` + comparison signal) + a cash noun
  + **two or more** parsed round ranges; ABR cue → the ABR round set. `None` otherwise (a single
  range is the round-cash workflow's job — they stay non-overlapping on range count, and the floor
  short-circuits before the workflow ever runs). Appended to `deterministic_btd6_list_reply`.
- Tests: firing (2 ranges / 3 ranges / single-round endpoints / ABR cue / spread / tie), and the
  negatives (one range → defer to workflow, no cash cue, no comparison signal, strategy).

If capacity remains: assess the **paragon** §7.5 member as a second slice.

## ✅ Done — two slices, PR #955 (self-merge on green, Q-0113)

**Slice 1 — §7.5 round-range cash comparison floor:**
- `btd6_data_service.compare_round_ranges(ranges, *, roundset="default")` — prices each inclusive
  range once via the existing `round_cash` (the round-cash workflow's own owner), dedups normalized
  `(lo, hi)`, ranks **descending** (most cash first), fails closed (<2 distinct priceable ranges),
  ABR-aware. Single-round segments (`lo == hi`) contribute their own `round_cash`.
- `btd6_context_service.deterministic_round_range_comparison_reply` + `_extract_round_ranges` /
  `_format_round_range_comparison` / `_fmt_money` — fires on an earning noun + a comparison signal +
  **≥2** parsed round ranges (a round token required before each range's first anchor, so `5-0-0`
  crosspaths are never mis-read); ABR cue → alternate set. Appended to the dispatcher.
- Non-overlap with the single-range round-cash workflow is structural: this floor requires ≥2 ranges
  **and** short-circuits before the workflow ever runs (verified in `natural_language_stage`).
- 18 tests (`tests/unit/services/test_btd6_round_range_comparison.py`); smoke-verified live (rounds
  40-60 = $38,149 > 20-40 = $12,824; ABR-aware; crosspath/single-range/strategy negatives defer).

**Slice 2 — floor-builder exclusivity invariant (promotes the #950 Q-0089 idea):**
- Extracted the dispatcher's builder tuple to a module-level `_BTD6_LIST_BUILDERS` (behaviour
  identical) so the invariant iterates the **live** tuple.
- `tests/unit/invariants/test_btd6_floor_builder_exclusivity.py` — runs **every** builder against a
  curated corpus; asserts **exactly one** fires per should-fire phrase (the expected one, and the
  dispatcher serves it) and **zero** on should-defer phrases; a coverage test fails if a builder is
  added to the dispatcher without a corpus phrase. Makes the prose "the builders don't overlap"
  contract executable across all 6 (now growing) builders. 14 tests, all green.

De-staled docs: AI §7.5 plan (round-range ✅#955; only paragon remains) + current-state ▶ ledger
entry; held the Recently-shipped ratchet at 20 by archiving #905 to `current-state-archive.md`.
`check_quality --full` green (**10022 passed**, +36); `check_architecture --mode strict` 0 errors;
mypy clean.

## ▶ Handoff — next dispatch

§7.5 now covers **cost** (tower #946 + difficulty #950) **+ round-range cash** (#955). The one
remaining §7.5 member is **paragon degree/resource** — and it needs scoping, not just a copy of the
cost builder. Data findings from this run:
- **`paragon_cost` lives on `TowerStats`** (`btd6_stats_service.get_tower_stats(tower_id).paragon_cost`,
  used by `btd6_superlative_service._paragon_cost_rows`) — it is the **degree-1 build cost**, keyed by
  **tower_id**.
- **`btd6_stats_service.resolve_paragon(query)` returns a *paragon_id*** (not tower_id), single-result
  (first match in the sentence). A comparison needs a **multi-paragon scanner** (the paragon analogue
  of `_scan_towers_with_positions`) over paragon proper names ("Apex Plasmaster", "Navarch of the
  Seas"), each → tower_id → `paragon_cost`. There is a `_paragon_index()` tower_id↔paragon_id map.
- **Spec decision needed:** the clean, fully-deterministic member is a **paragon build-cost
  comparison** (degree-1 totals) — ships under Q-0048 like the cost siblings. "Cost/resource to reach
  **degree N**" is the `paragon_service` reverse-solve, which is **API-backed / non-deterministic** —
  defer it or owner-gate it; do not put a non-deterministic number on the pre-emptive floor.
Otherwise: the AI §7 families beyond §7.5, or BUG-0009 slice 3 (newest-towers, still `data`-gated).

## 💡 Session idea (Q-0089)

`docs/ideas/round-range-comparison-bare-range-list-2026-06-16.md` — accept **round-anchored bare-range
lists** in the new round-range floor. Today it needs a round token before *each* range's first anchor
(to keep `5-0-0`-style crosspaths out), so "rounds 1-30, 30-60 or 60-80" (token only on the first)
silently defers to the model — the exact BUG-0009 mis-assembly class the floor exists to own. Once ≥1
explicit round-token range is present, accept subsequent bare `N-M` ranges that are not
crosspath-adjacent. Genuine, specific, born from this session's own conservatism trade-off;
dedup-checked against `docs/ideas/`; README-indexed. *(Distinct from slice 2, which **promoted** the
#950 session's existing idea — this is a new one.)*

## ⟲ Previous-session review (Q-0102)

Previous run = **#953 (BTD6 Live Events — dead drill-down crash + current-event-first redesign).**
Did well: root-caused a 100%-broken user-facing feature (every event drill-down `TypeError`'d on a
nonexistent `search_facts(entity_key=…)` kwarg) that shipped green **because** a bare `AsyncMock` was
more permissive than the real function, then redesigned the browser current-event-first and fixed a
latent boss-metadata suffix bug — diagnosis-from-a-screen-recording to root cause, defense-in-depth.

**System improvement it surfaces (act on it):** #953's own Q-0089 idea —
`autospec-mock-fidelity-guard` — is genuinely load-bearing, not filler: a mock more permissive than
reality shipped a fully-broken feature past CI. It should not sit as an idea. A future AI/testing-lane
session with capacity should build the **lightweight slice first** — `AsyncMock(spec=real_fn)` /
`create_autospec` for the **`btd6_db` / service-facade** seams the floor + view-model code call
through — which is exactly where the #953 crash hid. That single targeted application (not a repo-wide
lint yet) would have turned that production crash into a red test, and it directly protects the
deterministic-floor work this chain keeps extending. (No filler — this is the concrete, specific gap.)

## 📋 Doc audit (Q-0104)

- `check_current_state_ledger --strict`: 8 recent merges (#944/#945/#947/#948/#949/#951/#952/#953)
  not yet entered — **left for the reconciliation routine** (full-ledger catch-up is its lane per
  Q-0124; next cadence pass fires at #960). My own #955 entry is in; ratchet held at 20 by archiving
  #905 → `current-state-archive.md` (the ledger guard now resolves #905 from the archive).
- New owner decisions / router Q: none this run.
- Docs reachable: `check_docs --strict` green; the §7.5 plan + ledger entry cross-reference
  #946/#950/#955; the new idea is README-indexed.
