# 2026-06-09 — AI + BTD6 answerability: Phase 1A (deterministic round-cash query)

## Arc

Maintainer asked to implement the codex plan from the most recent PR (#611,
`docs/planning/ai-btd6-answerability-roadmap-2026-06-09.md`) — "use it as guidance,
verify it yourself." Verified the plan against source (it is sound), then implemented its
recommended first slice: **Phase 1A**, the deterministic BTD6-owned round-cash query. The
5-phase roadmap far exceeds one session and Phases 1B–5 are gated, so this session lands
1A completely and stops at the gate.

## Shipped

- `disbot/services/btd6_data_service.round_cash(round_start, round_end=None)` — a pure,
  read-only sibling of `round_composition` / `cumulative_upgrade_costs`. Owner-calculates
  the **inclusive** range total (`range_cash`), exposes the cumulative endpoints
  (`cumulative_before_start` / `cumulative_at_end`) so the `cumulative(B) − cumulative(A−1)`
  identity is explicit, normalizes reversed ranges, and returns structured `invalid_range`
  / `cash_unavailable` refusals (never a fabricated number). Economy assumptions
  (standard/default round set, Medium $650 start, no income towers, no Double/Half-Cash)
  are returned as a field, not left implicit.
- 20 new tests in `tests/unit/services/test_btd6_round_cash.py` pinning every row of the
  roadmap's Phase 1A semantics table (incl. an explicit pin that A–B counts **both**
  endpoints — `range_cash != cumulative(B) − cumulative(A)`).
- Docs: marked Phase 1A shipped in the roadmap (top Progress marker + Phase 1A note);
  added a "Recently shipped" entry + "Last updated" clause to `docs/current-state.md`.

## Why only 1A (gate reasoning)

- Phase 1A adds **zero AI/user-facing behaviour** (nothing calls `round_cash` yet), so it
  sits *below* the global AI/BTD6 feature-expansion gate — it is a deterministic data
  derivation + tests, not an AI feature or a data-extraction pass.
- Phase 1B (register a net-new `btd6_round_cash` AI tool + intent-shaped grounding) is
  blocked by the owner decision **AR-10** ("lock the orchestration foundation before any
  net-new tools"), which the roadmap itself treats as a hard gate. The orchestration
  foundation is the next Opus target and is **not** yet done — so 1B stays queued, not
  overridden.

## Verification

- `python3.10 -m pytest tests/unit/services/test_btd6_round_cash.py tests/unit/services/test_btd6_data_service.py` → 53 passed.
- `python3.10 scripts/check_quality.py --full` → black/isort/ruff/check_docs clean, mypy
  clean, **8263 passed, 16 skipped**. (Black initially wanted the long list-comprehension
  wrapped; applied `python3.10 -m black` — the PostToolUse auto-format hook did **not**
  fire in this web container, so I formatted by hand, as the journal warns.)
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors (only pre-existing
  WARN-tier `[known]` items; the new function adds no imports/layer crossings).
- Live REPL demo on the real dataset: "r50→r60" = `range_cash` 19840.0, and
  `cumulative_at_end (55134.0) − cumulative_before_start (35294.0) == 19840.0` — the
  published identity holds. Out-of-range and partial-overlap return structured refusals.
  (No bot boot: `round_cash` is wired to nothing yet, so a boot exercises nothing the
  deterministic tests don't; the full suite already imports the module.)

## Context delta

- **Needed but not pointed to:** the `cash_source` metadata string *inside*
  `disbot/data/btd6/rounds.json` documents the exact economy basis (Medium $650 start, no
  income towers, v55 decay) — it, not a folio, is the source of truth for the assumptions
  text. Also: the inclusive-vs-exclusive "from A to B" ambiguity is decided only in the
  roadmap's §5.7/§9, not in any binding doc.
- **Pointed to but didn't need:** the context-map "recommended read set" routed me to four
  cog importers — irrelevant for a purely additive function (no call site changed). For an
  *additive* service function the importer list is noise; it matters only for renames/moves.
- **Discovered by hand:** the cumulative-cash baseline ($650 Medium start) lives as a bare
  `_STARTING_CASH = 650` constant in the *test* file, not the service. I added the canonical
  `_MEDIUM_STARTING_CASH` to the service (the data owner) so the running-total baseline has
  a home next to the query that uses it; the test keeps its independent recompute by design.
- **Unresolved for next session:** reconcile this PR's # into the roadmap + current-state
  "Recently shipped"; Phase 1B remains blocked on the orchestration foundation (AR-10) — do
  not add the `btd6_round_cash` AI tool until that lands.
