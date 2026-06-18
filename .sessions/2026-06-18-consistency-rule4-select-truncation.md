# 2026-06-18 — Consistency linter rule 4: select-option truncation

> **Status:** `in-progress`

## What I'm about to do
Add **rule 4 (`select_option_truncation`)** to `scripts/check_consistency.py` — flag a
front-truncating slice `expr[:N]` (N ≤ 25, no lower/step) inside a `views/` file that
builds `discord.SelectOption`s. This is the exact **#1040** silent-drop class: a Discord
select caps at 25 options, so `options[:25]` / `roles[:25]` / `text_channels[:25]`
**silently drop** every entry past the cap instead of paginating. Surfaced by the #1040
bug and the previous session's explicit session-idea ("turn registry-built-select
limit-drift into a CI signal"). Windowed pagination (`x[start:start+N]`, variable bounds)
is correctly NOT flagged. Warn-only + disposable (Q-0105), one rule per PR per the
[consistency-linter plan](../docs/planning/repo-consistency-linter-plan-2026-06-17.md).

Tests in `tests/unit/scripts/test_check_consistency.py` (positive + windowed/string-limit/
non-select/allowlist negatives). Then de-stale the plan + current-state.
