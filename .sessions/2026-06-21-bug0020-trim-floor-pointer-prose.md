# 2026-06-21 — BUG-0020: trim_recently_shipped floor-pointer prose contamination (+ ruff-pin drift)

> **Status:** `complete` — tooling/docs only (no `disbot/` runtime) → self-merge on green (Q-0113).

> **Run type:** routine · dispatch

## What I did

Scheduled dispatch, no work order → advanced the next plan slice. Picked **bugs-first**: closed the
one OPEN tooling bug (BUG-0020) at the root with a regression test, and fixed a drift bug I spotted
along the way (the ruff pin).

### Slice 1 — BUG-0020 (root fix + guard)
`scripts/trim_recently_shipped.py`'s floor-pointer recompute scanned the **whole** archive for `#N`
and took min/max over all matches, so it picked up stray prose references (a `band-#1170`
parenthetical note, `#1` rank notation) and wrote a wrong `Older merges (#HIGH … #LOW)` span — caught
on the actuator's first real use (seventeenth Q-0107 pass wrote `#1170 … #1` for a true span of
`#1129 … #535`).
- **Fix:** new `_archive_span_numbers(archive_text)` reads **only archived bullet headers**
  (`^- \*\*#…`), taking each bullet's leading `#A · #B …` cluster (the run before the first ` (` date
  paren or `**` bold close). Grouped non-monotonic bands (`#690 · #721`) still contribute their newest
  member; free-floating `#N` in prose no longer counts. `_rewrite_floor` calls it instead of the
  whole-archive `_pr_numbers`. Module docstring de-staled ("whole archive" → "bullet headers").
- **Guard:** `tests/unit/scripts/test_trim_recently_shipped.py::test_floor_pointer_ignores_stray_pr_refs_in_prose`
  feeds an archive whose prose carries a stray high (`band-#9999`) + low (`#1`) `#N` and asserts the
  span ignores both. The existing non-monotonic-band test still passes (proves the cluster path keeps
  grouped members).
- Bug-book BUG-0020 → **FIXED**.

### Slice 1b — ruff-pin drift (spotted while running the CI mirror; Q-0166 fix-on-sight)
Running `check_quality.py` locally raised a false ERA001 in `botsite/app.py` (a file I didn't touch).
Root cause: Dependabot's `chore(deps-dev)` bump (#2b035a3d) raised **only** `requirements-dev.txt`
to `ruff==0.15.18`, leaving `code-quality.yml` + `.pre-commit-config.yaml` at `0.15.14` — the exact
"bump all three places together" drift CLAUDE.md warns about. 0.15.18 flags an ERA001 false positive
on a genuine prose comment that 0.15.14 (CI's actual version) does not. Realigned the dev pin back to
`0.15.14` (the value CI + pre-commit enforce) with an inline note. Adopting 0.15.18 would be a separate
deliberate three-place bump + suppressing that ERA001 FP — not done here.

## What shipped
- `scripts/trim_recently_shipped.py` — `_archive_span_numbers` helper + `_rewrite_floor` rewire + docstring.
- `tests/unit/scripts/test_trim_recently_shipped.py` — new prose-contamination regression test.
- `requirements-dev.txt` — ruff `0.15.18` → `0.15.14` (drift realign).
- `docs/health/bug-book.md` — BUG-0020 FIXED.

## Verification
- `python3.10 -m pytest tests/unit/scripts/test_trim_recently_shipped.py` → 10 passed.
- `python3.10 scripts/check_quality.py --full` → lint + mypy clean, 11036 passed (after pinning ruff
  to CI's 0.15.14). One pre-existing **flaky** failure under `-n auto` —
  `test_runtime.py::test_acquire_lock_or_exit_exits_zero_after_wait_timeout` — passes in isolation
  (real-`time.monotonic` 0.05s budget, CPU-starvation flake). Captured as **BUG-0021** (OPEN) for a
  deterministic fix; not caused by this change.
- No `disbot/` runtime touched → arch check trivially unaffected.

## Handoff
BUG-0020 is closed at the root. Next: **BUG-0021** (flaky `acquire_lock_or_exit` wait-timeout test) is
captured OPEN with a proposed deterministic fix (mock `time.monotonic`); a good small next slice. The
substantial ungated lanes in current-state ▶ Next action still stand: creature-game v1 runtime cog,
botsite React-SPA migration, the `public-data-contract-field-snapshot` guard.

## ⚑ Self-initiated
None — BUG-0020 was the OPEN bug-book queue (bugs-first), and the ruff-pin realign is fix-on-sight
drift (Q-0166). No invented feature.

## 💡 Session idea
**Dependabot dev-dep bumps that touch a tool pinned in 3 places should fail a CI guard unless all
three move together.** This run's ruff drift (`requirements-dev.txt` bumped alone) is the second
"pinned-in-three-places drifted" incident; a tiny `scripts/check_tool_pin_parity.py` (stdlib: parse
the black/isort/ruff/mypy versions from `code-quality.yml`, `requirements-dev.txt`,
`.pre-commit-config.yaml` and assert equality) wired into `code-quality.yml` would turn the prose rule
into an enforced one and red-flag an incomplete Dependabot bump at PR time. Worth having — captured for
grooming.

## ⟲ Previous-session review
The previous session (world-registry parity invariant, #1156 follow-up) was a clean, well-scoped
self-merge slice and correctly declined the heavier gated lanes (PR 2 migration, CLAUDE.md edits) with
explicit reasons — good judgment. One thing it could have done: while it was the *first* session after
the seventeenth reconciliation pass that surfaced BUG-0020, it left that OPEN tooling bug for a later
run; a bugs-first sweep of the freshly-written bug-book at session start would have caught a
same-shape, same-day fixable item. System improvement it surfaces: the **tool-pin parity guard** above
— had it existed, the ruff drift this run chased would never have reached a dispatch session.

## 📤 Run report
- **Run type:** routine · dispatch
- **What shipped:** BUG-0020 floor-pointer prose-contamination root fix + regression guard; ruff dev-pin
  drift realign (0.15.18 → 0.15.14); BUG-0021 captured.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none
- **⚑ Self-initiated:** none
