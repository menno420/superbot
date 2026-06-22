# 2026-06-22 — `band_pr_status --themes`: draft grouped-entry skeleton

> **Status:** `in-progress` — born-red HOLD. Dispatch routine slice 2 (same run as the Starboard PR 2
> #1270). Building the band-#1260 pass's filed Q-0089 idea
> ([band-pr-status-author-classifier](../ideas/band-pr-status-author-classifier-2026-06-21.md)). Flip
> to `complete` as the final step.

> **Run type:** `routine · dispatch`

## What I'm about to do

Every Q-0107 reconciliation pass hand-themes the band's merged PRs into grouped Recently-shipped
entries — the expensive half is reverse-engineering what the **opaque merge-commit PRs**
(`Merge pull request #N from menno420/claude/funny-franklin-…`) actually shipped, by running
`git show --stat` per PR. `scripts/band_pr_status.py` (#1181) already classifies merged/closed/open but
not **theme**.

This adds a `--themes` mode: for each merged PR in the band, read the commit's touched files
(`git diff --name-only <sha>^..<sha>`, first-parent — works for both merge and squash commits), bucket
each PR by its dominant top-level path area (`disbot/cogs/`, `disbot/services/`, `docs/planning/`,
`dashboard/`, …), and emit a **draft grouped-entry skeleton** the pass edits instead of reconstructing
cold. Stdlib, read-only, disposable (Q-0105) — same detector→actuator shape as the trim actuator.

## Files (planned)

- `scripts/band_pr_status.py` — `--themes` flag + pure grouping core (area-for-files, group-by-theme,
  render-skeleton) + thin `git diff` wrapper
- `tests/unit/scripts/test_band_pr_status.py` — pure-core tests for the theming (mirrors the existing
  classifier tests if present)
