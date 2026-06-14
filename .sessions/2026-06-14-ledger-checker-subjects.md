# 2026-06-14 — ledger-checker prints missing-PR merge subjects (band-#840 queue slot 9)

> **Status:** `complete` — PR **#864**; born-red card flipped as the deliberate final step
> (Q-0133) once code + tests + close-out docs were all in.

**About to do:** the band-#840 reconciliation queue's **slot 9** (turn-key tooling) — make
`scripts/check_current_state_ledger.py` print each missing PR's **merge-commit subject** beside
its number, collapsing the manual `git log --grep "#N"` loop every Q-0107 reconciliation pass
runs by hand. Then assess capacity for a second bounded slice. Autonomous status-check fire; no
explicit task → standing handoff (current-state ▶ Next action → band-#840 queue §4).

## What shipped

Two paired slices hardening the **ledger drift guard** (`scripts/check_current_state_ledger.py`),
the checker the autonomous loop relies on to catch `current-state.md` drift between reconciliation
passes — both grooming-lane ideas the band-#840 queue had already routed, executed together
because they touch the same file and the same concern.

1. **Slot 9 — print missing-PR merge subjects** ([idea](../docs/ideas/ledger-checker-print-pr-subjects-2026-06-14.md)).
   Refactored `_git_merged_pr_numbers` to derive from a new ordered
   `_git_merged_pr_map(limit) -> {pr: merge-subject}` (no new `git` call — the subject was already
   in hand at extraction and discarded). `main()` now prints `  - #N  <subject>` for each missing
   PR, degrading to `(no merge commit found — closed/unmerged?)` for an unmapped number. Collapses
   the manual `git log --grep "#N"` loop every Q-0107 reconciliation pass runs by hand.
2. **Range-scope structural fix** ([idea](../docs/ideas/ledger-checker-range-scope-2026-06-13.md)).
   New `known_ledger_numbers` partitions `current-state.md` at `## Recently shipped` and expands
   `#AAA–#BBB` ranges **only** in that tail (+ the whole archive); individual `#N` refs still count
   everywhere. Closes the **band-#800 false-green** (a forward-looking planning range in the
   `▶ Next action` pointer used to mark a whole band "present" the instant it merged, hiding ~14
   PRs while the guard reported green). The convention mitigation (reference the pass by name, never
   an inline range) stays good practice but is **no longer load-bearing**.

- `tests/unit/scripts/test_check_current_state_ledger.py`: +5 tests (map newest-wins dedup +
  ordering; `main` prints subjects + degrades gracefully; range expands inside Recently-shipped /
  archive; a planning range above the header does **not** mask its interior).
- Marked both idea files + their README index entries `✅ implemented`.

## Verification

- `python3.10 scripts/check_quality.py --full` green — **9606 passed**, 37 skipped.
- `check_architecture --mode strict` — 0 new errors (only pre-existing `[known]` xp-view warnings).
- Dogfooded live: the guard correctly still flags **#862/#863** (real between-pass lag, not
  masked) and prints their merge subjects.

## 💡 Session idea (Q-0089)

**Distinguish benign newest-merge lag from real drift in the ledger guard** —
[`docs/ideas/ledger-guard-benign-lag-vs-drift-2026-06-14.md`](../docs/ideas/ledger-guard-benign-lag-vs-drift-2026-06-14.md).
Surfaced directly by dogfooding this session: `--strict` (run by `/session-close`) currently
fails on the *expected* newest-merge lag (#862/#863 this run) exactly as it would on real drift,
training an operator to ignore a red signal. The idea splits the guard's output into `lagging`
(newest ~2, or newer than the `Last reconciliation pass: #M` marker — informational) vs `drift`
(older, never recorded — actionable), gating `--strict` on drift only. Genuine, new, believed-in,
and a direct extension of this session's work; dedup-grepped `docs/ideas/` first (no lag/staleness
idea existed).

## ⟲ Previous-session review (Q-0102) — #855 (P1-1 Layer A, BTD6 path/line resolution)

- **Did well:** exemplary discipline on the "run, don't assume" rule — it *re-verified*
  `resolve_upgrade("bomb shooter middle path") → none` live before building, rather than trusting
  the design doc's months-old diagnosis, and scoped tightly to the deterministic, non-creds-gated
  half (Layer A) while honestly flagging the unverified live end-to-end for the maintainer. Its
  context-delta reflection (the design doc isn't on the standard orientation route) produced a
  concrete fix in the same session. A clean model of a bounded slice.
- **Could've done better / system note:** it noticed mid-session that "Pass 3d already cites this
  design doc §4.1 as Layer A / mechanism 2" — i.e. *half of Layer A had already shipped earlier and
  the design doc's status banner never said so*. It fixed the banner but the underlying gap is
  systemic: a **design/plan doc's status banner can silently drift from what's actually shipped**,
  and nothing checks it. **Improvement:** the same `check_docs`-family guard that flags stale docs
  could grow a lightweight check that a design/plan doc claiming a "design-for-review" or "future"
  status for a mechanism isn't contradicted by a `Pass 3X`/symbol that already implements it — or,
  cheaper, a convention that shipping a plan's mechanism updates that plan's status line in the same
  PR (the mirror of this repo's strong ledger discipline, applied to plan docs). Worth a router note
  if it recurs; not pressing enough to gate on yet.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | pending (1 expected, on green via auto-merge once the card flips) |
| Tasks | 2 bounded slices (band-#840 queue slot 9 + the paired range-scope structural fix) |
| Tests added | +5 (ledger guard) |
| CI | `check_quality --full` green (9606 passed); arch 0 new errors |
| New ideas contributed | 1 (Q-0089 — benign-lag vs drift) |
| Ideas groomed/closed | 2 marked `✅ implemented` (print-subjects, range-scope) |
| Repo-rule trips | 0 |
