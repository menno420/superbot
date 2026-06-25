# 2026-06-25 — BTD6 grounding eval: fixture-drift anchor guard (S2 P1-1)

> **Status:** `in-progress`

## Goal (dispatch run, empty scheduled fire → advance the next plan slice)

Empty scheduled fire, no open PRs. Per the routine: advance the next **▶ startable**
plan slice. Picked **S2 P1-1 BTD6 eval cases** — "offline test assertions over
already-grounded facts → offline-verifiable + self-mergeable" (roadmap S2 dispatch
note). The existing grounding-anchor guard
(`tests/evals/test_btd6_grounding_anchors.py`) pins every *`llm_judge`-rubric*
number to a deterministic `btd6_data_service` re-derivation — but the BTD6
**grounding** cases that use `contains(...)` graders bake their truth into the
`tool_results` **fixture**, not a rubric, so those numbers have **no data-drift
guard** at all. A re-seed that changes Navarch's income or a paragon cost would
leave the eval silently testing against a stale fixture.

## What I'm about to do

**Slice 1 — fixture-drift anchor guard (offline tests, no runtime change).**
Extend `test_btd6_grounding_anchors.py` with a `FixtureAnchor` table that pins each
number baked into a grounding case's `tool_results` facts to its deterministic
re-derivation, closing two directions for the `contains`-grader cases:
1. **data drift** — the fixture number must come back from `btd6_stats_service`
   (Navarch income `$3,200`, Navarch/Buccaneer paragon cost `$550,000`);
2. **fixture drift** — that number must actually appear in the named case's
   `tool_results` facts (so editing the fixture away from the grounded truth fails).
Plus a guard-the-guard test. No `disbot/` runtime touched.

## Status checklist
- [ ] Slice 1 — fixture-drift anchor guard + tests green
- [ ] CI mirror green (`check_quality.py --full`) + arch strict 0 errors
- [ ] De-stale S2 sector doc
- [ ] Session enders (idea / prev-review / doc audit / run-report footer)
