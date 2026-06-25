# 2026-06-25 — BTD6 grounding eval: fixture-drift anchor guard (S2 P1-1)

> **Status:** `complete`

## Goal (dispatch run, empty scheduled fire → advance the next plan slice)

Empty scheduled fire, no open PRs. Per the routine: advance the next **▶ startable**
plan slice. Picked **S2 P1-1 BTD6 eval cases** — "offline test assertions over
already-grounded facts → offline-verifiable + self-mergeable" (roadmap S2 dispatch
note). The existing grounding-anchor guard
(`tests/evals/test_btd6_grounding_anchors.py`) pins every *`llm_judge`-rubric*
number to a deterministic `btd6_data_service` re-derivation — but the BTD6
**grounding** cases that use `contains(...)` graders bake their truth into the
`tool_results` **fixture**, not a rubric, so those numbers had **no data-drift
guard** at all. A re-seed that changed Navarch's income or a paragon cost would
leave the eval silently testing against a stale fixture.

## What shipped (PR #1458)

**Slice 1 — fixture-drift anchor guard (offline tests, no runtime change).**
- New `FixtureAnchor` table in `test_btd6_grounding_anchors.py` pinning each number
  baked into a grounding case's `tool_results` facts to its deterministic
  re-derivation from `btd6_stats_service`:
  - Navarch income `$3,200` (`get_paragon_stats("navarch_of_the_seas").income_per_round`)
    — in both `grounding.btd6_navarch_income` and `grounding.btd6_carryover_followup`;
  - Navarch/Buccaneer paragon cost `$550,000` (`.cost`) — in the navarch case.
- Two test directions mirror the rubric anchors:
  1. **data drift** — the fixture number must come back from the dataset;
  2. **fixture drift** — that number must still appear in the named case's fixture
     (editing the fixture away from the grounded truth fails).
  Plus a stale-anchor guard and a guard-the-guard (`_fixture_numbers` actually
  reads a known number).
- **Curation principle documented** in the module docstring + an S2-sector handoff:
  I empirically checked the *remaining* unanchored rubric figures (cumulative
  range-cash, ABR boundaries) and they are **not** cleanly reproducible — a naive
  `round_cash(1, N)` lands ~$10 off the rubric totals (a starting-cash/boundary
  convention), and `$71,315.20` is a *distractor* BUG-0004 tells the judge to
  reject. Anchoring those blindly would assert a wrong "truth" and make the guard
  lie (CLAUDE.md Q-0120). So they stay deliberately unanchored, with a note + a
  ▶ Next-startable handoff for a future slice that nails the convention first.
- **Drift cleanup (bugs-first):** removed a stale claim file
  (`docs/owner/claims/claude-funny-franklin-ry0ygk.md`) for the settle-once CI
  guard that already merged as #1454 (zero open PRs confirms its session closed).

## Verification
- `tests/evals/test_btd6_grounding_anchors.py`: **34 passed** (the new fixture
  anchors + the existing rubric anchors).
- Full CI mirror `python3.10 scripts/check_quality.py --full`: **12511 passed,
  48 skipped, 2 xfailed** (green).
- `check_architecture.py --mode strict`: **0 errors** (49 known warnings; test-only
  change touches no `disbot/`).
- Doc audit: `check_current_state_ledger.py --strict` exit 0 (benign newest-merge
  lag only); `check_docs.py --strict` green.

## Status checklist
- [x] Slice 1 — fixture-drift anchor guard + tests green
- [x] CI mirror green + arch strict 0 errors
- [x] De-stale S2 sector doc + stale-claim cleanup
- [x] Session enders (idea / prev-review / doc audit / run-report footer)

## 💡 Session idea (Q-0089)

**Eval-anchor coverage report** — a small advisory script/test that inventories
every numeric token asserted across `tests/evals/cases.py` (both `llm_judge`
rubrics and `tool_results` fixtures) and reports which are **not** covered by an
`Anchor`/`FixtureAnchor`. Today the coverage gap is buried in a prose comment
(the range-cash convention figures); a measurable, advisory coverage readout would
make "which asserted truths still have no drift guard?" answerable at a glance and
turn the curation backlog into a visible, groomable list — the same observability
win the bug-book root-fix-backlog checker gives. Genuinely useful (I hand-built
exactly this inventory this run to decide what was safely anchorable); worth having
because eval drift-guards silently *under*-covering is the failure mode they exist
to prevent. Dedup-checked `docs/ideas/` — no existing eval-coverage idea.

## ⟲ Previous-session review (Q-0102)

Prev = `2026-06-24-syncslash-gated-unification.md` (PR #1426, route `!syncslash
global` through the diff-gated auto-sync helper). **Did well:** noticed the
`admin_cog.py` was at ~787 LOC and would breach the 800-LOC `test_cog_size`
invariant if the new logic were inlined, and proactively extracted to
`cogs/admin/_slash_sync.py` — fixing the constraint at the root rather than
bumping the ceiling. Clean, exactly the "bugs-first / root-cause" instinct.
**System improvement it surfaces:** the cog-size ceiling is only enforced by a
*test* that fires at edit time — an author only learns they're near the 800 limit
after writing the code. A cheap `pre-edit-check` readout ("this cog is at 787/800
LOC — budget 13 lines") when a `cogs/*_cog.py` file is opened would surface the
constraint *before* the work, not after. Small, advisory, in the spirit of the
existing pre-edit tooling.

## 📤 Run report

- **Did:** empty scheduled fire → advanced S2 P1-1 with a fixture-drift anchor guard for the BTD6 grounding eval cases (closes a real, previously-uncovered drift class) · **Outcome:** shipped
- **Shipped:** #1458 — `FixtureAnchor` table pinning Navarch income/cost fixtures to `btd6_stats_service` re-derivations; offline test-only; CI green
- **Run type:** `routine · dispatch` (Q-0165)
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** `none` (advanced an existing plan slice, S2 P1-1; no new idea promoted to plan/build)
- **↪ Next:** S2 P1-1 — anchor the remaining range-cash convention figures *after* nailing the exact cumulative/starting-cash convention (a naive `round_cash(1, N)` is ~$10 off — see the curation note in `test_btd6_grounding_anchors.py`); live `llm_judge` battery + absence-guard Layer B stay creds-gated.
