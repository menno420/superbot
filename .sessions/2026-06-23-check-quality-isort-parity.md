# 2026-06-23 — Fix: check_quality isort scope drifted from CI (false-red on tests/)

> **Status:** `in-progress` — born-red card (Q-0133); flips to `complete` as the final step.
> Routine · dispatch, owner-present (maintainer said "fix it"). CLASS: fix. Auto-merges on green.

## Root cause

`scripts/check_quality.py` (the "true CI mirror") runs isort with
`--skip-glob "*/(\.github|tests|venv|env|build|dist)/*"`. isort's `--skip-glob` takes a **glob**,
not a regex — the `(a|b)` alternation matches nothing, so isort silently scans `tests/`. CI itself
hit this exact bug and **fixed it on 2026-06-15** by switching to directory-name `--skip` flags
(`code-quality.yml` L126-131), but `check_quality.py` kept the old broken form — so the two drifted:
CI excludes tests/ from isort, the mirror does not. Result: the mirror throws **false-red isort
failures on test files CI would never flag** (it misled this run's slice-3 into needlessly isort-ing
test files). CLAUDE.md's "CI excludes tests/ from isort" is CORRECT; the mirror was the wrong half.

## Fix

- `check_quality.py`: replace the broken `--skip-glob <regex>` with CI's exact
  `--skip .github --skip tests --skip venv --skip env --skip build --skip dist` form.
- Add `tests/unit/scripts/test_check_quality_ci_parity.py` — parses `code-quality.yml` and asserts
  check_quality's black/isort/ruff exclude scopes cover the same dirs, so this drift class can't recur.
