# 2026-06-20 — Shared, unit-tested merge-state helper (stop the CI guard regressing a 4th time)

> **Status:** `in-progress`

## Arc

Continuation of the #1187/#1188 CI-race fixes. Both captured a follow-up: this merge-state logic has
been re-broken **3+ times** because it lived as untested inline shell, and each "fix" reached back
for GitHub's async `mergeStateStatus`. The durable fix is to make the logic a **single source of
truth pinned by a test**, so a regression fails CI instead of shipping. Self-initiated promotion of
the captured idea (Q-0172). **CI tooling only — no `disbot/` runtime.**

## Sweep first (the other captured follow-up)

Grepped `.github/workflows/` for every `mergeStateStatus` / `mergeable` consumer: **only the two
already-fixed guards** remain, and every surviving `mergeStateStatus` mention is a comment
explaining why we *don't* use it. The class is confirmed closed — no third instance to fix.

## What this PR adds

- **`scripts/git_merge_state.py`** — stdlib-only, one source of truth for both guards:
  - `conflict <base> <head>` → `CLEAN | DIRTY | UNKNOWN` (`git merge-tree --write-tree`, with an
    object-existence guard so a missing sha can't false-flag).
  - `behind <base> <head>` → `BEHIND | CURRENT | UNKNOWN` (`git merge-base --is-ancestor`).
- **`tests/unit/scripts/test_git_merge_state.py`** — temp-repo tests with real conflict / clean /
  behind / up-to-date / missing-object topologies. This is the regression guard: a future edit that
  reaches back for the async field (or breaks the logic) fails CI.
- **Both workflows now call the helper** instead of duplicating inline git logic — `pr-conflict-guard`
  (`conflict`) and `pr-auto-update` (`behind`). One source of truth; the test guards what they run.

## Verification

- `pytest tests/unit/scripts/test_git_merge_state.py` → 5/5.
- Parity on real SHAs: `conflict e944e25 7ac8655` → DIRTY (the real #1185 conflict); my own branch vs
  moved main → CLEAN + BEHIND (correct — main moved when #1188/#1190 merged).
- Both workflows: YAML parses, `bash -n` clean.
- `check_quality.py --check-only` → all green (helper is under the `scripts/*.py` ruff ignore;
  tests/ is outside CI's black/ruff scope by design).
- `check_quality.py --full` → _(recorded at close)_.

## Shipped

_(filled at close)_
