# 2026-06-23 — Fishing test helpers: kill the duplicated roll_catch mock (slice 3)

> **Status:** `in-progress` — born-red card (Q-0133); flips to `complete` as the final step.
> Routine · dispatch (empty-fire schedule, **slice 3** — after #1340 + #1341 merged). A
> twice-confirmed test-infra friction fix (workflow improvement = first-class). Auto-merges on green.

## Arc

Slices 1 (#1340 deepwater venue) and 2 (#1341 weather forecast) both hit the **same friction**: the
`services.fishing_workflow.roll_catch` mock signature is hand-duplicated **~17 times** across
`test_fishing_workflow.py` + `test_fishing_workflow_bait.py`, so each signature change (slice 1 added
`venue=`, slice 2 added the `current_weather` ambient) meant editing every site by hand — and my first
scripted insert even broke single-line `with` blocks. Both slice reviews flagged the fix; it's now
genuinely earned, so slice 3 lands it.

## Plan (this PR)

- **`tests/unit/services/_fishing_helpers.py`** (new) — the canonical-signature stubs in ONE place:
  `CATCH` sentinel, `fake_roll_catch(catch)` (non-recording), `recording_roll_catch(record)` (captures
  `{level, rarity_pull, venue}` of the call). A future `roll_catch` signature change is now a **single**
  edit, not 17.
- Refactor both fishing service test files to import + use them; update the handful of recording
  assertions to read the shared `record` dict.
- Pure test refactor — **no production code changes**; the full suite is the proof it's behaviour-
  preserving.
