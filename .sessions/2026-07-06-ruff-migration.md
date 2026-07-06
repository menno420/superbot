# 2026-07-06 — Ruff migration (A3): ruff replaces black + isort

> **Status:** `in-progress` — born-red hold (Q-0133). Flip to `complete` as the deliberate final step.

## What this session is doing

Owner-directed continuation of the CI-setup arc (after #1744 merged). Executes handoff item #3 / design
§C.4 **A3** — the biggest "fewer checks" win: **ruff replaces black + isort** (5 python-gate tools → 3),
removing two-thirds of the formatter pin-drift surface (the #1074/#1315/#1556 drift class). Owner picked
this over the audit-seam guard / gh-permission checker; repo is quiet (no open PRs / claims) so the
whole-tree reformat has no parallel-conflict hazard.

Atomic recipe (design §C.4, all in one PR):
1. Port `[tool.ruff.lint.isort]` into `pyproject.toml` (`known-first-party`, black-profile) + enable `I`.
2. `ruff format` the tree (~95 files) — Black-compatible.
3. Verify magic-trailing-comma parity vs `black 26.5.1`; confirm `I` adds no churn beyond the format.
4. Swap black/isort → ruff in all five: `code-quality.yml`, `requirements-dev.txt`,
   `.pre-commit-config.yaml`, `scripts/check_quality.py`, `scripts/claude_post_edit.py`.
5. Update `scripts/check_tool_pins.py` `_TOOLS`/pins.
6. Full CI mirror (`check_quality.py --full`) proves local == CI before push.

_(Body — shipped, parity result, findings, run report — written as the deliberate final step.)_
