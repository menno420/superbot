# Idea — `band_pr_status.py --themes` should print each PR's subject line

> **Status:** `ideas` — captured 2026-07-01 (Q-0089, thirty-first reconciliation pass). Small,
> decided-lane repo-tooling refactor. Area: `scripts/band_pr_status.py` (the reconciliation
> band-authoring helper). Sector: S4 docs-system tooling.

## The gap (grounded in this pass)

`band_pr_status.py --themes` drafts a grouped-entry skeleton for the Recently-shipped ledger, but it
buckets PRs **by touched top-level directory** (`disbot/cogs`, `disbot/services`, `disbot/views`, …)
and labels each line `_theme?_` with a list of *touched files* — **never the PR's title/subject**.

Touched-dir buckets cross-cut the real themes badly. On the band-#1620 pass the fishing coral-structures
arc (#1596 · #1598 · #1603 · #1605) was split across the `disbot/views`, `disbot/utils`, and
`disbot/services` buckets, and the reaction-roles slim-builder arc was split too — because the branches
(`claude/funny-franklin-*`) are reused across unrelated themes, so neither dir- nor branch-grouping
recovers the theme. The only reliable signal is the **PR subject**, which the skeleton omits — so the
agent falls back to hand-grepping `git log --grep "#N"` merge-commit bodies for every PR to recover the
titles (exactly what this pass did). That hand-grep is the drift-prone, time-consuming core of the pass.

## The change

Add each PR's **subject line** to every skeleton line, e.g.

```
- #1603 — feat(fishing): fold Tide Pool + Dock into a 🏗 Structures sub-hub  [disbot/views]
```

Source the subject the same way `band_pr_status.py` already resolves merged-on-main PRs: the
squash-merge subject (`<title> (#N)`) or the `Merge pull request #N …` commit's body first line, from
the `git log` it already runs — no new dependency, still offline-capable. Optionally keep the touched-dir
tag as a secondary hint. With subjects in the skeleton, an agent regroups by *reading the printed
subjects* instead of re-fetching them one PR at a time.

## Why it's worth having

- Removes the single most repetitive manual step of every 30-PR reconciliation pass (title recovery).
- Reduces mis-grouping (subjects are the ground truth for the theme; touched-dir is not).
- Pure additive change to an existing disposable helper (Q-0105); no new deps, stays offline.

## Related

- Complements `trim_recently_shipped.py` (the trim *actuator*) — this improves the *authoring* half.
- The runbook pointer added this pass (`docs/operations/autonomous-routines.md` STEP 2) makes
  `--themes` discoverable; this idea makes its output directly usable.
