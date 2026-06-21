# 2026-06-21 — CI-reliability batch: BUG-0020 + BUG-0021 + BUG-0022

> **Status:** `complete` — tooling/test/docs only (no `disbot/` runtime changed) → self-merge on
> green (Q-0113).

> **Run type:** routine · dispatch

## What I did

Scheduled dispatch, no work order → advanced the plan **bugs-first**. Started on the one OPEN
tooling bug (BUG-0020); shipping it surfaced two more CI-reliability bugs (a flaky test, then a
test that clobbers a tracked file), each root-caused and fixed with a stays-fixed guard in the
same PR. All three are test/tooling hygiene — no runtime code touched.

### Slice 1 — BUG-0020: trim floor-pointer prose contamination (root)
`scripts/trim_recently_shipped.py`'s floor-pointer recompute scanned the **whole** archive for `#N`
and took min/max over all matches, picking up stray prose refs (a `band-#1170` note, `#1` rank
notation) → wrong `Older merges (#HIGH … #LOW)` span (it wrote `#1170 … #1` for a true `#1129 …
#535` on its first real use).
- **Fix:** new `_archive_span_numbers()` reads **only archived bullet headers**, taking each
  bullet's leading `#A · #B …` cluster (before the first ` (` or `**`). Grouped non-monotonic bands
  (`#690 · #721`) still contribute their newest member; prose `#N` no longer counts.
- **Guard:** `test_floor_pointer_ignores_stray_pr_refs_in_prose`.

### Slice 1b — ruff-pin drift (Q-0166 fix-on-sight)
Dependabot's `chore(deps-dev)` bump raised **only** `requirements-dev.txt` to `ruff==0.15.18`, leaving
`code-quality.yml` + `.pre-commit-config.yaml` at `0.15.14` — the "bump all three together" drift
CLAUDE.md warns about. 0.15.18 raised a false ERA001 on a genuine prose comment in `botsite/app.py`
that CI's actual 0.15.14 does not. Realigned the dev pin to `0.15.14`.

### Slice 2 — BUG-0021: flaky `acquire_lock_or_exit` wait-timeout test (root)
`test_acquire_lock_or_exit_exits_zero_after_wait_timeout` drove the lock loop against the **real**
`time.monotonic` with a 0.05 s budget (sleep mocked instant) and asserted `await_count >= 2`. Under
parallel-xdist CPU starvation the budget could elapse after one attempt → intermittent red.
- **Fix:** fake the clock — it only advances when the mocked `asyncio.sleep` runs; one sleep jumps
  past the budget, so the loop gives up on exactly attempt 2 (`await_count == 2`). No runtime code
  changed. Verified 5× + full file green.

### Slice 3 — BUG-0022: full suite clobbers tracked `botsite/site/data.js` (root)
Diagnosing why CI reddened on `data.js` stale-vs-`site.json`: `scripts/export_dashboard_data.py
main()` wrote the SPA data layer to a **hardcoded** real path, ignoring its output args, stamped with
the live `git rev-parse --short HEAD`. The CLI tests drive `main()` with `tmp_path` for
dashboard/site.json but data.js still hit the **tracked** repo file → every full-suite run rewrote it
with the session sha → `git add -A` swept it into the commit, desynced from the committed site.json →
red botsite-tests. This is what corrupted my own first push (`data.js` build = my born-red sha).
- **Fix (root):** `main()` takes `--data-js-output` (default = real path, so the reconciliation
  routine's regen is unchanged); the two CLI tests redirect it to tmp.
- **Guard:** `test_cli_does_not_clobber_tracked_data_js_when_redirected` snapshots the real
  `DATA_JS_OUTPUT_FILE`, runs `main()` redirected, asserts the tracked file is byte-identical after.
- Restored the accidentally-committed `botsite/site/data.js` to `origin/main`'s version.

## What shipped
- `scripts/trim_recently_shipped.py` + `tests/unit/scripts/test_trim_recently_shipped.py` (BUG-0020).
- `requirements-dev.txt` — ruff `0.15.18` → `0.15.14` (drift realign).
- `tests/unit/services/test_runtime.py` — deterministic clock fake (BUG-0021).
- `scripts/export_dashboard_data.py` + `tests/unit/scripts/test_export_dashboard_data.py` (BUG-0022).
- `botsite/site/data.js` — restored to main (revert accidental inclusion).
- `docs/health/bug-book.md` — BUG-0020/0021/0022 all FIXED.

## Verification
- BUG-0020: `pytest test_trim_recently_shipped.py` → 10 passed (incl. new guard).
- BUG-0021: target test 5× green + full `test_runtime.py` (21) green.
- BUG-0022: `pytest test_export_dashboard_data.py` → 31 passed; real `data.js` md5 unchanged before/after.
- `check_quality.py --check-only` green (ruff 0.15.14); `check_docs.py --strict`,
  `check_current_state_ledger.py --strict` green.

## Handoff
Three CI-reliability bugs closed at the root. The substantial ungated lanes in current-state ▶ Next
action still stand for the next dispatch: **creature-game v1 runtime cog**, **botsite React-SPA
migration**, the `public-data-contract-field-snapshot` guard, or a `needs-hermes-review` lane
(consistency-linter AI-nav PR 1 · procedures→skills Batch 2).

## ⚑ Self-initiated
None — all three were bugs-first (BUG-0020 from the OPEN queue; BUG-0021/BUG-0022 root-caused while
shipping it). The ruff realign is fix-on-sight drift (Q-0166). No invented feature.

## 💡 Session idea
**A `scripts/check_tool_pin_parity.py` (stdlib) wired into `code-quality.yml`** that parses the
black/isort/ruff/mypy versions from `code-quality.yml`, `requirements-dev.txt`, and
`.pre-commit-config.yaml` and fails unless all three agree. This run's ruff drift is the second
"pinned-in-three-places drifted" incident; the rule is currently prose-only. Such a guard would
red-flag an incomplete Dependabot bump at PR time instead of leaking a false-positive lint into a
dispatch session. Captured for grooming.

## ⟲ Previous-session review
The previous session (world-registry parity invariant, #1156 follow-up) was clean and correctly
declined the gated heavy lanes — good judgment. What it (and several prior sessions) missed is
systemic, not local: **BUG-0022 means any session that ran `check_quality.py --full` and then
`git add -A` could silently ship a corrupted `data.js`** — a latent trap that had been live since the
botsite data layer landed. None of the recent botsite-touching sessions caught it because the
symptom only appears when the regenerated file is *committed*. System improvement it surfaces (now
acted on): tests must never write tracked files — the `--data-js-output` redirect is the fix, and the
broader lesson is the **tool-pin parity guard** idea above plus a possible "no test writes a tracked
path" sweep as a future check.

## 📤 Run report
- **Run type:** routine · dispatch
- **What shipped:** BUG-0020 (trim floor-pointer prose) + BUG-0021 (flaky lock-wait test) + BUG-0022
  (suite clobbers tracked data.js) — all root fixes with stays-fixed guards; ruff dev-pin drift realign.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none
- **⚑ Self-initiated:** none
