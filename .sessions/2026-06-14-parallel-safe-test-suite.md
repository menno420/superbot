# 2026-06-14 — CI efficiency arc: cost reduction (#814) + parallel-safe test suite (#815)

> **Status:** `complete`

**PRs (both merged):** **#814** (concurrency-cancel + pip/mypy caching + the Q-0126
duplicate-work convention; xdist tried & reverted) · **#815** (made the suite parallel-safe,
re-enabled `pytest -n auto` — the ~3× CI speedup #814 had to defer).
**Branch:** `claude/trusting-goldberg-po4p7s`. Both auto-merged on green (Q-0123).

## Context

Owner observed (June Actions metrics) that `code-quality.yml` dwarfs every other workflow —
940 runs / 2,396 min/month — and asked to make it cheaper *and* stop parallel agents
duplicating work. #814 shipped the safe wins; the big lever (parallelize the 9.4k-test suite,
~109s→~35s) was reverted there because CI proved the suite wasn't parallel-safe. This session
(continuation) root-fixed that and turned it back on.

## What shipped

**#814 (earlier this session):**
- `concurrency:` cancel-in-progress on `code-quality.yml` (the biggest lever on the *run count*) +
  `pip` + `.mypy_cache` caching (per-run minutes). xdist was tried — reverted: non-deterministic
  parallel failures. Evidence + plan parked in `docs/ideas/ci-cost-and-duplicate-work-prevention-2026-06-14.md`.
- **Q-0126** (owner via AskUserQuestion): claim ledger (`docs/owner/active-work.md`) + push-batching,
  added to CLAUDE.md § Session & plan workflow.

**#815 (this turn — "continue from where you left off"):**
1. **Diagnosed** the parallel non-determinism: reproduced reliably under `pytest --dist loadscope`
   (default `load` was green locally — the trap). A *different* subset failed each run.
2. **Root cause — three process-global singletons** leaked across tests, colliding only under
   parallel scheduling: `core.runtime.lifecycle` phase (access-check cluster), `feature_flags._REGISTRY`
   defaults (`test_platform_flags_embed`), and a leaked `server_logging` bus subscription
   (`test_event_bus_delivery` — its `_reset_for_tests()` deliberately never unsubscribed).
3. **Fix:** one autouse fixture in `tests/conftest.py` resets lifecycle + startup_outcome +
   feature_flags (registry **snapshot/restore**, not wipe) per test; `server_logging._reset_for_tests()`
   now tears down its bus subscription + drops the `_SUBSCRIBED` latch. Each module already shipped a
   reset hook — `startup_outcome`'s docstring literally asks for an autouse fixture — they were just
   never wired suite-wide.
4. **Re-enabled** `-n auto` in `code-quality.yml` + `scripts/check_quality.py`; pinned
   `pytest-xdist==3.6.1`. Idea doc Follow-up marked DONE.

## Verification

- **8 parallel runs, all `9422 passed, 0 failed`** (5× `--dist loadscope` + 3× `-n auto`), ~34–38s
  vs ~109s serial. `check_quality --full` green (incl. pytest via the new `-n auto` mirror, 34.43s);
  `check_architecture --mode strict` 0 errors.
- The honest caveat the idea doc documents: green locally ≠ proof; the real test was CI across runs.
  #815's CI went green and auto-merged hands-off (~2 min) — and *that* run exercised `-n auto`.

## Context delta (reflection)

- **What worked:** treated the #814 idea doc as the spec — it had the exact evidence table + plan, so
  this turn was execution, not re-discovery. The `--dist loadscope` tip (from #814's evidence) was the
  unlock: it turns a flaky bug into a deterministic repro.
- **Decisions made alone:** snapshot/restore the feature-flag registry rather than call its
  `_reset_for_tests()` (which wipes to empty and would drop import-time defaults) — the non-obvious
  correctness call. Fixed the bus leak at its *source* (`server_logging`) rather than wiping the global
  bus in conftest, to avoid the `_SUBSCRIBED`-latch desync.
- **Weak point of what shipped:** the conftest autouse fixture now runs for all 9,422 tests; it's
  cheap (trivial resets) but it *is* suite-wide coupling. And the fix addresses the 3 *observed* leak
  sources — a future test adding new global-state pollution would reintroduce flakiness (see the idea).
- **One change that would have helped most:** a central isolation registry (the idea below) — I found
  a dozen+ `_reset_for_tests` hooks wired ad-hoc in individual test files; the gap was precisely that
  none of the three I needed were wired *globally*.

## 💡 Session idea (Q-0089)

**A central test-isolation registry so every process-global module's reset hook is auto-applied.**
This session's whole bug class was "module ships a `_reset_for_tests()` but it's only wired in *some*
test files' fixtures, so it leaks elsewhere." The codebase already has 12+ such hooks
(`lifecycle`, `startup_outcome`, `feature_flags`, `subsystem_schema`, `user_config`, `scope_locks`,
`server_logging`, the schema modules, `guild_config`, `_log_buffer`, …). Idea: a `tests/_isolation.py`
listing `(import_path, reset_callable)` for each, and **one** conftest autouse fixture that iterates it
— new global-state modules add one line instead of hoping every reader's fixture remembers them. Bonus:
a lint that flags a `def _reset_for_tests` not present in the registry. This generalizes the #815 fix
into a guardrail so the suite *stays* parallel-safe. Genuinely new (distinct from the point-fix shipped);
test-infra only, so it's a free-rein lane, but sizeable enough to groom into a small plan first.

## ⟲ Previous-session review (Q-0102) — the #814 turn (same session, earlier)

- **Did well:** shipped the safe CI wins (concurrency-cancel is the single biggest lever on the 940
  run-count) and — crucially — **reverted xdist the moment CI showed it was flaky** rather than shipping
  known-bad parallelism. And it documented the failure evidence + a turn-key plan in the idea doc, which
  is *exactly* why this turn could execute cleanly. That hand-off discipline is the system working.
- **Missed / could've done better:** #814 *initially shipped* `-n auto` before proving parallel-safety
  across multiple runs — it took a real CI failure to catch it (cost a revert). The lesson it learned
  ("verify across many runs, `--dist loadscope` reproduces locally") is the one this turn applied up
  front. Also: the #814 turn left **no `.sessions/` log** — the evidence lived only in the idea doc;
  this log backfills it.
- **System improvement it surfaces:** the parallel-safety regression risk is permanent now that `-n
  auto` is on. Beyond the idea above, the cheapest guard is a **periodic (nightly/weekly) routine** that
  runs the suite under `--dist loadscope` a few times — it deterministically catches new isolation leaks
  that `-n auto` would only surface as intermittent CI flakes (the hardest kind to debug). Worth a router
  round vs. the per-PR cost.
