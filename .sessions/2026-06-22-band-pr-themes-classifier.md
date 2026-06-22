# 2026-06-22 — `band_pr_status --themes`: draft grouped-entry skeleton

> **Status:** `complete` — Dispatch routine slice 2 (same run as Starboard PR 2 #1270, now MERGED).
> Built the band-#1260 pass's filed Q-0089 idea
> ([band-pr-status-author-classifier](../ideas/band-pr-status-author-classifier-2026-06-21.md)).
> PR #1271, auto-merge armed on green. Self-initiated (Q-0172) — mechanizes the reconciliation routine.

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

## What shipped

- **`scripts/band_pr_status.py`** — a `--themes` mode: for each *merged* PR newer than the
  reconciliation marker, read the merge's first-parent diff (`git diff --name-only <sha>^..<sha>` —
  works for both merge and squash commits), bucket each PR by its **dominant signal area**
  (`disbot/cogs`, `disbot/services`, `docs/planning`, …) and emit a draft grouped-entry skeleton the
  pass edits. Pure core (`dominant_area` / `group_by_theme` / `render_theme_skeleton`) + thin git
  wrappers (`git_merged_pr_shas` / `pr_changed_files`); `--json` too. Git-only → works in the routine
  container with no `gh`/token. Live-verified against the band-#1230 and band-#1260 ranges.
- **`tests/unit/scripts/test_band_pr_status.py`** — 10 new pure-core cases (specificity tie-break,
  session-card/test/artifact de-weighting, noise-only fallback, newest-first grouping, render
  sample-cleaning, git-error → empty).

## Findings / decisions

- **De-weight noise, but never drop a PR.** Session cards (`.sessions/`), tests, and generated
  artifacts (`dashboard.json`, `site.json`, `data.js`, `active-work.md`) ride along on nearly every PR
  and don't describe its theme, so they're excluded from the area vote *and* the file sample — but a PR
  that touched *only* noise (an auto-refresh bot PR) still buckets to that area and shows its file, so
  no PR vanishes from the skeleton.
- **Ties break by specificity** (`AREA_PREFIXES` order) so a mixed code+docs PR themes as the code area
  — matching how the pass reads a fan-out by eye.
- **Scoped the formatter to changed files only** this slice — the explicit lesson from slice 1's
  `ruff --fix tests/` foot-gun (which mutated 339 unrelated files). No recurrence.

## 📤 Run report

- **Did:** `band_pr_status --themes` draft grouped-entry skeleton (the band-#1260 Q-0089 idea) ·
  **Outcome:** shipped (PR #1271, auto-merge armed on green)
- **Shipped:** #1271 — band_pr_status `--themes`
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none — disposable dev tooling (Q-0105), not CI-wired; merged = deployed
- **⚑ Self-initiated:** yes — promoted the band-#1260 pass's filed Q-0089 idea → build with no
  dispatch/owner ask (Q-0172). Stdlib, read-only, disposable; flagged for owner review.
- **↪ Next:** the reconciliation routine's STEP 2 (band theming) now has a one-command starting point;
  a future pass should confirm the skeleton lands intact a couple of times before leaning on it (Q-0105
  "unverified" note already on the script). Run-level enders (new idea / previous-session review / doc
  audit) for this dispatch run are in the slice-1 card (`2026-06-22-starboard-pr2-config-polish.md`) —
  this is the same session.

## 💡 Session idea (slice-2 increment)

**Wire `--themes` into the reconciliation routine's saved prompt (STEP 2).** The tool now exists but
nothing tells the pass to run it; a one-line addition to `docs/operations/autonomous-routines.md`'s
reconciliation procedure ("run `band_pr_status.py --themes` to draft §1's grouped entries") would close
the build→adopt gap — the same gap the trim actuator (#1181) had until it was wired into this routine.
(Deferred to the next reconciliation pass since editing that routine prompt is its lane, not a dispatch
slice; captured here so it isn't lost.)
