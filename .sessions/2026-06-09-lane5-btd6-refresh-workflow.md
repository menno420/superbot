# Lane 5 — BTD6 data-refresh workflow (manual-dispatch only) — 2026-06-09

> Agent 3 of a 4-agent parallel run on the multi-lane execution plan (Lanes 2/3/5/6
> in flight simultaneously). This session: **Lane 5 only.** PR: **#633** (draft at
> first push per Q-0052, marked ready at session end).

## Summary

Committed `.github/workflows/btd6-data-refresh.yml` — the Q-0049-approved BTD6
data-refresh workflow. `workflow_dispatch` is the **only** trigger (no schedule/cron;
the header comment marks adding one as needing a new owner ask). It clones the
`Btd6ModHelper/btd6-game-data` dump into `/tmp` (~320 MB, never committed) and runs
the existing tested chain from `docs/btd6/btd6-data-refresh-pipeline-plan.md`:
validate-anchors (hard gate) → overlay (name-frozen) → audit (piped to the run
Summary page, `pipefail` so a crash fails the step) → coverage-map regen → opt-in
default-false `regenerate_decode_inventory` input (plan decision 3, per its own
recommendation). Output is a reviewable PR on `auto/btd6-data-refresh` via
`peter-evans/create-pull-request` SHA-pinned at v8.1.1 (the repo's workflows avoid
unpinned third-party actions — `code-quality.yml` says so explicitly); minimal
`permissions:`; `concurrency` queue. Empty diff → no PR (the normal between-patches
outcome).

**Root-cause fix shipped in the same PR:** live-running the chain showed
`btd6_decode_inventory_report.py` doesn't emit the `Status:` badge that
`check_docs.py --strict` requires on every `docs/**/*.md` — the badge had been
hand-added to the committed artifact only, silently breaking the script's
byte-for-byte regeneration claim. Any regeneration (workflow opt-in step or the plan
doc's manual chain) would have stripped it and reddened the refresh PR's doc-hygiene
gate. Fixed at the generator (`_HEADER_LINES` module constant), pinned by two new
tests (header ↔ committed artifact prefix; badge validity). Also fixed the plan
doc's manual chain, which invoked the decode report without its **required**
`--dump` flag or redirect target.

## Verification

- actionlint 1.7.12 (downloaded to /tmp): **0 findings**. PyYAML parse: trigger list
  is exactly `['workflow_dispatch']`.
- Real-clone end-to-end run (dump `4e22e58`, game v55.1): anchors OK · overlay
  **0-change no-op** · audit **0 SUSPECT** (the one grep hit is the legend line) ·
  coverage map **byte-identical** · decode report regenerates badge-intact. The
  committed decode doc still pins v55.0 `a3348a8` — the dump moved upstream, so the
  maintainer's first dispatch with the opt-in input will produce a real PR.
- CI mirror `check_quality.py --full`: **8404 passed, 22 skipped**; arch strict 0
  errors; `check_docs.py --strict` green after doc edits.

## Files changed

- `.github/workflows/btd6-data-refresh.yml` — new (the deliverable).
- `scripts/btd6_decode_inventory_report.py` + its test file — badge root-cause fix.
- `docs/btd6/btd6-data-refresh-pipeline-plan.md` — header → committed (#633); sketch
  marked historical (the file wins); decisions 2+3 resolved; manual-chain `--dump` fix.
- `docs/planning/multi-lane-execution-plan-2026-06-09.md` — Lane 5 ticked, #633.
- `docs/roadmap.md` — BTD6 section bullet only (left the shared at-a-glance "Next"
  row alone: 4 agents would collide there; next consolidation prunes it).
- `docs/current-state.md` — **deliberately untouched**: it names merged PRs only and
  "deliberately names no open PRs"; #633 is open. The scoreboard carries live state.

## Parallel-agent notes

- Verified zero open PRs at session start — no competing Lane 5 PR.
- Stayed off Lanes 2/3/6 files entirely. Shared files touched: scoreboard (own lane
  block only) and roadmap (BTD6 section only). Conflicts, if any, are UNION-resolvable.
- Skipped the standing end-of-session idea-grooming pass (Q-0015): four agents
  grooming `docs/ideas/` concurrently is a collision generator, and the session brief
  scopes this agent to Lane 5 only. Next solo session resumes grooming.

## Context delta

- **Needed but not pointed to:** `scripts/check_docs.py`'s badge rule ("every
  `docs/**/*.md`, first 12 lines") — the reading route covered the BTD6 chain but not
  the doc-hygiene gate the workflow's *output* must pass. Any future lane whose CI
  job writes/regenerates a `docs/` file needs this in its read set. Also
  `ai-evals.yml` as the repo's manual-dispatch + step-summary style precedent —
  worth naming in any future workflow-lane brief.
- **Pointed to but didn't need:** `scripts/parse_gamedata.py` internals beyond its
  argparse block (the lane only chains the CLI; the ~2700 lines above `main()` were
  irrelevant). `btd6_gamedata_inventory.py` likewise — argparse + output path
  sufficed.
- **Discovered by hand:** (1) the generator↔artifact badge drift class — a generated
  doc that gets hand-edited breaks regeneration *silently* until something
  regenerates it; the new prefix-pinning test is the reusable pattern. (2) The
  committed decode doc lags the dump (v55.0 vs v55.1 live) — surfaced here so the
  first real dispatch isn't a surprise PR. (3) `create-pull-request` v8's only
  breaking change is the Node-24 runner floor (GitHub-hosted is fine) — checked so
  the SHA pin isn't stale-on-arrival. (4) GitHub-token-opened PRs don't trigger CI —
  documented in the workflow header + the generated PR body (close/reopen to run it).
