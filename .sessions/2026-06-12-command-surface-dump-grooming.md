# 2026-06-12 — Grooming pass: offline command-surface dump (PR #732)

**PR:** [#732](https://github.com/menno420/superbot/pull/732) — `feat(tooling): offline command-surface dump script`
**Trigger:** grooming pass following PR #731 (untested-surface checklist) merge.
The Q-0089 session idea from that session — "offline command-surface dump script" —
was recorded in `.sessions/2026-06-12-untested-surface-checklist.md` but had no
idea file or idea lifecycle state. This session executes it as the
standing secondary task.

## What shipped

`scripts/command_surface_dump.py` — AST-based read-only dump of every
prefix/slash/group command across all cog files. No live bot or Postgres required.

### Modes

| Command | Output |
|---|---|
| `python3.10 scripts/command_surface_dump.py` | Table grouped by cog: `!name [perm] aliases:…` |
| `--json` | JSON array: name / aliases / kind / perm / cog_file / lineno |
| `--diff-checklist` | Commands in source absent from the untested-surface checklist |
| `--cog economy_cog.py` | Restrict to one cog file |

### First run numbers

- 188 command entries across 37 cog files
- `--diff-checklist`: 120 flagged (expected — the checklist uses hub-level entries +
  an exclusion table for CI-covered surfaces, not explicit per-command rows for everything)

### Tests

`tests/unit/scripts/test_command_surface_dump.py` — 8 tests:
extraction from known cog, alias extraction, kind detection (prefix/slash),
admin perm detection, JSON roundtrip, diff-checklist exit code, empty-cogs error path.

### Docs updated

- `docs/roadmap.md` — session queue item #1 (untested-surface checklist) marked
  ~~executed~~ with PR #731 reference + companion script note
- `docs/ideas/README.md` — Q-0089 idea recorded as executed with result summary
- `docs/current-state.md` — header "Next action" updated to reflect item #1 done,
  PR #730 typo fixed to #731

## Context delta (reflection interview)

1. **Route correct:** the session idea was in the session log; no standalone idea file
   existed; executed directly as the grooming pass (small + safe + tooling lane).
2. **Black/ruff interplay:** ruff added trailing commas → black re-reformatted. Fixed
   by running black a second time after ruff. Stable after two passes.
3. **120 diff-checklist gaps are expected:** the checklist covers hub-level entries
   (`!games` covers games hub) and has an exclusion table for CI-covered surfaces.
   The `--diff-checklist` mode is most useful for future additions — when a new command
   ships but doesn't get a checklist entry in the same PR.
4. **Decisions made alone:** used `!grp` label for `group` kind in table output (keeps
   it visually distinct from `!` prefix commands); used `member` as the default perm
   when no explicit decorator is found (safe conservative choice).

## 💡 Session idea (Q-0089)

**Checklist-diff ratchet in CI.**

Add a CI step that runs `scripts/command_surface_dump.py --diff-checklist` and
**fails if the gap count increases** (not if any gap exists — the current 120 gaps are
known). This would enforce the "add checklist entry in the same PR" maintenance protocol
from `untested-surface-checklist.md` § "How to use this checklist." Trivially implementable:
capture the baseline count in a committed text file (`scripts/.checklist-baseline`) and
fail if `--diff-checklist | wc -l` grows. Zero-cost to maintain; enforces the invariant
automatically. Dedup: not in `docs/ideas/`; adjacent to the `check_docs` orphan guard
pattern (same enforcement philosophy).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (PR #731 — merged via webhook notification at session start) |
| CI-red rounds | 1 (black/ruff ordering issue — fixed in one pass) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (CI ratchet for checklist gap count) |
| Ideas groomed | 1 (command-surface dump script executed) |
