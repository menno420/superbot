# 2026-06-23 — Fix: check_quality isort scope drifted from CI (false-red on tests/)

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Routine · dispatch, owner-present (maintainer said "fix it"). CLASS: fix. PR #1343 auto-merges on green.

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

## The "verify before fixing" pivot (worth keeping)

The owner said "fix it" about the item I'd flagged at close-out: *"CLAUDE.md is wrong — CI lints
tests/ imports."* But following the binding rule (a tool verdict that fights the evidence is the
tool's bug — verify against ground truth first), I checked the **actual** CI config before touching
the doc. `code-quality.yml` plainly excludes tests/ (`--skip tests`, with its own NOTE about this
exact glob trap). So **CLAUDE.md was right all along** — the bug was the *mirror* diverging from CI,
not the doc. The fix went to the real root (`check_quality.py`) and **CLAUDE.md needs no change**.
Had I "fixed" the doc on my slice-3 hunch, I'd have *introduced* drift into a correct file. This is
the Q-0120 false-green instinct paying off in reverse.

## Verification

- Behavioural proof: planted a deliberately mis-sorted import in `tests/`, ran `check_quality.py
  --check-only` → isort **passed** (tests/ now excluded, matching CI); pre-fix it would have failed.
- `check_quality.py --full` → **11964 passed** (incl. the 5 new parity tests), all formatters green
  (the edited `scripts/check_quality.py` is itself in formatter scope and clean). ·
  `check_architecture --mode strict` → 0 errors.

## Session enders

- **♻ Grooming (Q-0015):** no idea moved (this is an owner-directed bug fix, not an idea promotion);
  the run's grooming happened in slices 1–2 (fishing design §5 + weather Other-idea marked shipped).
- **💡 Session idea (Q-0089):** *Generalise the parity guard to a "mirror-vs-CI" meta-check* — this
  drift (the script keeping a stale form while CI moved on) is the same class as the three-places
  tool-pin drift (#1320). A single `check_ci_mirror.py` that asserts **every** flag `check_quality.py`
  passes to black/isort/ruff/mypy/pytest matches `code-quality.yml`'s would catch the *next* divergence
  (e.g. a new `--exclude` CI adds) before it produces a false signal. Logged, not built (its own slice).
- **⟲ Previous-session review:** slices 1–3 of this run were solid, but slice 3's close-out made a
  **confident wrong call** — it asserted "CLAUDE.md is wrong" from a single observation without
  checking the CI config, and only the owner's "fix it" prompt (plus the verify-first rule) caught it
  before that wrong conclusion propagated into a doc edit. **System lesson:** a flagged
  "the docs are wrong" should carry *"unverified against source"* until checked — the same humility the
  CodeGraph `dead-unresolved` / Q-0120 false-green rules encode. A good candidate note for the
  dispatch close-out checklist (captured, not applied — CLAUDE.md is read-only to an autonomous run).
- **📋 Doc audit (Q-0104):** no doc change needed (CLAUDE.md was correct); the #1343 ledger entry is
  the next recon pass's job (marker #1320, next #1350). No other drift spotted.

## 📤 Run report

- **Run type:** routine · dispatch
- **⚑ Self-initiated:** no — owner-directed in-session ("fix it if you want, I'm here now"). Root-caused
  + fixed the check_quality↔CI isort-scope drift + added a parity guard.
- **⚑ Owner-decisions:** none (the "fix" turned out to be a tool bug, not a doc/policy call).
- **⚑ Owner-manual-steps:** none (dev-tooling + test only; no runtime/deploy effect).
